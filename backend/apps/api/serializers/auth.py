from rest_framework import serializers
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError as DjangoValidationError

from apps.users.models import User, ClientProfile, AgentProfile
from apps.core.utils.phone import normalize_to_e164


class ClientRegisterSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=32)
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        normalized = normalize_to_e164(attrs['phone'])
        if User.objects.filter(phone=normalized).exists():
            raise serializers.ValidationError({'phone': 'Ce numéro est déjà utilisé'})
        if User.objects.filter(username=attrs['username']).exists():
            raise serializers.ValidationError({'username': 'Ce nom est déjà utilisé'})
        try:
            password_validation.validate_password(attrs['password'])
        except DjangoValidationError as e:
            raise serializers.ValidationError({'password': list(e.messages)})
        attrs['phone'] = normalized
        return attrs
    # Pas de create: la vue gère le flux stateless


class AgentRegisterSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=32)
    password = serializers.CharField(write_only=True, min_length=8)
    username = serializers.CharField(max_length=150, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    agency_name = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def validate(self, attrs):
        normalized = normalize_to_e164(attrs['phone'])
        if User.objects.filter(phone=normalized).exists():
            raise serializers.ValidationError({'phone': 'Ce numéro est déjà utilisé'})
        if attrs.get('email') and User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({'email': 'Cet email est déjà utilisé'})
        if attrs.get('username') and User.objects.filter(username=attrs['username']).exists():
            raise serializers.ValidationError({'username': 'Ce nom est déjà utilisé'})
        try:
            password_validation.validate_password(attrs['password'])
        except DjangoValidationError as e:
            raise serializers.ValidationError({'password': list(e.messages)})
        attrs['phone'] = normalized
        return attrs
    # Pas de create: la vue gère le flux stateless


class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=32)
    password = serializers.CharField(write_only=True)


class OTPRequestSerializer(serializers.Serializer):
    pending_token = serializers.CharField()


class OTPVerifySerializer(serializers.Serializer):
    pending_token = serializers.CharField()
    code = serializers.CharField(max_length=6)
    otp_id = serializers.CharField(max_length=128, required=False, allow_blank=True)


class PasswordResetRequestSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=32)


class PasswordResetVerifySerializer(serializers.Serializer):
    reset_token = serializers.CharField()
    code = serializers.CharField(max_length=6)


class PasswordResetFinalizeSerializer(serializers.Serializer):
    reset_session_token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_new_password(self, value: str) -> str:
        try:
            password_validation.validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value


class MeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'phone', 'username', 'email', 'role']

