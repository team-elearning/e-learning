from rest_framework import serializers

from account.models import UserModel, Profile, ParentalConsent
from account.domains.user_domain import UserDomain
from account.domains.profile_domain import ProfileDomain
from account.domains.login_domain import LoginDomain
from account.domains.parental_consent_domain import ParentalConsentDomain
from account.domains.change_password_domain import ChangePasswordDomain
from account.domains.reset_password_domain import ResetPasswordDomain

"""Serializer for sending user data in responses."""
class UserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=15, required=False)
    created_on = serializers.DateTimeField(read_only=True)
    # 🚨 notice: we don’t expose password in API responses

    class Meta:
        model = UserModel
        fields = [
            "id", "username", "email", "is_active"
            "phone", "created_on", "role"
        ]
        read_only_fields = ["id", "created_on"]
    
    def to_domain(self) -> UserDomain:
        """Convert serializer data -> UserDomain."""
        return UserDomain.from_dict(self.validated_data)

    @staticmethod
    def from_domain(domain: UserDomain) -> dict:
        """Convert UserDomain -> dict (API response)."""
        return domain.to_dict()


class ProfileSerializer(serializers.ModelSerializer):
    """Serializer for Profile <-> ProfileDomain mapping."""

    class Meta:
        model = Profile
        fields = [
            "user", "display_name", "avatar_url",
            "dob", "gender", "language", "metadata"
        ]
        read_only_fields = ["user"]

    def to_domain(self) -> ProfileDomain:
        return ProfileDomain.from_dict(self.validated_data)

    @staticmethod
    def from_domain(domain: ProfileDomain) -> dict:
        return domain.to_dict()


class ParentalConsentSerializer(serializers.ModelSerializer):
    """Serializer for ParentalConsent <-> ParentalConsentDomain mapping."""

    class Meta:
        model = ParentalConsent
        fields = [
            "id", "parent", "child", "consented_at",
            "scopes", "revoked_at", "metadata"
        ]
        read_only_fields = ["id", "consented_at"]

    def to_domain(self) -> ParentalConsentDomain:
        return ParentalConsentDomain.from_dict(self.validated_data)

    @staticmethod
    def from_domain(domain: ParentalConsentDomain) -> dict:
        return domain.to_dict()



"""Serializer for user registration requests (input only)."""
class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=["student", "instructor", "admin"], default="student")
    first_name = serializers.CharField(max_length=30, required=False)
    last_name = serializers.CharField(max_length=30, required=False)
    phone = serializers.CharField(max_length=15, required=False)

    def to_domain(self):
        """Convert validated data into a UserDomain object"""
        return UserDomain(**self.validated_data)
    

"""Serializer for login requests (input only)."""
class LoginSerializer(serializers.Serializer):
    username_or_email = serializers.CharField()
    raw_password = serializers.CharField(write_only=True)

    def to_domain(self) -> "LoginDomain":
        """Convert validated data into a LoginDomain object"""
        return LoginDomain(username_or_email=self.validated_data["username_or_email"],
                           raw_password=self.validated_data["raw_password"],)
    
    
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def to_domain(self, user_id: int) -> ChangePasswordDomain:
        return ChangePasswordDomain(
            user_id=user_id,
            old_password=self.validated_data["old_password"],
            new_password=self.validated_data["new_password"]
        )
    

class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    reset_token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)

    def to_domain(self) -> ResetPasswordDomain:
        return ResetPasswordDomain.from_dict(self.validated_data)
