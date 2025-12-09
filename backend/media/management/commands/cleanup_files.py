import boto3
import re
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from media.models import UploadedFile, FileStatus 
from content.models import Course, Module, Lesson, ContentBlock
from content.services.content_block_service import _extract_file_ids_from_html



class Command(BaseCommand):
    help = 'Công cụ dọn dẹp hệ thống File (Staging & Broken Links)'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=1, help='Tuổi thọ file staging (ngày)')
        parser.add_argument('--dry-run', action='store_true', help='Chỉ in ra chứ không xóa thật')

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        days = options['days']

        if self.dry_run:
            self.stdout.write(self.style.WARNING("--- DRY RUN MODE: KHÔNG CÓ FILE NÀO BỊ XÓA ---"))

        self.stdout.write(self.style.WARNING(f"--- BẮT ĐẦU DỌN DẸP (Cấu hình: >{days} ngày) ---"))

        # --- TASK 1: XÓA FILE STAGING (Bulk Delete - Nhanh) ---
        self.cleanup_staging_files(days)

        # # Nếu không làm bước này, bước check S3 phía sau sẽ thấy DB vẫn còn record nên không xóa file.
        # self.cleanup_zombie_rows()

        # # 3. Dọn Rác Payload (Nặng, chạy cuối tuần)
        # # Có thể check datetime.today().weekday() == 6 để chạy chủ nhật
        # self.cleanup_payload_orphans()

        # # GỘP TASK 2 & 3: QUÉT 1 LẦN RA CẢ 2 LOẠI RÁC
        # # Thay vì quét 2 lần (1 lần check broken, 1 lần check orphan)
        # # Ta quét S3 một lần, lấy danh sách đó so với DB -> Ra kết quả luôn.
        # self.cleanup_consistency_check()

        # 2. DỌN ORPHAN (So khớp S3 vs DB)
        # Chỉ chạy bước này khi hệ thống thấp tải (ví dụ ban đêm)
        self.cleanup_orphans()


    # def cleanup_zombie_rows(self):
    #     """
    #     Bước 0: Tìm và xóa các dòng UploadedFile trong DB mà đối tượng cha đã bị xóa.
    #     """
    #     self.stdout.write("0. Đang quét Zombie Records (DB trỏ vào hư vô)...")
        
    #     # Danh sách các Model mà UploadedFile có thể bám vào.
    #     # Bạn cần thêm ContentBlock vào đây nếu ContentBlock cũng có thể chứa file upload.
    #     models_to_check = [Course, Module, Lesson, ContentBlock] 

    #     total_zombies = 0

    #     for model_class in models_to_check:
    #         # --- SỬA LẠI ĐOẠN NÀY ---
    #         # Dùng ContentType của Django để lấy ID đại diện cho Model
    #         ct = ContentType.objects.get_for_model(model_class)
            
    #         # Lấy tất cả ID hiện có của Model thật (Ví dụ: Lấy list ID của tất cả Course đang tồn tại)
    #         existing_ids = model_class.objects.values_list('id', flat=True)

    #         # Tìm các UploadedFile thuộc loại Model này (ví dụ Course) 
    #         # NHƯNG object_id lại KHÔNG nằm trong danh sách ID Course thật
    #         zombies = UploadedFile.objects.filter(
    #             content_type=ct
    #         ).exclude(
    #             object_id__in=existing_ids
    #         )
            
    #         count = zombies.count()
    #         if count > 0:
    #             self.stdout.write(f"   - Phát hiện {count} dòng mồ côi thuộc về {model_class.__name__}. Đang xóa...")
    #             zombies.delete() 
    #             total_zombies += count

    #     if total_zombies == 0:
    #         self.stdout.write(self.style.SUCCESS("   ✓ DB sạch sẽ, không có record rác (Zombie)."))
    #     else:
    #         self.stdout.write(self.style.SUCCESS(f"   ✓ Đã dọn dẹp tổng cộng {total_zombies} zombie records."))


    def _list_all_s3_objects(self):
        """Helper: Liệt kê toàn bộ file trên bucket"""
        s3 = boto3.client('s3', 
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID, 
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            endpoint_url=getattr(settings, 'AWS_S3_ENDPOINT_URL', None)
        )
        paginator = s3.get_paginator('list_objects_v2')
        keys = set()
        for page in paginator.paginate(Bucket=settings.AWS_STORAGE_BUCKET_NAME):
            if 'Contents' in page:
                for obj in page['Contents']:
                    keys.add(obj['Key'])
        return keys

    def _delete_s3_batch(self, keys):
        """Helper: Xóa batch 1000 file"""
        s3 = boto3.client('s3', 
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID, 
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            endpoint_url=getattr(settings, 'AWS_S3_ENDPOINT_URL', None)
        )
        batch_size = 1000
        for i in range(0, len(keys), batch_size):
            batch = keys[i:i+batch_size]
            objects = [{'Key': k} for k in batch]
            try:
                s3.delete_objects(
                    Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                    Delete={'Objects': objects, 'Quiet': True}
                )
                self.stdout.write(f" - Deleted batch {len(batch)} files.")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error deleting batch: {e}"))


    def cleanup_staging_files(self, days):
        """Logic xóa hàng loạt file Staging"""
        self.stdout.write("\n1. --- CLEANUP STAGING ---")
        cutoff_time = timezone.now() - timedelta(days=days)
        
        junk_files_qs = UploadedFile.objects.filter(
            status=FileStatus.STAGING, 
            uploaded_at__lt=cutoff_time
        ).exclude(file='')

        count = junk_files_qs.count()
        self.stdout.write(f"Tìm thấy {count} file staging hết hạn.")

        if count > 0 and not self.dry_run:
            # Xóa file trên S3 (Logic xóa batch)
            paths = list(junk_files_qs.values_list('file', flat=True))
            self._delete_s3_batch(paths)
            
            # Xóa record trong DB
            junk_files_qs.delete()
            self.stdout.write(self.style.SUCCESS("Đã dọn dẹp Staging xong."))

        # if count == 0:
        #     self.stdout.write(self.style.SUCCESS("✓ Staging: Sạch sẽ."))
        #     return

        # self.stdout.write(f"Staging: Tìm thấy {count} file. Đang xóa...")
        
        # # 2. Gom danh sách Key để xóa trên S3 (Batch processing)
        # # S3 giới hạn xóa tối đa 1000 file/request, nên ta chia batch nếu quá nhiều
        # BATCH_SIZE = 1000
        # all_junk_files = list(junk_files_qs.values_list('file', flat=True)) # Lấy list string path
        
        # s3_client = boto3.client(
        #     's3',
        #     aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        #     aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        #     region_name=settings.AWS_S3_REGION_NAME,
        # )

        # # Xử lý từng cụm 1000 file
        # for i in range(0, len(all_junk_files), BATCH_SIZE):
        #     batch_keys = all_junk_files[i:i + BATCH_SIZE]
            
        #     # Format đúng chuẩn boto3 yêu cầu: [{'Key': 'path1'}, {'Key': 'path2'}...]
        #     objects_to_delete = [{'Key': key} for key in batch_keys]
            
        #     try:
        #         # Gửi 1 lệnh xóa duy nhất cho cả cụm
        #         response = s3_client.delete_objects(
        #             Bucket=settings.AWS_STORAGE_BUCKET_NAME,
        #             Delete={
        #                 'Objects': objects_to_delete,
        #                 'Quiet': True
        #             }
        #         )
        #         self.stdout.write(f"- Đã gửi lệnh xóa {len(batch_keys)} file trên S3.")
                
        #     except Exception as e:
        #         self.stdout.write(self.style.ERROR(f"Lỗi khi xóa batch S3: {e}"))
        
        # # Giả lập xóa DB
        # deleted_count, _ = junk_files_qs.delete()
        # self.stdout.write(self.style.SUCCESS(f"✓ Staging: Đã xóa {deleted_count} file."))


    def cleanup_orphans(self):
        """
        Logic so khớp "Nuclear": Lấy tất cả path trong DB so với S3.
        """
        self.stdout.write("\n2. --- CLEANUP ORPHANS (PRODUCTION) ---")
        
        # BƯỚC A: Lấy danh sách "WhiteList" (File đang dùng trong DB)
        valid_paths = set()

        # 1. Quét Course Thumbnail (Public)
        self.stdout.write("Scanning Course Thumbnails...")
        courses = Course.objects.exclude(thumbnail='').values_list('thumbnail', flat=True)
        for path in courses:
            # Lưu ý: DB lưu "course_thumbnails/abc.jpg"
            # Nhưng trên S3 nó nằm ở "public/course_thumbnails/abc.jpg"
            # Cần normalize path cho khớp với cấu trúc S3
            valid_paths.add(f"public/{path}")

        # 2. Quét ContentBlock (Private & Public)
        self.stdout.write("Scanning ContentBlocks...")
        blocks = ContentBlock.objects.exclude(payload={}).values_list('type', 'payload')
        
        for b_type, payload in blocks:
            if not payload: continue
            
            # 2.1 Video/PDF/File (Private)
            if 'file_path' in payload:
                # DB lưu: "courses/123/video.mp4" -> S3: "private/courses/123/video.mp4"
                valid_paths.add(f"private/{payload['file_path']}")
            
            # 2.2 Rich Text Images (Public)
            if b_type == 'rich_text':
                html = payload.get('html_content', '')
                # Dùng Regex quét src="..." để tìm path
                # Pattern này tìm các link chứa domain S3 của bạn
                # Ví dụ: https://my-bucket.s3.amazonaws.com/public/attachments/xyz.jpg
                # Ta cần trích xuất phần path: "public/attachments/xyz.jpg"
                
                # Regex đơn giản hóa (cần tùy chỉnh theo domain thật của bạn)
                # Giả sử domain là settings.AWS_S3_CUSTOM_DOMAIN
                domain = settings.AWS_S3_CUSTOM_DOMAIN.replace('.', r'\.')
                pattern = rf'https?://{domain}/([^"\']+)'
                
                matches = re.findall(pattern, html)
                for match in matches:
                    valid_paths.add(match)

        self.stdout.write(f"-> Tổng số file hợp lệ trong DB: {len(valid_paths)}")

        # BƯỚC B: Lấy danh sách thực tế trên S3
        self.stdout.write("Listing S3 Objects...")
        s3_files = self._list_all_s3_objects()
        self.stdout.write(f"-> Tổng số file trên S3: {len(s3_files)}")

        # BƯỚC C: Tìm file rác (S3 có - DB không có)
        # Chỉ quét trong folder 'public/' và 'private/' để tránh xóa nhầm folder khác
        target_s3_files = {k for k in s3_files if k.startswith(('public/', 'private/'))}
        
        orphans = target_s3_files - valid_paths
        
        self.stdout.write(self.style.WARNING(f"-> PHÁT HIỆN {len(orphans)} FILE RÁC (ORPHANS)."))

        # BƯỚC D: Xóa
        if orphans:
            if self.dry_run:
                self.stdout.write("Dry run: Danh sách file sẽ bị xóa:")
                for o in list(orphans)[:10]: # In mẫu 10 cái
                    print(f" - {o}")
            else:
                self.stdout.write("Đang tiến hành xóa...")
                self._delete_s3_batch(list(orphans))
                self.stdout.write(self.style.SUCCESS("Đã dọn dẹp Orphans xong."))


    # def cleanup_payload_orphans(self):
    #     """
    #     Bước "Deep Scan": Quét sâu vào payload JSON để tìm file bị bỏ rơi.
    #     Ví dụ: User sửa bài rich text, xóa ảnh đi, nhưng ảnh vẫn link với block trong DB.
    #     """
    #     self.stdout.write("--- BẮT ĐẦU QUÉT RÁC TRONG PAYLOAD (DEEP SCAN) ---")
        
    #     # Lấy tất cả block có file đính kèm để đỡ phải quét block rỗng
    #     # (Tối ưu performance)
    #     blocks_with_files = ContentBlock.objects.prefetch_related('files').all()
        
    #     total_deleted = 0
        
    #     # Map logic giống hệt trong Service
    #     single_file_map = {
    #         'video': 'video_id', 'pdf': 'file_id', 
    #         'docx': 'file_id', 'audio': 'audio_id', 'file': 'file_id'
    #     }

    #     for block in blocks_with_files:
    #         # 1. Xác định những file ĐANG ĐƯỢC SỬ DỤNG (Active)
    #         active_file_ids = set()
    #         payload = block.payload or {}
            
    #         if block.type == 'rich_text':
    #             html = payload.get('html_content', '')
    #             # Hàm extract bạn đã có ở service, import vào đây dùng
    #             active_file_ids.update(_extract_file_ids_from_html(html))
                
    #         elif block.type in single_file_map:
    #             key = single_file_map[block.type]
    #             fid = payload.get(key)
    #             if fid:
    #                 active_file_ids.add(str(fid)) # Đảm bảo là string để so sánh
            
    #         # 2. Xác định những file ĐANG LIÊN KẾT TRONG DB
    #         # (Những file mà bảng UploadedFile đang trỏ vào block này)
    #         db_files = block.files.all() # Nhờ prefetch_related nên ko tốn query
            
    #         for db_file in db_files:
    #             db_file_id = str(db_file.id)
                
    #             # 3. SO SÁNH: Nếu DB có, mà Payload không dùng -> RÁC
    #             if db_file_id not in active_file_ids:
    #                 self.stdout.write(f" - Block {block.id}: Xóa file thừa {db_file_id} ({db_file.file.name})")
    #                 db_file.delete() # Trigger xóa S3 luôn
    #                 total_deleted += 1

    #     if total_deleted > 0:
    #         self.stdout.write(self.style.SUCCESS(f"✓ Đã dọn dẹp {total_deleted} file thừa do chỉnh sửa payload."))
    #     else:
    #         self.stdout.write(self.style.SUCCESS("✓ Payload sạch sẽ."))


    # def cleanup_consistency_check(self):
    #     self.stdout.write("--- BẮT ĐẦU ĐỒNG BỘ DỮ LIỆU S3 & DB ---")
        
    #     s3 = boto3.client('s3', ...)
    #     paginator = s3.get_paginator('list_objects_v2')
    #     bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        
    #     # 1. Tải TOÀN BỘ danh sách file trên S3 vào RAM (Set)
    #     # Lưu ý: Nếu > 100k file, nên dùng AWS Inventory (Cách 2 ở trên)
    #     self.stdout.write("1. Đang tải danh sách file từ S3 (Batch List)...")
    #     s3_keys = set()
        
    #     page_iterator = paginator.paginate(Bucket=bucket_name, Prefix='media/')
    #     for page in page_iterator:
    #         if 'Contents' in page:
    #             for obj in page['Contents']:
    #                 s3_keys.add(obj['Key'])
        
    #     self.stdout.write(f"-> Tìm thấy {len(s3_keys)} file trên S3.")

    #     # 2. Tải TOÀN BỘ danh sách file trong DB vào RAM (Set)
    #     self.stdout.write("2. Đang tải danh sách file từ DB...")
    #     # values_list trả về list string path
    #     db_files = set(UploadedFile.objects.exclude(file='').values_list('file', flat=True))
    #     self.stdout.write(f"-> Tìm thấy {len(db_files)} file trong DB.")

    #     # 3. TÌM FILE HỎNG (Có trong DB - Mất trên S3)
    #     # Logic tập hợp: DB - S3 = Những cái có ở DB mà ko có ở S3
    #     broken_links = db_files - s3_keys
        
    #     if broken_links:
    #         self.stdout.write(self.style.ERROR(f"3. Phát hiện {len(broken_links)} broken links (DB có, S3 mất). Đang fix DB..."))
    #         # Xóa batch DB
    #         UploadedFile.objects.filter(file__in=broken_links).delete()
    #     else:
    #         self.stdout.write(self.style.SUCCESS("3. Không có broken links."))

    #     # 4. TÌM FILE RÁC S3 (Có trên S3 - Mất trong DB)
    #     # Logic tập hợp: S3 - DB = Những cái thừa trên S3
    #     orphans = s3_keys - db_files
        
    #     if orphans:
    #         self.stdout.write(self.style.WARNING(f"4. Phát hiện {len(orphans)} file rác trên S3. Đang xóa..."))
            
    #         # Convert Set về List để chia batch xóa
    #         orphan_list = list(orphans)
    #         batch_size = 1000
            
    #         for i in range(0, len(orphan_list), batch_size):
    #             batch = orphan_list[i:i+batch_size]
    #             objects = [{'Key': k} for k in batch]
                
    #             # Gọi API xóa Batch của AWS (1 request xóa 1000 file)
    #             s3.delete_objects(
    #                 Bucket=bucket_name,
    #                 Delete={'Objects': objects, 'Quiet': True}
    #             )
    #             self.stdout.write(f"   - Đã xóa batch {len(batch)} file.")
    #     else:
    #          self.stdout.write(self.style.SUCCESS("4. Không có file rác trên S3."))

    #     self.stdout.write(self.style.SUCCESS("--- HOÀN TẤT ĐỒNG BỘ ---"))