from rest_framework import serializers
from account.models import UserModel

"""Serializer for sending user data in responses."""
class UserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=30, required=False)
    last_name = serializers.CharField(max_length=30, required=False)
    phone = serializers.CharField(max_length=15, required=False)
    created_on = serializers.DateTimeField(read_only=True)
    # 🚨 notice: we don’t expose password in API responses

    class Meta:
        model = UserModel
        fields = [
            "id", "username", "email", "first_name", "last_name",
            "phone", "created_on", "role"
        ]

        extra_kwargs = {
            "password": {"write_only": True},
        }


"""Serializer for user registration requests."""
class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=['student', 'instructor', 'admin'], default='student')
    first_name = serializers.CharField(max_length=30, required=False)
    last_name = serializers.CharField(max_length=30, required=False)
    phone = serializers.CharField(max_length=15, required=False)


"""Serializer for login requests."""
class LoginSerializer(serializers.Serializer):
    username_or_email = serializers.CharField()
    password = serializers.CharField(write_only=True)