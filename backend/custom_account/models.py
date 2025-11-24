import uuid
from django.db import models
from django.db.models.signals import post_save
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.dispatch import receiver
from django.conf import settings



# Create your models here.
class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email must be set')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, email, password, **extra_fields)
    

class UserModel(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    role = models.CharField(max_length=20, 
                            choices=[('student', 'Student'), 
                                     ('instructor', 'Instructor'), 
                                     ('admin', 'Admin')], 
                            default='student')
    phone = models.CharField(max_length=15, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        app_label = 'custom_account'
        indexes = [models.Index(fields=['role'])]
        verbose_name = ('User')
        verbose_name_plural = ('Users')
        ordering = ['email']

    def __str__(self):
        return self.email
    

class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        primary_key=True, 
        related_name='profile'
    )
    
    # --- Basic Info ---
    display_name = models.CharField(max_length=150, blank=True, null=True)
    avatar_url = models.TextField(blank=True, null=True) # Có thể cân nhắc models.ImageField nếu lưu local
    dob = models.DateField(blank=True, null=True)
    gender = models.CharField(
        max_length=16,
        choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')],
        blank=True, null=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'

    def __str__(self):
        return f"{self.display_name or self.user.email}"
    



