"""
Modèles Listing, ListingImage, Video, ListingReport
────────────────────────────────────────────────────
Biens immobiliers publiés par les agents, avec photos et vidéos.
Vidéos protégées : le client ne voit que le thumbnail ; la lecture
complète consomme 1 clé virtuelle (VirtualKeyUsage).

Cycle de vie d'une annonce :
  ACTIF → INACTIF (agent désactive manuellement)
  ACTIF → EXPIRED (auto, après expires_at sans renouvellement)
  ACTIF → SUSPENDED (auto, après N signalements ou par admin)
  EXPIRED / INACTIF → ACTIF (renouvellement par l'agent)
"""

import uuid
from datetime import timedelta
from django.conf import settings
from django.db import models
from django.utils import timezone


# ── Constantes configurables ─────────────────────────────────
LISTING_EXPIRY_DAYS = 7
LISTING_AUTO_SUSPEND_REPORTS = 3


class Listing(models.Model):
    """Annonce immobilière publiée par un agent."""

    class Type(models.TextChoices):
        LOCATION = 'LOCATION', 'Location'
        VENTE = 'VENTE', 'Vente'

    class Status(models.TextChoices):
        ACTIF = 'ACTIF', 'Actif'
        INACTIF = 'INACTIF', 'Inactif'
        EXPIRED = 'EXPIRED', 'Expirée'
        SUSPENDED = 'SUSPENDED', 'Suspendue'

    class Furnishing(models.TextChoices):
        FURNISHED = 'FURNISHED', 'Meublé'
        UNFURNISHED = 'UNFURNISHED', 'Non meublé'
        SEMI_FURNISHED = 'SEMI_FURNISHED', 'Semi-meublé'

    # ── Relations ──────────────────────────────────────────────
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='listings',
        limit_choices_to={'role': 'AGENT'},
    )

    # ── Informations principales ──────────────────────────────
    title = models.CharField('Titre', max_length=255)
    description = models.TextField('Description détaillée', blank=True)
    listing_type = models.CharField(
        'Type', max_length=16, choices=Type.choices,
    )
    status = models.CharField(
        'Statut', max_length=16, choices=Status.choices, default=Status.ACTIF,
    )

    # ── Localisation ──────────────────────────────────────────
    city = models.CharField('Ville', max_length=100)
    neighborhood = models.CharField('Quartier', max_length=100, blank=True)
    address = models.CharField('Adresse', max_length=255, blank=True)
    latitude = models.DecimalField(
        'Latitude', max_digits=9, decimal_places=6, null=True, blank=True,
    )
    longitude = models.DecimalField(
        'Longitude', max_digits=9, decimal_places=6, null=True, blank=True,
    )

    # ── Caractéristiques du bien ──────────────────────────────
    price = models.DecimalField(
        'Prix affiché (XOF)', max_digits=12, decimal_places=2,
    )
    rooms = models.PositiveSmallIntegerField('Nombre de pièces', null=True, blank=True)
    bedrooms = models.PositiveSmallIntegerField('Chambres', null=True, blank=True)
    bathrooms = models.PositiveSmallIntegerField('Salles de bain', null=True, blank=True)
    surface_m2 = models.DecimalField(
        'Surface (m²)', max_digits=10, decimal_places=2, null=True, blank=True,
    )
    furnishing = models.CharField(
        'Ameublement', max_length=16, choices=Furnishing.choices,
        blank=True,
    )

    # ── Commodités (JSON list) ────────────────────────────────
    amenities = models.JSONField(
        'Commodités', default=list, blank=True,
        help_text='Liste de commodités : eau, electricite, parking, gardien, etc.',
    )

    # ── Compteurs dénormalisés (mis à jour par signals / services) ─
    views_count = models.PositiveIntegerField('Nombre de vues', default=0, editable=False)
    favorites_count = models.PositiveIntegerField('Favoris', default=0, editable=False)
    reports_count = models.PositiveSmallIntegerField(
        'Signalements', default=0, editable=False,
    )

    # ── Cycle de vie ──────────────────────────────────────────
    published_at = models.DateTimeField(
        'Publié le', null=True, blank=True,
        help_text='Date de la dernière publication/renouvellement.',
    )
    expires_at = models.DateTimeField(
        'Expire le', null=True, blank=True,
        help_text='Date d\'expiration automatique.',
    )

    # ── Timestamps ────────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['agent', '-created_at'], name='idx_listing_agent_date'),
            models.Index(fields=['city', 'listing_type', 'status'], name='idx_listing_search'),
            models.Index(fields=['status', '-created_at'], name='idx_listing_active'),
            models.Index(fields=['status', 'listing_type', 'price'], name='idx_listing_price'),
            # Tâche d'expiration : annonces actives dont expires_at est passé
            models.Index(fields=['status', 'expires_at'], name='idx_listing_expiry'),
        ]

    def __str__(self) -> str:
        return f"{self.title} — {self.city} ({self.get_listing_type_display()})"

    def save(self, *args, **kwargs):
        # Auto-set published_at et expires_at à la première publication
        if not self.published_at and self.status == self.Status.ACTIF:
            self.published_at = timezone.now()
            self.expires_at = self.published_at + timedelta(days=LISTING_EXPIRY_DAYS)
        super().save(*args, **kwargs)

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return timezone.now() > self.expires_at

    @property
    def days_remaining(self) -> int:
        """Jours restants avant expiration. 0 si expiré."""
        if self.expires_at is None:
            return 0
        delta = (self.expires_at - timezone.now()).days
        return max(delta, 0)

    def renew(self, days: int = LISTING_EXPIRY_DAYS):
        """Renouvelle l'annonce pour N jours supplémentaires."""
        now = timezone.now()
        self.status = self.Status.ACTIF
        self.published_at = now
        self.expires_at = now + timedelta(days=days)
        self.save(update_fields=['status', 'published_at', 'expires_at', 'updated_at'])


