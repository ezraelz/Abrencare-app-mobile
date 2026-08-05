from rest_framework import serializers
from .models import User
from roles.models import Role
from roles.serializers import RoleSerializer
from django.contrib.auth.password_validation import validate_password
from .models import User
from roles.models import Role
import re
try:
    from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
except Exception:
    # Fallback minimal base class if simplejwt is not available or unresolved by the analyzer.
    # Uses RefreshToken.for_user so CustomTokenObtainPairSerializer.super().get_token will work.
    from rest_framework_simplejwt.tokens import RefreshToken

    class TokenObtainPairSerializer:
        @classmethod
        def get_token(cls, user):
            return RefreshToken.for_user(user)


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    status = serializers.ReadOnlyField()
    profile_picture_url = serializers.ReadOnlyField()
    role = RoleSerializer(read_only=True)

    personal_information = serializers.ReadOnlyField()
    medical_information = serializers.ReadOnlyField()
    emergency_contact = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",

            # Profile
            "full_name",
            "status",
            "role",
            "profile_picture_url",

            # Structured sections
            "personal_information",
            "medical_information",
            "emergency_contact",

            # Raw fields (optional but useful)
            "first_name",
            "last_name",
            "phone_number",
            "date_of_birth",
            "date_joined",
        ]
        read_only_fields = ["id"]

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "password",
        ]

    def create(self, validated_data):
        password = validated_data.pop("password")
        role, _= Role.objects.filter(role_name="patient").first()

        user = User(**validated_data, role=role)
        user.set_password(password)
        user.save()

        return user

class UserUpdateSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "profile_picture",
            "username",
            "email",
            "role",
            "date_of_birth",
            "phone_number",
            "address",
            "postal_code",
            "city",
        ]

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['username'] = user.username
        token['email'] = user.email
        token['is_superuser'] = user.is_superuser

        return token


class EnhancedChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(
        required=True, 
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True, 
        write_only=True,
        min_length=8,
        style={'input_type': 'password'},
        help_text="Password must be at least 8 characters long and contain uppercase, lowercase, number and special character"
    )
    confirm_password = serializers.CharField(
        required=True, 
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate_new_password(self, value):
        # Use Django's built-in password validation
        validate_password(value)
        
        # Additional custom validation
        if not any(char.isupper() for char in value):
            raise serializers.ValidationError("Password must contain at least one uppercase letter.")
        
        if not any(char.islower() for char in value):
            raise serializers.ValidationError("Password must contain at least one lowercase letter.")
        
        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError("Password must contain at least one number.")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            raise serializers.ValidationError("Password must contain at least one special character.")
        
        # Check for common patterns
        common_patterns = ['123456', 'password', 'qwerty', 'abc123']
        if value.lower() in common_patterns:
            raise serializers.ValidationError("Password is too common. Please choose a stronger password.")
        
        return value
    
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': 'New passwords do not match.'
            })
        
        user = self.context['request'].user
        
        # Check if new password is different from current password
        if user.check_password(data['new_password']):
            raise serializers.ValidationError({
                'new_password': 'New password must be different from current password.'
            })
        
        return data