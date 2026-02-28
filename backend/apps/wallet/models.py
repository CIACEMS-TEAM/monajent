"""
Modèles Wallet, WalletEntry, PlatformRevenue, WithdrawalRequest
───────────────────────────────────────────────────────────────
Portefeuille agent : accumule les gains (10 XOF par interaction).
Seuil minimum de retrait : 2 000 XOF.

Sources de revenus agent (10 XOF chacune) :
  • Visionnage vidéo (VirtualKeyUsage)
  • Visite physique (VisitRequest)
PlatformRevenue (5 XOF par interaction) tracé pour chaque source.

Flux de retrait :
  1. Agent configure son code PIN de retrait (4 chiffres, hashé)
  2. Agent demande un retrait (≥ 2 000 XOF, méthode + numéro + PIN)
  3. Le montant est bloqué (balance déduite immédiatement → anti-double-retrait)
  4. Admin approuve → transfert effectué, WithdrawalRequest = COMPLETED
  5. Admin rejette → montant restauré au wallet, WithdrawalRequest = REJECTED

Sécurité PIN :
  • Le PIN est hashé (make_password) — jamais stocké en clair
  • Requis à chaque demande de retrait
  • Protège contre les accès non autorisés au compte
"""

from decimal import Decimal
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from django.db import models


MINIMUM_WITHDRAWAL = Decimal('2000.00')  # Seuil retrait (XOF)
PIN_LENGTH = 4                           # Longueur du code PIN


class Wallet(models.Model):
    """Portefeuille unique d'un agent."""

    agent = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wallet',
        limit_choices_to={'role': 'AGENT'},
    )
    balance = models.DecimalField(
        'Solde (XOF)', max_digits=12, decimal_places=2, default=Decimal('0.00'),
    )
    total_earned = models.DecimalField(
        'Total gagné (XOF)', max_digits=12, decimal_places=2, default=Decimal('0.00'),
        help_text='Cumul historique de tous les crédits.',
    )
    total_withdrawn = models.DecimalField(
        'Total retiré (XOF)', max_digits=12, decimal_places=2, default=Decimal('0.00'),
    )

    # ── Code PIN de retrait (hashé) ───────────────────────
    withdrawal_pin_hash = models.CharField(
        'PIN de retrait (hashé)', max_length=128, blank=True,
        help_text='Code PIN à 4 chiffres, hashé via make_password. '
                  'Requis pour chaque demande de retrait.',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        pass  # OneToOneField crée déjà un index unique sur agent

    def __str__(self) -> str:
        return f"Wallet<{self.agent.phone}> {self.balance} XOF"

    @property
    def can_withdraw(self) -> bool:
        return self.balance >= MINIMUM_WITHDRAWAL

    @property
    def has_pin(self) -> bool:
        """True si l'agent a configuré son code PIN de retrait."""
        return bool(self.withdrawal_pin_hash)

    def set_pin(self, raw_pin: str) -> None:
        """Hashe et enregistre le code PIN."""
        self.withdrawal_pin_hash = make_password(raw_pin)
        self.save(update_fields=['withdrawal_pin_hash', 'updated_at'])

    def check_pin(self, raw_pin: str) -> bool:
        """Vérifie le code PIN contre le hash stocké."""
        if not self.withdrawal_pin_hash:
            return False
        return check_password(raw_pin, self.withdrawal_pin_hash)


class WalletEntry(models.Model):
    """Ligne de mouvement dans le portefeuille agent."""

    class EntryType(models.TextChoices):
        CREDIT = 'CREDIT', 'Crédit (gain)'
        DEBIT = 'DEBIT', 'Débit (retrait)'

    class Source(models.TextChoices):
        VIDEO_VIEW = 'VIDEO_VIEW', 'Visionnage vidéo'
        PHYSICAL_VISIT = 'PHYSICAL_VISIT', 'Visite physique'
        WITHDRAWAL = 'WITHDRAWAL', 'Retrait'
        ADJUSTMENT = 'ADJUSTMENT', 'Ajustement admin'

    wallet = models.ForeignKey(
        Wallet, on_delete=models.CASCADE, related_name='entries',
    )
    entry_type = models.CharField(
        'Type', max_length=8, choices=EntryType.choices,
    )
    source = models.CharField(
        'Source', max_length=20, choices=Source.choices, default=Source.VIDEO_VIEW,
    )
    amount = models.DecimalField('Montant', max_digits=10, decimal_places=2)
    label = models.CharField('Libellé', max_length=255, blank=True)

    # Référence optionnelle au visionnage
    ref_usage = models.OneToOneField(
        'packs.VirtualKeyUsage',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='wallet_entry',
        help_text='VirtualKeyUsage ayant généré ce crédit.',
    )

    # Référence optionnelle à la visite physique
    ref_visit = models.OneToOneField(
        'visits.VisitRequest',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='wallet_entry',
        help_text='VisitRequest ayant généré ce crédit.',
    )

    # Pour les retraits : méthode et référence
    withdrawal_method = models.CharField(
        'Méthode de retrait', max_length=32, blank=True,
        help_text='Ex: ORANGE_MONEY, WAVE, MTN',
    )
    withdrawal_ref = models.CharField(
        'Référence retrait', max_length=128, blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['wallet', '-created_at'], name='idx_entry_wallet_date'),
        ]

    def __str__(self) -> str:
        sign = '+' if self.entry_type == self.EntryType.CREDIT else '-'
        return f"{sign}{self.amount} XOF — {self.label}"


