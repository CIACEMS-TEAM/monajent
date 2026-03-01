"""
Serializers Agent — Monajent
─────────────────────────────
• AgentProfileReadSerializer     → profil agent complet (lecture)
• AgentProfileUpdateSerializer   → mise à jour partielle du profil
• AgentDocumentSerializer        → documents KYC
"""

from rest_framework import serializers

from apps.users.models import User, AgentProfile, AgentDocument


# ═══════════════════════════════════════════════════════════════
# Documents KYC
# ═══════════════════════════════════════════════════════════════


class AgentDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentDocument
        fields = ['id', 'file', 'doc_type', 'side', 'label', 'uploaded_at', 'updated_at']
        read_only_fields = ['id', 'uploaded_at', 'updated_at']


KYC_MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 Mo
KYC_ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'pdf'}


class AgentDocumentUploadSerializer(serializers.Serializer):
    """Upload ou remplacement d'un document KYC."""
    file = serializers.FileField()
    doc_type = serializers.ChoiceField(choices=AgentDocument.DocType.choices)
    side = serializers.ChoiceField(choices=AgentDocument.Side.choices)

    def validate_file(self, value):
        if value.size > KYC_MAX_FILE_SIZE:
            raise serializers.ValidationError(
                f"Le fichier dépasse la taille maximale de {KYC_MAX_FILE_SIZE // (1024 * 1024)} Mo."
            )
        ext = value.name.rsplit('.', 1)[-1].lower() if '.' in value.name else ''
        if ext not in KYC_ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                f"Format non supporté. Formats acceptés : JPG, PNG, PDF."
            )
        return value

    def validate(self, attrs):
        doc_type = attrs['doc_type']
        side = attrs['side']

        if doc_type == AgentDocument.DocType.CNI:
            if side == AgentDocument.Side.SINGLE:
                raise serializers.ValidationError(
                    "Pour une CNI, veuillez spécifier RECTO ou VERSO."
                )
        else:
            if side != AgentDocument.Side.SINGLE:
                raise serializers.ValidationError(
                    "Pour ce type de document, utilisez SINGLE."
                )
        return attrs


# ═══════════════════════════════════════════════════════════════
# Profil agent
# ═══════════════════════════════════════════════════════════════


class AgentProfileReadSerializer(serializers.ModelSerializer):
    """Lecture du profil agent complet (user + agent_profile + documents)."""
    phone = serializers.CharField(source='user.phone', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    role = serializers.CharField(source='user.role', read_only=True)
    member_since = serializers.DateTimeField(source='user.created_at', read_only=True)
    documents = AgentDocumentSerializer(many=True, read_only=True)

    class Meta:
        model = AgentProfile
        fields = [
            'phone', 'username', 'email', 'role', 'member_since',
            'agency_name', 'verified', 'kyc_status', 'kyc_rejection_reason', 'bio',
            'contact_phone', 'contact_email',
            'national_id_number', 'national_id_document',
            'profile_photo',
            'documents',
            'created_at', 'updated_at',
        ]
        read_only_fields = fields


class AgentProfileUpdateSerializer(serializers.Serializer):
    """Mise à jour partielle du profil agent (multipart pour fichiers)."""
    username = serializers.CharField(max_length=150, required=False)
    email = serializers.EmailField(required=False, allow_blank=True)

    agency_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    bio = serializers.CharField(required=False, allow_blank=True)
    contact_phone = serializers.CharField(max_length=32, required=False, allow_blank=True)
    contact_email = serializers.EmailField(required=False, allow_blank=True)

    national_id_number = serializers.CharField(max_length=64, required=False, allow_blank=True)
    national_id_document = serializers.ImageField(required=False, allow_null=True)

    profile_photo = serializers.ImageField(required=False, allow_null=True)

    def validate_username(self, value):
        user = self.context.get('user')
        if user and User.objects.filter(username=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("Ce nom d'utilisateur est déjà pris.")
        return value

    def validate_email(self, value):
        if not value:
            return value
        user = self.context.get('user')
        if user and User.objects.filter(email=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("Cet email est déjà utilisé.")
        return value
