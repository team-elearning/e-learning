from rest_framework import serializers
from .models import AppUser

class AppUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppUser
        fields = ['id', 'username', 'email', 'date_joined', 'role', 'phone']
        read_only_fields = ['id', 'date_joined']