class PlatformRevenue(models.Model):
    """
    Revenu plateforme par interaction (5 XOF).
    Source : visionnage vidéo OU visite physique.
    """

    class Source(models.TextChoices):
        VIDEO_VIEW = 'VIDEO_VIEW', 'Visionnage vidéo'
        PHYSICAL_VISIT = 'PHYSICAL_VISIT', 'Visite physique'

    source = models.CharField(
        'Source', max_length=20, choices=Source.choices, default=Source.VIDEO_VIEW,
    )

    # Exactement UNE des deux FK doit être renseignée
    usage = models.OneToOneField(
        'packs.VirtualKeyUsage',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='platform_revenue',
    )
    visit = models.OneToOneField(
        'visits.VisitRequest',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='platform_revenue',
    )

    amount = models.DecimalField(
        'Montant', max_digits=10, decimal_places=2, default=Decimal('5.00'),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        ref = self.usage or self.visit
        return f"PlatformRevenue<{self.amount} XOF — {self.get_source_display()} — {ref}>"


class WithdrawalRequest(models.Model):
    """
    Demande de retrait par un agent.

    Flux :
      PENDING  → agent fait la demande, montant bloqué (solde déduit)
      COMPLETED → admin approuve, transfert effectué
      REJECTED  → admin rejette, montant restauré au wallet
    """

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'En attente'
        COMPLETED = 'COMPLETED', 'Effectué'
        REJECTED = 'REJECTED', 'Rejeté'

    class Method(models.TextChoices):
        ORANGE_MONEY = 'ORANGE_MONEY', 'Orange Money'
        WAVE = 'WAVE', 'Wave'
        MTN = 'MTN', 'MTN Mobile Money'

    wallet = models.ForeignKey(
        Wallet, on_delete=models.CASCADE, related_name='withdrawals',
    )
    amount = models.DecimalField('Montant (XOF)', max_digits=12, decimal_places=2)
    method = models.CharField(
        'Méthode', max_length=16, choices=Method.choices,
    )
    phone_number = models.CharField(
        'Numéro de destination', max_length=20,
        help_text='Numéro mobile money pour le virement.',
    )

    status = models.CharField(
        'Statut', max_length=12, choices=Status.choices, default=Status.PENDING,
    )

    # Référence au WalletEntry DEBIT créé lors de la demande
    wallet_entry = models.OneToOneField(
        WalletEntry,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='withdrawal_request',
        help_text='Entrée DEBIT créée lors de la demande.',
    )

    # Admin qui traite la demande
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='processed_withdrawals',
        help_text='Admin ayant traité la demande.',
    )
    processed_at = models.DateTimeField('Traité le', null=True, blank=True)
    admin_note = models.TextField('Note admin', blank=True)

    # Référence de transaction du provider (si complété)
    transaction_ref = models.CharField(
        'Réf. transaction', max_length=128, blank=True,
        help_text='Référence de la transaction mobile money.',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['wallet', 'status', '-created_at'], name='idx_withdrawal_wallet'),
            models.Index(fields=['status', '-created_at'], name='idx_withdrawal_status'),
        ]

    def __str__(self) -> str:
        return (
            f"Retrait<{self.wallet.agent.phone}> "
            f"{self.amount} XOF via {self.get_method_display()} [{self.status}]"
        )
