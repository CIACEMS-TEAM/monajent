"""
Modèles PackPurchase & VirtualKeyUsage
───────────────────────────────────────
Pack standard : 500 XOF → 33 clés virtuelles + 1 clé physique.
Chaque visionnage consomme 1 clé virtuelle et crée un VirtualKeyUsage
qui déclenche :
  • WalletEntry(CREDIT, 10 XOF) pour l'agent
  • PlatformRevenue(5 XOF) pour la plateforme
"""

from decimal import Decimal
from django.conf import settings
from django.db import models


# ── Constantes métier ─────────────────────────────────────────
PACK_PRICE = Decimal('500.00')        # Prix du pack (XOF)
PACK_VIRTUAL_KEYS = 33                # Clés virtuelles par pack
AGENT_REVENUE_PER_VIEW = Decimal('10.00')
PLATFORM_REVENUE_PER_VIEW = Decimal('5.00')


class PackPurchase(models.Model):
    """
    Achat d'un pack par un client.
    1 pack = 33 clés virtuelles + 1 clé physique (visite).
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='packs',
        limit_choices_to={'role': 'CLIENT'},
    )

    # Montant & devise
    amount = models.DecimalField(
        'Montant', max_digits=10, decimal_places=2, default=PACK_PRICE,
    )
    currency = models.CharField('Devise', max_length=3, default='XOF')

    # Clés virtuelles
    virtual_total = models.PositiveSmallIntegerField(
        'Clés virtuelles totales', default=PACK_VIRTUAL_KEYS,
    )
    virtual_used = models.PositiveSmallIntegerField(
        'Clés virtuelles utilisées', default=0,
    )

    # Clé physique (visite)
    has_physical_key = models.BooleanField(
        'Clé physique disponible', default=True,
    )
    is_locked_by_visit = models.BooleanField(
        'Pack verrouillé par visite', default=False,
        help_text='True dès qu\'une visite physique consomme la clé physique.',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(
                fields=['user', 'is_locked_by_visit', '-created_at'],
                name='idx_pack_user_active',
            ),
        ]

    def __str__(self) -> str:
        remaining = self.virtual_remaining
        return f"Pack<{self.user.phone}> {remaining}/{self.virtual_total} clés"

    # ── Propriétés calculées ──────────────────────────────────
    @property
    def virtual_remaining(self) -> int:
        """Clés virtuelles restantes (0 si pack verrouillé par visite)."""
        if self.is_locked_by_visit:
            return 0
        return self.virtual_total - self.virtual_used

    @property
    def is_exhausted(self) -> bool:
        """True si plus aucune clé (virtuelle ou physique) n'est utilisable."""
        return self.virtual_remaining == 0 and not self.has_physical_key


class VirtualKeyUsage(models.Model):
    """
    1 enregistrement = 1 visionnage = 1 clé virtuelle consommée.
    Contrainte UNIQUE (pack, video, user) pour anti-double-crédit.
    Chaque usage génère :
      • 1 WalletEntry(CREDIT, 10 XOF) → agent
      • 1 PlatformRevenue(5 XOF) → plateforme
    """

    pack = models.ForeignKey(
        PackPurchase, on_delete=models.CASCADE, related_name='key_usages',
    )
    video = models.ForeignKey(
        'listings.Video', on_delete=models.CASCADE, related_name='key_usages',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='video_views',
        help_text='Client qui a visionné',
    )
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='earned_views',
        help_text='Agent propriétaire de l\'annonce (bénéficiaire)',
    )

    # Montants enregistrés (pour traçabilité historique)
    amount_agent = models.DecimalField(
        'Revenu agent', max_digits=10, decimal_places=2,
        default=AGENT_REVENUE_PER_VIEW,
    )
    amount_platform = models.DecimalField(
        'Revenu plateforme', max_digits=10, decimal_places=2,
        default=PLATFORM_REVENUE_PER_VIEW,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['pack', 'video', 'user'],
                name='unique_pack_video_user',
            ),
        ]
        indexes = [
            # "Ce client a-t-il déjà vu cette vidéo ?" (toutes packs confondus)
            models.Index(fields=['user', 'video'], name='idx_usage_user_video'),
            # Stats agent : vues reçues par période
            models.Index(fields=['agent', '-created_at'], name='idx_usage_agent_date'),
            # Stats vidéo : vues par vidéo par période
            models.Index(fields=['video', '-created_at'], name='idx_usage_video_date'),
        ]

    def __str__(self) -> str:
        return f"View<{self.user.phone} → {self.video}>"
