from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager,
)


class UserManager(BaseUserManager):
    def create_user(self, phone=None, password=None, **extra_fields):
        if not phone:
            raise ValueError("Le numéro de téléphone est requis")
        email = extra_fields.get('email')
        if email:
            extra_fields['email'] = self.normalize_email(email)
        user = self.model(phone=phone, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault('role', User.Role.ADMIN)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(phone, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        CLIENT = 'CLIENT', 'Client'
        AGENT = 'AGENT', 'Agent'
        ADMIN = 'ADMIN', 'Admin'

    # Identifiants
    phone = models.CharField(
        max_length=32,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^\+[1-9]\d{5,14}$',
                message='Le numéro doit être au format E.164 (ex: +2250123456789)',
            )
        ],
    )
    username = models.CharField(max_length=150, unique=True, null=True, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.CLIENT)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # Plus de champs OTP: flux d'inscription stateless (D7)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    def __str__(self) -> str:
        return self.phone or self.email or str(self.pk)

    class Meta:
        ordering = ['-created_at']


class ClientProfile(models.Model):
    class Intent(models.TextChoices):
        RENT = 'RENT', 'Location'
        BUY = 'BUY', 'Achat'

    class Furnishing(models.TextChoices):
        ANY = 'ANY', 'Indifférent'
        FURNISHED = 'FURNISHED', 'Meublé'
        UNFURNISHED = 'UNFURNISHED', 'Non meublé'

    class KYCStatus(models.TextChoices):
        NONE = 'NONE', 'Aucun'
        PENDING = 'PENDING', 'En cours'
        VERIFIED = 'VERIFIED', 'Vérifié'

    user = models.OneToOneField('users.User', on_delete=models.CASCADE, related_name='client_profile')
    whatsapp_phone = models.CharField(max_length=32, blank=True)
    is_phone_verified = models.BooleanField(default=False)

    # Préférences et notifications
    preferences = models.JSONField(default=dict, blank=True)
    language = models.CharField(max_length=8, default='fr')
    device_tokens = models.JSONField(default=list, blank=True)

    # KYC et informations optionnelles
    kyc_status = models.CharField(max_length=16, choices=KYCStatus.choices, default=KYCStatus.NONE)
    id_number = models.CharField(max_length=64, blank=True)
    referral_code = models.CharField(max_length=32, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"ClientProfile<{self.user.phone}>"


class AgentProfile(models.Model):
    class KycStatus(models.TextChoices):
        NOT_SUBMITTED = 'NOT_SUBMITTED', 'Non soumis'
        PENDING = 'PENDING', 'En attente de vérification'
        APPROVED = 'APPROVED', 'Approuvé'
        REJECTED = 'REJECTED', 'Rejeté'

    user = models.OneToOneField('users.User', on_delete=models.CASCADE, related_name='agent_profile')
    agency_name = models.CharField(max_length=255, blank=True)
    verified = models.BooleanField(default=False)
    kyc_status = models.CharField(max_length=16, choices=KycStatus.choices, default=KycStatus.NOT_SUBMITTED)
    kyc_rejection_reason = models.TextField(blank=True)
    bio = models.TextField(blank=True)

    contact_phone = models.CharField(max_length=32, blank=True)
    contact_email = models.EmailField(blank=True)

    # Vérification d'identité (KYC)
    national_id_number = models.CharField(max_length=64, blank=True)
    national_id_document = models.ImageField(upload_to='agents/id_documents/', null=True, blank=True)

    # Photo de profil de l'agent
    profile_photo = models.ImageField(upload_to='agents/profile_photos/', null=True, blank=True)

    # Statut partenaire (attribué manuellement via admin)
    is_partner = models.BooleanField(default=False)
    partner_since = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"AgentProfile<{self.user.phone}>"


class AgentDocument(models.Model):
    class DocType(models.TextChoices):
        CNI = 'CNI', 'Carte Nationale d\'Identité'
        PASSPORT = 'PASSPORT', 'Passeport'
        PERMIT = 'PERMIT', 'Permis de conduire'
        OTHER = 'OTHER', 'Autre'

    class Side(models.TextChoices):
        RECTO = 'RECTO', 'Recto'
        VERSO = 'VERSO', 'Verso'
        SINGLE = 'SINGLE', 'Document unique'

    agent_profile = models.ForeignKey(AgentProfile, on_delete=models.CASCADE, related_name='documents')
    file = models.FileField(upload_to='agents/documents/')
    doc_type = models.CharField(max_length=16, choices=DocType.choices, default=DocType.CNI)
    side = models.CharField(max_length=8, choices=Side.choices, default=Side.SINGLE)
    label = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('agent_profile', 'doc_type', 'side')]

    def __str__(self) -> str:
        return f"AgentDocument<{self.agent_profile.user.phone}:{self.doc_type}/{self.side}>"


class LegalConsent(models.Model):
    """Trace juridique du consentement utilisateur aux documents légaux."""

    class DocumentType(models.TextChoices):
        CGU = 'CGU', 'Conditions Générales d\'Utilisation'
        PRIVACY = 'PRIVACY', 'Politique de Confidentialité'
        AGENT_CONDITIONS = 'AGENT_CONDITIONS', 'Conditions Spécifiques Agents'

    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='legal_consents')
    document_type = models.CharField(max_length=32, choices=DocumentType.choices)
    document_version = models.CharField(max_length=32)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)
    accepted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-accepted_at']
        indexes = [
            models.Index(fields=['user', 'document_type']),
        ]

    def __str__(self) -> str:
        return f"Consent<{self.user.phone}:{self.document_type}:{self.document_version}>"


class Notification(models.Model):
    class Category(models.TextChoices):
        KYC = 'KYC', 'Vérification KYC'
        SYSTEM = 'SYSTEM', 'Système'
        VISIT = 'VISIT', 'Visite'
        WALLET = 'WALLET', 'Wallet'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    category = models.CharField(max_length=16, choices=Category.choices, default=Category.SYSTEM)
    title = models.CharField(max_length=255)
    message = models.TextField()
    link = models.CharField(
        'Lien de navigation', max_length=255, blank=True,
        help_text='Route frontend (ex: /agent/visits, /agent/settings#kyc)',
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"Notification<{self.user.phone}:{self.title[:30]}>"


