# from django.contrib import admin
# from .models import Enrollment, LessonProgress

# @admin.register(Enrollment)
# class EnrollmentAdmin(admin.ModelAdmin):
#     list_display = ('user', 'course', 'enrolled_at', 'completed_at')
#     list_filter = ('course',)
#     search_fields = ('user__username', 'user__email', 'course__title')
#     readonly_fields = ('enrolled_at',)

# @admin.register(LessonProgress)
# class LessonProgressAdmin(admin.ModelAdmin):
#     list_display = ('get_user', 'get_course', 'lesson', 'completed_at')
#     list_filter = ('lesson__module__course',)
#     search_fields = ('enrollment__user__username', 'lesson__title')
#     readonly_fields = ('updated_at',)

#     @admin.display(description='User')
#     def get_user(self, obj):
#         return obj.enrollment.user

#     @admin.display(description='Course')
#     def get_course(self, obj):
#         return obj.enrollment.course
