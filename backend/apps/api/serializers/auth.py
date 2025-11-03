from dataclasses import dataclass
import random
from typing import Any

from django.db import transaction
from rest_framework import serializers

from apps.users.models import User, ClientProfile, AgentProfile


class ClientRegisterSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=32)
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=6)

    def validate(self, attrs):
        if User.objects.filter(phone=attrs['phone']).exists():
            raise serializers.ValidationError({'phone': 'Ce numéro est déjà utilisé'})
        if User.objects.filter(username=attrs['username']).exists():
            raise serializers.ValidationError({'username': 'Ce nom est déjà utilisé'})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        user = User.objects.create_user(
            phone=validated_data['phone'],
            password=validated_data['password'],
            username=validated_data.get('username'),
            role=User.Role.CLIENT,
        )
        ClientProfile.objects.create(user=user)
        return user


class AgentRegisterSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=32)
    password = serializers.CharField(write_only=True, min_length=6)
    username = serializers.CharField(max_length=150, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    agency_name = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def validate(self, attrs):
        if User.objects.filter(phone=attrs['phone']).exists():
            raise serializers.ValidationError({'phone': 'Ce numéro est déjà utilisé'})
        if attrs.get('email') and User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({'email': 'Cet email est déjà utilisé'})
        if attrs.get('username') and User.objects.filter(username=attrs['username']).exists():
            raise serializers.ValidationError({'username': 'Ce nom est déjà utilisé'})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        user = User.objects.create_user(
            phone=validated_data['phone'],
            password=validated_data['password'],
            username=validated_data.get('username') or None,
            email=validated_data.get('email') or None,
            role=User.Role.AGENT,
        )
        AgentProfile.objects.create(
            user=user,
            agency_name=validated_data.get('agency_name', ''),
        )
        return user


class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=32)
    password = serializers.CharField(write_only=True)


class OTPRequestSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=32)
    # Par simplicité, on génère ici (en réel: générer côté service et envoyer par SMS)
    code = serializers.CharField(max_length=6, read_only=True)

    def validate(self, attrs):
        code = f"{random.randint(0, 999999):06d}"
        attrs['code'] = code
        return attrs


class OTPVerifySerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=32)
    code = serializers.CharField(max_length=6)


class MeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'phone', 'username', 'email', 'role']

