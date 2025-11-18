from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import AuthenticationFailed
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from dj_rest_auth.serializers import LoginSerializer
from allauth.account.models import EmailAddress

from custom_account.models import UserModel, Profile
from custom_account.domains.user_domain import UserDomain
from custom_account.domains.profile_domain import ProfileDomain
# from custom_account.domains.parental_consent_domain import ParentalConsentDomain
from custom_account.domains.change_password_domain import ChangePasswordDomain
from custom_account.domains.reset_password_domain import ResetPasswordDomain
from custom_account.services import auth_service, profile_service

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
            "id", "username", "email", "is_active",
            "phone", "created_on", "role"
        ]
        read_only_fields = ["id", "created_on"]

    def get_fields(self):
        """Dynamically make some fields read-only depending on the user."""
        fields = super().get_fields()

        request = self.context.get("request", None)
        if request and not request.user.is_staff:  # Non-admin user
            # Make restricted fields read-only
            fields["role"].read_only = True
            fields["is_active"].read_only = True

        return fields
    
    def to_domain(self) -> UserDomain:
        """Convert serializer data -> UserDomain."""
        return UserDomain.from_dict(self.validated_data)

    @staticmethod
    def from_domain(domain: UserDomain) -> dict:
        """Convert UserDomain -> dict (API response)."""
        return domain.to_dict()
    
    def to_representation(self, instance):
        # Nếu instance là UserDomain, convert sang dict
        if isinstance(instance, UserDomain):
            return {
                'id': instance.id,
                'username': instance.username,
                'email': instance.email,
                'role': instance.role,
                'created_on': instance.created_on,
                'phone': instance.phone,
            }
        return super().to_representation(instance)


class ProfileSerializer(serializers.ModelSerializer):
    """Serializer for Profile <-> ProfileDomain mapping."""

    class Meta:
        model = Profile
        fields = [
            "user_id", "display_name", "avatar_url",
            "dob", "gender", "language", "metadata"
        ]
        read_only_fields = ["user_id"]

    def to_domain(self) -> ProfileDomain:
        """Convert serializer data to domain object."""
        data = dict(self.validated_data)

        # inject user_id from context or instance
        if self.instance:
            data["user_id"] = self.instance.user_id
        else:
            # trường hợp create profile
            user = self.context.get("user")
            if not user:
                raise ValueError("Missing user in serializer context")
            data["user_id"] = user.id

        domain = ProfileDomain.from_dict(data)
        domain.validate()
        return domain

    @staticmethod
    def from_domain(domain: ProfileDomain) -> dict:
        return domain.to_dict()


# class ParentalConsentSerializer(serializers.ModelSerializer):
#     """Serializer for ParentalConsent <-> ParentalConsentDomain mapping."""

#     class Meta:
#         model = ParentalConsent
#         fields = [
#             "id", "parent", "child", "consented_at",
#             "scopes", "revoked_at", "metadata"
#         ]
#         read_only_fields = ["id", "consented_at"]

#     def to_domain(self) -> ParentalConsentDomain:
#         return ParentalConsentDomain.from_dict(self.validated_data)

#     @staticmethod
#     def from_domain(domain: ParentalConsentDomain) -> dict:
#         return domain.to_dict()



"""Serializer for user registration requests (input only)."""
class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=["student", "instructor", "admin"], default="student")
    phone = serializers.CharField(max_length=15, required=False)

    def to_domain(self):
        """Convert validated data into a UserDomain object"""
        return UserDomain(**self.validated_data)
    

class CustomLoginSerializer(LoginSerializer):
    def validate(self, attrs):
        username = attrs.get('username')
        email = attrs.get('email')
        password = attrs.get('password')
        
        user = None

        # 1. Tìm user dựa trên username hoặc email gửi lên
        if username:
            user = UserModel.objects.filter(username=username).first()
        elif email:
            user = UserModel.objects.filter(email=email).first()

        # 2. Kiểm tra logic thủ công để báo lỗi chi tiết
        if not user:
            # Lỗi A: User không tồn tại
            raise serializers.ValidationError(
                {"detail": "Tài khoản không tồn tại trong hệ thống."}
            )

        if not user.check_password(password):
            # Lỗi B: Sai mật khẩu
            raise serializers.ValidationError(
                {"detail": "Mật khẩu không chính xác."}
            )

        if not user.is_active:
            # Lỗi C: Tài khoản bị khóa (is_active=False)
            raise serializers.ValidationError(
                {"detail": "Tài khoản này đã bị vô hiệu hóa."}
            )

        # 3. Kiểm tra Email Verification (Optional - cho trường hợp bạn gặp lúc nãy)
        # Nếu bạn dùng allauth và bắt buộc verify email
        if email: 
             email_record = EmailAddress.objects.filter(user=user, email=email).first()
             if email_record and not email_record.verified:
                  raise serializers.ValidationError(
                    {"detail": "Email chưa được xác thực. Vui lòng kiểm tra hộp thư."}
                )

        # 4. Nếu qua hết các bước trên, để dj-rest-auth chạy logic gốc (tạo token, v.v.)
        # Chúng ta dùng try/catch vì authenticate() của Django có thể fail vì lý do khác
        try:
            return super().validate(attrs)
        except serializers.ValidationError as e:
            # Nếu logic gốc vẫn báo lỗi (ví dụ lỗi hệ thống khác), ta trả về lỗi đó
            # Hoặc custom lại thông báo nếu muốn
            raise serializers.ValidationError(
                {"detail": "Đăng nhập thất bại. (Lỗi xác thực hệ thống)"}
            )
    

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def to_domain(self, user_id: int) -> ChangePasswordDomain:
        return ChangePasswordDomain(
            user_id=user_id,
            old_password=self.validated_data["old_password"],
            new_password=self.validated_data["new_password"]
        )
    

class SetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True, required=True)
    

class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    reset_token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)

    def to_domain(self) -> ResetPasswordDomain:
        return ResetPasswordDomain.from_dict(self.validated_data)

    
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'username_or_email'
    username_or_email = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username_or_email = attrs.get("username_or_email")
        password = attrs.get("password")

        # Authenticate using custom service
        try:
            user = auth_service.authenticate_user(username_or_email, password)
        except ValidationError as e:
            # Raise AuthenticationFailed for invalid credentials to return 401
            raise AuthenticationFailed("No active account found with the given credentials", code="authentication")

        # Set user to bypass parent authentication
        self.user = user

        # Get profile
        try:
            profile = profile_service.get_profile_by_user(user.id)
        except ObjectDoesNotExist:
            profile = profile_service.create_default_profile(user.id)

        # Generate tokens manually
        refresh = RefreshToken.for_user(user)
        data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'username': user.username,
                'email': user.email,
                'role': "admin" if user.is_staff else user.role,
                'full_name': profile.display_name if profile.display_name else user.username,
            }
        }
        return data
    

class UserPublicOutputSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = UserModel
        fields = ['username', 'email', 'role', 'full_name']

    def get_role(self, user_obj):
        if user_obj.is_staff:
            return "admin"
        
        if hasattr(user_obj, 'role'):
            return user_obj.role
        return "student" 

    def get_full_name(self, user_obj):
        try:
            profile = user_obj.profile 
            if profile.display_name:
                return profile.display_name
            return user_obj.username
        except Exception:
            return user_obj.username