class ListingImage(models.Model):
    """Photo d'une annonce (N photos par listing)."""

    listing = models.ForeignKey(
        Listing, on_delete=models.CASCADE, related_name='images',
    )
    image = models.ImageField(upload_to='listings/images/')
    caption = models.CharField('Légende', max_length=255, blank=True)
    order = models.PositiveSmallIntegerField('Ordre', default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self) -> str:
        return f"Image #{self.order} — {self.listing.title}"


class Video(models.Model):
    """
    Vidéo rattachée à une annonce.
    Accès protégé : seul le thumbnail est visible gratuitement.
    La lecture complète nécessite la consommation d'une clé virtuelle.

    Anti-fraude : file_hash (SHA-256) empêche un agent de téléverser
    la même vidéo plusieurs fois pour gonfler ses revenus.
    """

    listing = models.ForeignKey(
        Listing, on_delete=models.CASCADE, related_name='videos',
    )
    file = models.FileField(upload_to='listings/videos/')
    thumbnail = models.ImageField(
        upload_to='listings/thumbnails/', null=True, blank=True,
    )
    duration_sec = models.PositiveIntegerField('Durée (s)', null=True, blank=True)

    # Identifiant unique pour les URLs signées / accès protégé
    access_key = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    # Anti-fraude : SHA-256 du fichier vidéo
    file_hash = models.CharField(
        'Hash SHA-256', max_length=64, blank=True, db_index=True,
        help_text='SHA-256 du fichier vidéo, calculé à l\'upload pour détection de doublons.',
    )

    # Compteur dénormalisé
    views_count = models.PositiveIntegerField('Vues', default=0, editable=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['listing', '-created_at'], name='idx_video_listing_date'),
        ]
        constraints = [
            # Un agent ne peut pas avoir deux vidéos identiques (même hash)
            # via listing → agent. Vérifié au niveau service (cross-table).
        ]

    def __str__(self) -> str:
        return f"Video<{self.listing.title}> ({self.duration_sec or '?'}s)"


# ═══════════════════════════════════════════════════════════════
# Signalement d'annonce
# ═══════════════════════════════════════════════════════════════


class ListingReport(models.Model):
    """
    Signalement d'une annonce par un client.
    Après N signalements (LISTING_AUTO_SUSPEND_REPORTS), l'annonce
    est automatiquement suspendue en attente de modération admin.
    """

    class Reason(models.TextChoices):
        ALREADY_SOLD = 'ALREADY_SOLD', 'Bien déjà vendu'
        ALREADY_RENTED = 'ALREADY_RENTED', 'Bien déjà loué'
        MISLEADING = 'MISLEADING', 'Annonce trompeuse / vidéo ne correspond pas'
        DUPLICATE_VIDEO = 'DUPLICATE_VIDEO', 'Même vidéo que sur une autre annonce'
        SCAM = 'SCAM', 'Arnaque suspectée'
        OTHER = 'OTHER', 'Autre'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'En attente'
        REVIEWED = 'REVIEWED', 'Examiné'
        RESOLVED = 'RESOLVED', 'Résolu (annonce supprimée/suspendue)'
        DISMISSED = 'DISMISSED', 'Rejeté (faux signalement)'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='listing_reports',
        limit_choices_to={'role': 'CLIENT'},
        help_text='Client qui signale',
    )
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name='reports',
    )
    reason = models.CharField(
        'Raison', max_length=24, choices=Reason.choices,
    )
    description = models.TextField(
        'Détails', blank=True,
        help_text='Explication facultative du signalement.',
    )
    status = models.CharField(
        'Statut', max_length=16, choices=Status.choices, default=Status.PENDING,
    )
    admin_note = models.TextField('Note admin', blank=True)
    reviewed_at = models.DateTimeField('Examiné le', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            # Un client ne peut signaler la même annonce qu'une seule fois
            models.UniqueConstraint(
                fields=['user', 'listing'],
                name='unique_user_listing_report',
            ),
        ]
        indexes = [
            models.Index(fields=['listing', 'status'], name='idx_report_listing_status'),
            models.Index(fields=['status', '-created_at'], name='idx_report_pending'),
        ]

    def __str__(self) -> str:
        return f"Report<{self.user.phone} → {self.listing.title}> [{self.get_reason_display()}]"
