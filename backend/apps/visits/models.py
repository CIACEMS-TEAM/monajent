"""
Modèles VisitRequest & AgentAvailabilitySlot
─────────────────────────────────────────────
Flux de visite physique — Monajent

1. L'agent pré-configure ses créneaux de disponibilité (ex: Lundi 9h-12h)
2. Le client voit les créneaux et en choisit un
3. La demande consomme : 1 clé physique + 1 clé virtuelle (agent touche 10 XOF)
4. L'agent confirme la demande (ou elle expire après 48h → clés restaurées)
5. Le jour de la visite : l'agent demande le code au client AVANT la visite
6. L'agent valide le code via l'API → visite DONE

Sécurité :
  • Code demandé AVANT la visite → prouve que le client est présent
  • Si l'agent ne confirme pas → clés restaurées automatiquement
  • Si annulation → clé physique restaurée + clé virtuelle perdue (agent a déjà touché)
"""

import secrets
import string
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


# ── Constantes configurables ─────────────────────────────────
VISIT_RESPONSE_DEADLINE_HOURS = 48
VISIT_CODE_LENGTH = 5
VISIT_CODE_ALPHABET = string.ascii_uppercase + string.digits  # A-Z + 0-9


def _generate_visit_code() -> str:
    """Génère un code alphanumérique majuscule de 5 caractères (ex: A3K7F)."""
    return ''.join(secrets.choice(VISIT_CODE_ALPHABET) for _ in range(VISIT_CODE_LENGTH))


# ═══════════════════════════════════════════════════════════════
# Disponibilités de l'agent
# ═══════════════════════════════════════════════════════════════


