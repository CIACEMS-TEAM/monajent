from dataclasses import dataclass
import random
from typing import Any

from django.db import transaction
from rest_framework import serializers

from apps.users.models import User, ClientProfile, AgentProfile, PendingSignup


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
        # Ne PAS créer l'utilisateur maintenant: créer une demande en attente
        phone = validated_data['phone']
        if User.objects.filter(phone=phone).exists():
            raise serializers.ValidationError({'phone': 'Ce numéro est déjà utilisé'})
        pending, _ = PendingSignup.objects.get_or_create(phone=phone, defaults={
            'role': PendingSignup.Role.CLIENT,
            'username': validated_data['username'],
        })
        pending.role = PendingSignup.Role.CLIENT
        pending.username = validated_data['username']
        pending.set_password(validated_data['password'])
        pending.save()
        return pending


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
        phone = validated_data['phone']
        if User.objects.filter(phone=phone).exists():
            raise serializers.ValidationError({'phone': 'Ce numéro est déjà utilisé'})
        pending, _ = PendingSignup.objects.get_or_create(phone=phone, defaults={
            'role': PendingSignup.Role.AGENT,
            'username': validated_data.get('username') or ''
        })
        pending.role = PendingSignup.Role.AGENT
        pending.username = validated_data.get('username') or ''
        pending.email = validated_data.get('email') or None
        pending.agency_name = validated_data.get('agency_name') or ''
        pending.set_password(validated_data['password'])
        pending.save()
        return pending


class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=32)
    password = serializers.CharField(write_only=True)


class OTPRequestSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=32)
    # pour D7, on n’a plus besoin de générer localement


class OTPVerifySerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=32)
    code = serializers.CharField(max_length=6)
    otp_id = serializers.CharField(max_length=128, required=False, allow_blank=True)


class MeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'phone', 'username', 'email', 'role']

