from rest_framework import serializers
from .models import UserModel

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = ['id', 'username', 'email', 'date_joined', 'role', 'phone']
        read_only_fields = ['id', 'date_joined']