class AgentAvailabilitySlot(models.Model):
    """
    Créneau hebdomadaire de disponibilité d'un agent pour les visites.
    L'agent configure ses créneaux une fois, les clients les voient
    et choisissent avant de soumettre la demande.
    """

    class DayOfWeek(models.IntegerChoices):
        LUNDI = 0, 'Lundi'
        MARDI = 1, 'Mardi'
        MERCREDI = 2, 'Mercredi'
        JEUDI = 3, 'Jeudi'
        VENDREDI = 4, 'Vendredi'
        SAMEDI = 5, 'Samedi'
        DIMANCHE = 6, 'Dimanche'

    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='availability_slots',
        limit_choices_to={'role': 'AGENT'},
    )
    day_of_week = models.PositiveSmallIntegerField(
        'Jour de la semaine', choices=DayOfWeek.choices,
    )
    start_time = models.TimeField('Début')
    end_time = models.TimeField('Fin')
    is_active = models.BooleanField('Actif', default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['day_of_week', 'start_time']
        indexes = [
            models.Index(fields=['agent', 'day_of_week', 'is_active'], name='idx_slot_agent_day'),
        ]

    def clean(self):
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError("L'heure de fin doit être après l'heure de début.")

    def __str__(self) -> str:
        day = self.get_day_of_week_display()
        return f"{day} {self.start_time:%H:%M}–{self.end_time:%H:%M}"


class AgentDateSlot(models.Model):
    """
    Créneau ponctuel (date spécifique) de disponibilité d'un agent.
    Complète les créneaux récurrents (AgentAvailabilitySlot) avec
    des dates spécifiques dans un agenda.
    """
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='date_slots',
        limit_choices_to={'role': 'AGENT'},
    )
    date = models.DateField('Date')
    start_time = models.TimeField('Début')
    end_time = models.TimeField('Fin')
    is_active = models.BooleanField('Actif', default=True)
    note = models.CharField('Note', max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date', 'start_time']
        unique_together = ['agent', 'date', 'start_time', 'end_time']
        indexes = [
            models.Index(fields=['agent', 'date', 'is_active'], name='idx_dateslot_agent_date'),
        ]

    def clean(self):
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError("L'heure de fin doit être après l'heure de début.")

    def __str__(self) -> str:
        return f"{self.date} {self.start_time:%H:%M}–{self.end_time:%H:%M}"


# ═══════════════════════════════════════════════════════════════
# Demande de visite
# ═══════════════════════════════════════════════════════════════


class VisitRequest(models.Model):
    """
    Demande de visite physique.
    Consomme 1 clé physique + 1 clé virtuelle (agent touche 10 XOF).
    """

    class Status(models.TextChoices):
        REQUESTED = 'REQUESTED', 'Demandée'
        CONFIRMED = 'CONFIRMED', 'Confirmée par l\'agent'
        DONE = 'DONE', 'Effectuée (code validé)'
        NO_SHOW = 'NO_SHOW', 'Absent'
        CANCELED = 'CANCELED', 'Annulée par le client'
        EXPIRED = 'EXPIRED', 'Expirée (agent n\'a pas répondu)'

    # ── Relations ──────────────────────────────────────────────
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='visit_requests',
        limit_choices_to={'role': 'CLIENT'},
        help_text='Client demandeur',
    )
    listing = models.ForeignKey(
        'listings.Listing',
        on_delete=models.CASCADE,
        related_name='visit_requests',
    )
    pack = models.OneToOneField(
        'packs.PackPurchase',
        on_delete=models.CASCADE,
        related_name='visit_request',
        help_text='Pack dont la clé physique est consommée (1 visite max par pack).',
    )
    slot = models.ForeignKey(
        AgentAvailabilitySlot,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='visit_requests',
        help_text='Créneau choisi par le client.',
    )

    # ── État & planification ──────────────────────────────────
    status = models.CharField(
        'Statut', max_length=16, choices=Status.choices, default=Status.REQUESTED,
    )
    scheduled_at = models.DateTimeField(
        'Date prévue', null=True, blank=True,
        help_text='Date/heure concrète de la visite (calculée à partir du créneau).',
    )
    consumed_physical_key_at = models.DateTimeField(
        'Clé physique consommée le', null=True, blank=True,
    )
    virtual_key_consumed = models.BooleanField(
        'Clé virtuelle consommée', default=False,
        help_text='True si une clé virtuelle a été consommée (client n\'avait pas encore vu la vidéo).',
    )

    # ── Code de vérification ──────────────────────────────────
    verification_code = models.CharField(
        'Code de vérification', max_length=5, default=_generate_visit_code,
        help_text='Code 5 caractères alphanumériques (ex: A3K7F) — '
                  'l\'agent le demande au client AVANT de commencer la visite.',
    )
    code_validated_at = models.DateTimeField(
        'Code validé le', null=True, blank=True,
    )

    # ── Deadline agent ────────────────────────────────────────
    response_deadline = models.DateTimeField(
        'Délai de réponse agent', null=True, blank=True,
        help_text='L\'agent doit confirmer avant cette date, '
                  'sinon la visite expire et les clés sont restaurées.',
    )

    # ── Notes ─────────────────────────────────────────────────
    client_note = models.TextField('Note du client', blank=True)
    agent_note = models.TextField('Note de l\'agent', blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['listing', 'status'], name='idx_visit_listing_status'),
            models.Index(fields=['user', '-created_at'], name='idx_visit_user_date'),
            models.Index(fields=['status', 'response_deadline'], name='idx_visit_deadline'),
        ]

    def __str__(self) -> str:
        return f"Visit<{self.user.phone} → {self.listing.title}> [{self.status}]"

    def save(self, *args, **kwargs):
        if not self.response_deadline and self.status == self.Status.REQUESTED:
            self.response_deadline = timezone.now() + timedelta(
                hours=VISIT_RESPONSE_DEADLINE_HOURS,
            )
        super().save(*args, **kwargs)

    @property
    def is_deadline_passed(self) -> bool:
        if self.response_deadline is None:
            return False
        return timezone.now() > self.response_deadline

    def validate_code(self, code: str) -> bool:
        """Valide le code (insensible à la casse)."""
        return self.verification_code.upper() == code.strip().upper()
