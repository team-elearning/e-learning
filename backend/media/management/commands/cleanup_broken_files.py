from django.core.management.base import BaseCommand
from media.services import file_service # 



class Command(BaseCommand):
    help = 'Quét CSDL và xóa các bản ghi UploadedFile không còn file vật lý tương ứng.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING(
            'Bắt đầu quét các file hỏng (tác vụ này có thể mất nhiều thời gian)...'
        ))
        
        try:
            result = file_service.cleanup_broken_links()
            count = result.get('deleted_count', 0)
            
            if count == 0:
                self.stdout.write(self.style.SUCCESS('Không tìm thấy file hỏng nào.'))
            else:
                self.stdout.write(self.style.SUCCESS(f"Đã xóa thành công {count} bản ghi file hỏng."))
                for filename in result.get('filenames', []):
                    self.stdout.write(f" - {filename}")
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Đã xảy ra lỗi nghiêm trọng: {e}"))