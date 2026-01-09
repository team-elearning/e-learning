from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import UserModel # Hoặc tên model User của bạn

@admin.register(UserModel)
class CustomUserAdmin(UserAdmin):
    # 1. Hiển thị danh sách (Thêm role và phone để dễ quản lý)
    list_display = ('username', 'email', 'role', 'phone', 'is_active', 'is_staff', 'created_on')
    
    # 2. Bộ lọc bên phải
    list_filter = ('role', 'is_active', 'is_staff')
    
    # 3. Tìm kiếm theo email, username, sđt
    search_fields = ('username', 'email', 'phone')
    
    # 4. Sắp xếp mặc định
    ordering = ('-created_on',)

    # 5. Các trường chỉ đọc (Vì created_on và updated_on là auto_now nên không sửa được)
    readonly_fields = ('created_on', 'updated_on')

    # 6. Form chỉnh sửa chi tiết (Quan trọng: Phải khớp với model)
    fieldsets = (
        ('Tài khoản', {'fields': ('username', 'email', 'password')}),
        ('Thông tin cá nhân', {'fields': ('phone', 'role')}),
        ('Quyền hạn', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Thời gian', {'fields': ('created_on', 'updated_on')}),
    )
    
    # 7. Form khi tạo user mới
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password', 'role', 'is_active', 'is_staff'),
        }),
    )
