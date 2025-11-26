from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone

from media.models import UploadedFile, FileStatus



class Command(BaseCommand):
    help = 'Xóa các file staging quá hạn (File rác)'

    def handle(self, *args, **options):
        # 1. Định nghĩa thời gian hết hạn (ví dụ: file staging để quá 24h là rác)
        cutoff_time = timezone.now() - timedelta(hours=24)

        # 2. Tìm các file rác
        junk_files = UploadedFile.objects.filter(
            status=FileStatus.STAGING, 
            uploaded_at__lt=cutoff_time
        )

        count = junk_files.count()
        if count == 0:
            self.stdout.write("Không có file rác nào để xóa.")
            return

        self.stdout.write(f"Tìm thấy {count} file rác. Đang tiến hành xóa...")

        # 3. Xóa từng file
        for file_obj in junk_files:
            try:
                # Xóa file vật lý trên AWS S3 trước
                # Lưu ý: delete(save=False) để ko trigger save model lần nữa
                file_obj.file.delete(save=False) 
                
                # Sau đó xóa record trong Database
                file_obj.delete()
                
                self.stdout.write(f"- Đã xóa: {file_obj.id} ({file_obj.original_filename})")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"- Lỗi khi xóa {file_obj.id}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"Đã dọn dẹp xong {count} file."))