import uuid
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

from account.models import UserModel



# Create your models here.
class ClassroomModel(models.Model):
    class_name = models.CharField(max_length=100, unique=True)
    created_by = models.IntegerField()
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, 
                              choices=[("active", "Active"), 
                                       ("archived", "Archived"), 
                                       ("deleted", "Deleted")],
                              default="active")
            
    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(status__in=["active", "archived", "deleted"]),
                name="valid_classroom_status"
            )
        ]


class MembershipModel(models.Model):
    classroom = models.ForeignKey(ClassroomModel, on_delete=models.CASCADE)
    student = models.ForiegnKey(UserModel, on_delete=models.CASCADE)
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

    def __str__(self):
        return f"Invitation for {self.email} to {self.classroom.class_name}"
    
    def is_expired(self):
        return timezone.now() > self.expires_on
    
    def save(self, *args, **kwargs):
        # Auto-set status to expired if past expiry date
        if self.is_expired() and self.status != "accepted":
            self.status = "expired"
        super().save(*args, **kwargs)