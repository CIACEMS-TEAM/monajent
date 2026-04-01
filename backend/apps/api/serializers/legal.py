from rest_framework import serializers

from apps.users.models import LegalConsent


class LegalConsentAcceptSerializer(serializers.Serializer):
    document_type = serializers.ChoiceField(
        choices=['AGENT_CONDITIONS'],
        help_text='Seul AGENT_CONDITIONS est accepté via cet endpoint (CGU/PRIVACY sont gérés à l\'inscription).',
    )


class LegalConsentReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = LegalConsent
        fields = ['id', 'document_type', 'document_version', 'accepted_at']
        read_only_fields = fields
