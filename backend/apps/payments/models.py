"""
Modèle Payment
──────────────
Paiement lié à l'achat d'un pack.
Le pack est créé automatiquement après confirmation du paiement (webhook).
Providers : Orange Money, Wave, MTN, carte bancaire.

Flux :
  1. Client POST /api/client/packs/buy/  → Payment(PENDING) + checkout_url
  2. Provider notifie le webhook          → Payment(PAID) + PackPurchase créé
"""

from django.conf import settings
from django.db import models


class Payment(models.Model):
    """Paiement pour un achat de pack."""

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'En attente'
        PAID = 'PAID', 'Payé'
        FAILED = 'FAILED', 'Échoué'
        REFUNDED = 'REFUNDED', 'Remboursé'

    class Provider(models.TextChoices):
        PAYSTACK = 'PAYSTACK', 'Paystack'
        ORANGE_MONEY = 'ORANGE_MONEY', 'Orange Money'
        WAVE = 'WAVE', 'Wave'
        MTN = 'MTN', 'MTN Money'
        CARD = 'CARD', 'Carte bancaire'
        OTHER = 'OTHER', 'Autre'

    # ── Relations ──────────────────────────────────────────────
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payments',
        limit_choices_to={'role': 'CLIENT'},
    )
    pack = models.OneToOneField(
        'packs.PackPurchase',
        on_delete=models.SET_NULL,
        related_name='payment',
        null=True,
        blank=True,
        help_text='Créé automatiquement après paiement confirmé.',
    )

    # ── Détails du paiement ───────────────────────────────────
    provider = models.CharField(
        'Fournisseur', max_length=16, choices=Provider.choices,
    )
    tx_ref = models.CharField(
        'Référence transaction', max_length=128, unique=True,
    )
    provider_tx_id = models.CharField(
        'ID transaction provider', max_length=255, blank=True, default='',
        help_text='Identifiant de la transaction chez le provider externe.',
    )
    status = models.CharField(
        'Statut', max_length=16, choices=Status.choices, default=Status.PENDING,
    )
    amount = models.DecimalField('Montant', max_digits=10, decimal_places=2)
    currency = models.CharField('Devise', max_length=3, default='XOF')

    checkout_url = models.URLField(
        'URL de paiement', max_length=512, blank=True, default='',
        help_text='URL de la page de paiement hébergée par le provider.',
    )

    # Métadonnées provider (réponse webhook, etc.)
    provider_metadata = models.JSONField(
        'Métadonnées provider', default=dict, blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at'], name='idx_payment_user_date'),
            models.Index(fields=['status'], name='idx_payment_status'),
        ]

    def __str__(self) -> str:
        return f"Payment<{self.tx_ref}> {self.amount} {self.currency} [{self.status}]"
