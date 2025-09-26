import uuid
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

from account.models import UserModel



# Create your models here.
class SchoolModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True, blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)  # e.g., {'location': 'Ha Noi'}

    class Meta:
        verbose_name = ('School')
        verbose_name_plural = ('Schools')
        ordering = ['name']

    def __str__(self):
        return self.name
    

class ClassroomModel(models.Model):
    school = models.ForeignKey(SchoolModel, on_delete=models.SET_NULL, null=True, blank=True, related_name='classrooms')
    class_name = models.CharField(max_length=100, unique=True)
    grade = models.CharField(max_length=16, blank=True, null=True)
    teacher = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='classrooms_taught')
    created_by = models.IntegerField()
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, 
                              choices=[("active", "Active"), 
                                       ("archived", "Archived"), 
                                       ("deleted", "Deleted")],
                              default="active")
            
    class Meta:
        indexes = [models.Index(fields=['school'])]
        verbose_name = ('Classroom')
        verbose_name_plural = ('Classrooms')
        ordering = ['name']

    def __str__(self):
        return self.name


class Enrollment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    classroom = models.ForeignKey(ClassroomModel, on_delete=models.CASCADE, related_name='enrollments')
    student = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='enrollments')
    role = models.CharField(max_length=32, default='student')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=32,
        default='active',
        choices=[('active', ('Active')), ('pending', ('Pending')), ('dropped', ('Dropped'))]
    )

    class Meta:
        unique_together = ('classroom', 'student')
        verbose_name = ('Enrollment')
        verbose_name_plural = ('Enrollments')

    def __str__(self):
        return f"{self.student} in {self.classroom}"
    

class MembershipModel(models.Model):
    classroom = models.ForeignKey(ClassroomModel, on_delete=models.CASCADE)
    student = models.ForeignKey(UserModel, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, 
                            choices=[("student", "Student"), 
                                     ("instructor", "Instructor"), 
                                     ("co-instructor", "Co-instructor")])
    joined_on = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ["classroom", "student"]  # Prevent duplicate memberships

    def __str__(self):
        return f"{self.student.username} - {self.classroom.class_name}"
    

class InvitationModel(models.Model):
    classroom = models.ForeignKey(ClassroomModel, on_delete=models.CASCADE, related_name="invitations")
    invite_code = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    email = models.EmailField(unique=True)
    created_by = models.IntegerField()
    created_on = models.DateTimeField(auto_now_add=True)
    expires_on = models.DateTimeField()
    status = models.CharField(max_length=20, 
                              choices=[("pending", "Pending"), 
                                       ("accepted", "Accepted"), 
                                       ("expired", "Expired")],
                              default="pending")
    usgaed_limit = models.IntegerField()
    used_count = models.IntegerField()
    
    class Meta:
        # Allow same email for different classrooms, but not same classroom + email
        unique_together = ["classroom", "email"]  
        indexes = [
            models.Index(fields=["invite_code"]),
            models.Index(fields=["email"]),
        ]
        