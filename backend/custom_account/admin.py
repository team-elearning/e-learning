from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import UserModel # Hoặc tên model User của bạn

# Đăng ký model vào Admin
admin.site.register(UserModel, UserAdmin)
