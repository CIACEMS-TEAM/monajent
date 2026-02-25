"""
Service de visite physique — Monajent (v3)
──────────────────────────────────────────
Modèle de revenus :
  • Pack = 33 clés virtuelles (15 XOF/clé) + 1 clé physique (GRATUITE)
  • L'agent touche 10 XOF UNE SEULE FOIS par client par annonce
  • La plateforme touche 5 XOF par interaction

Flux visite physique :
  1. Le client choisit un créneau parmi les disponibilités de l'agent
  2. Soumet la demande → transaction atomique :
     a. Vérifie si le client a DÉJÀ vu la vidéo de cette annonce
     b. SI OUI  → consomme SEULEMENT la clé physique (agent déjà payé)
     c. SI NON  → consomme clé physique + 1 clé virtuelle
                  + crédite agent 10 XOF + plateforme 5 XOF
                  + crée VirtualKeyUsage (pour que la vidéo soit « déjà vue »)
  3. L'agent confirme (ou expiration → clé physique restaurée)
  4. Jour J : agent demande le code au client AVANT la visite
  5. Agent valide le code → DONE

Annulation / Expiration :
  • Clé physique → TOUJOURS restaurée
  • Clé virtuelle → JAMAIS restaurée (l'interaction a eu lieu, agent payé)
"""

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.visits.models import VisitRequest, AgentAvailabilitySlot
from apps.packs.models import (
    PackPurchase, VirtualKeyUsage,
    AGENT_REVENUE_PER_VIEW, PLATFORM_REVENUE_PER_VIEW,
)
from apps.wallet.models import Wallet, WalletEntry, PlatformRevenue
from apps.listings.models import Listing


class VisitError(Exception):
    """Erreur métier liée aux visites."""
    pass


class NoPhysicalKeyError(VisitError):
    """Aucun pack avec clé physique disponible."""
    pass


class InvalidVisitCodeError(VisitError):
    """Le code de vérification est incorrect."""
    pass


class VisitNotConfirmedError(VisitError):
    """La visite n'est pas dans un état permettant la validation du code."""
    pass


class NoAvailableSlotsError(VisitError):
    """L'agent n'a aucun créneau de disponibilité configuré."""
    pass


# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════


def _has_interacted_with_listing(user, listing: Listing) -> bool:
    """
    Vérifie si le client a déjà consommé une clé virtuelle
    pour N'IMPORTE QUELLE vidéo de cette annonce.
    Si oui → l'agent a déjà été payé pour ce client/annonce.
    """
    return VirtualKeyUsage.objects.filter(
        user=user,
        video__listing=listing,
    ).exists()


def _find_pack_with_physical_key(user, need_virtual_key: bool) -> PackPurchase:
    """
    Trouve un pack FIFO avec clé physique disponible.
    Si need_virtual_key=True, le pack doit aussi avoir ≥1 clé virtuelle.
    """
    qs = (
        PackPurchase.objects
        .select_for_update()
        .filter(
            user=user,
            has_physical_key=True,
            is_locked_by_visit=False,
        )
    )
    if need_virtual_key:
        qs = qs.extra(where=["virtual_total - virtual_used > 0"])

    pack = qs.order_by('created_at').first()

    if pack is None:
        if need_virtual_key:
            raise NoPhysicalKeyError(
                "Aucun pack avec clé physique et clé virtuelle disponible. "
                "Achetez un nouveau pack."
            )
        raise NoPhysicalKeyError(
            "Aucun pack avec clé physique disponible. "
            "Achetez un nouveau pack."
        )
    return pack


# ═══════════════════════════════════════════════════════════════
# 1. Demande de visite (Client)
# ═══════════════════════════════════════════════════════════════


def request_visit(
    user,
    listing: Listing,
    slot: AgentAvailabilitySlot | None = None,
    scheduled_at=None,
    client_note: str = '',
) -> dict:
    """
    Le client demande une visite physique.

    Returns:
        dict avec :
          - visit: VisitRequest créée
          - virtual_key_consumed: bool
          - already_interacted: bool
    """
    agent = listing.agent
    already_interacted = _has_interacted_with_listing(user, listing)
    need_virtual_key = not already_interacted

    with transaction.atomic():
        pack = _find_pack_with_physical_key(user, need_virtual_key=need_virtual_key)

        # ── Consommer la clé physique (toujours) ─────────
        update_kwargs = dict(
            has_physical_key=False,
            is_locked_by_visit=True,
        )
        if need_virtual_key:
            update_kwargs['virtual_used'] = F('virtual_used') + 1

        PackPurchase.objects.filter(pk=pack.pk).update(**update_kwargs)

        # ── Créer la visite ──────────────────────────────
        visit = VisitRequest.objects.create(
            user=user,
            listing=listing,
            pack=pack,
            slot=slot,
            scheduled_at=scheduled_at,
            client_note=client_note,
            consumed_physical_key_at=timezone.now(),
            virtual_key_consumed=need_virtual_key,
        )

        if need_virtual_key:
            # ── Créer VirtualKeyUsage pour la vidéo principale ─
            # Marque le client comme ayant « interagi » avec cette annonce.
            # Ainsi, s'il regarde la vidéo plus tard → c'est gratuit.
            primary_video = listing.videos.order_by('pk').first()
            if primary_video:
                VirtualKeyUsage.objects.create(
                    pack=pack,
                    video=primary_video,
                    user=user,
                    agent=agent,
                    amount_agent=AGENT_REVENUE_PER_VIEW,
                    amount_platform=PLATFORM_REVENUE_PER_VIEW,
                )

            # ── Créditer l'agent (10 XOF) ───────────────
            wallet, _ = Wallet.objects.get_or_create(agent=agent)
            Wallet.objects.filter(pk=wallet.pk).update(
                balance=F('balance') + AGENT_REVENUE_PER_VIEW,
                total_earned=F('total_earned') + AGENT_REVENUE_PER_VIEW,
            )
            WalletEntry.objects.create(
                wallet=wallet,
                entry_type=WalletEntry.EntryType.CREDIT,
                source=WalletEntry.Source.PHYSICAL_VISIT,
                amount=AGENT_REVENUE_PER_VIEW,
                label=f"Visite physique — {listing.title}",
                ref_visit=visit,
            )

            # ── Revenu plateforme (5 XOF) ───────────────
            PlatformRevenue.objects.create(
                source=PlatformRevenue.Source.PHYSICAL_VISIT,
                visit=visit,
                amount=PLATFORM_REVENUE_PER_VIEW,
            )

    return {
        'visit': visit,
        'virtual_key_consumed': need_virtual_key,
        'already_interacted': already_interacted,
    }


# ═══════════════════════════════════════════════════════════════
# 2. Confirmation (Agent)
# ═══════════════════════════════════════════════════════════════


def confirm_visit(visit: VisitRequest, scheduled_at=None, agent_note: str = '') -> VisitRequest:
    """L'agent confirme la visite (peut ajuster la date)."""
    if visit.status != VisitRequest.Status.REQUESTED:
        raise VisitError(
            f"Impossible de confirmer : statut « {visit.get_status_display()} »."
        )

    visit.status = VisitRequest.Status.CONFIRMED
    if scheduled_at:
        visit.scheduled_at = scheduled_at
    visit.agent_note = agent_note
    visit.save(update_fields=['status', 'scheduled_at', 'agent_note', 'updated_at'])
    return visit


# ═══════════════════════════════════════════════════════════════
# 3. Validation du code (Agent — AVANT la visite)
# ═══════════════════════════════════════════════════════════════


def validate_visit_code(visit: VisitRequest, code: str) -> VisitRequest:
    """
    L'agent entre le code communiqué par le client.
    Doit être fait AVANT de commencer la visite (preuve de présence).
    """
    if visit.status != VisitRequest.Status.CONFIRMED:
        raise VisitNotConfirmedError(
            "La visite doit être confirmée avant de valider le code."
        )

    if not visit.validate_code(code):
        raise InvalidVisitCodeError("Code de vérification incorrect.")

    visit.status = VisitRequest.Status.DONE
    visit.code_validated_at = timezone.now()
    visit.save(update_fields=['status', 'code_validated_at', 'updated_at'])
    return visit


# ═══════════════════════════════════════════════════════════════
# 4. NO_SHOW (Agent — le client ne se présente pas)
# ═══════════════════════════════════════════════════════════════


def mark_no_show(visit: VisitRequest) -> VisitRequest:
    """
    L'agent marque le client comme absent.
    Uniquement si la visite est CONFIRMED (rendez-vous prévu mais client absent).
    La clé physique N'EST PAS restaurée (le créneau a été bloqué).
    """
    if visit.status != VisitRequest.Status.CONFIRMED:
        raise VisitError(
            f"Impossible de marquer absent : statut « {visit.get_status_display()} ». "
            "Seules les visites confirmées peuvent être marquées NO_SHOW."
        )

    visit.status = VisitRequest.Status.NO_SHOW
    visit.save(update_fields=['status', 'updated_at'])
    return visit


# ═══════════════════════════════════════════════════════════════
# 5. Annulation (Client)
# ═══════════════════════════════════════════════════════════════


def cancel_visit(visit: VisitRequest) -> None:
    """
    Le client annule sa demande.
    Clé physique → restaurée.
    Clé virtuelle → NON restaurée (agent a déjà touché, interaction a eu lieu).
    VisitRequest supprimée pour libérer le OneToOneField du pack.
    """
    if visit.status in (VisitRequest.Status.DONE, VisitRequest.Status.CANCELED,
                        VisitRequest.Status.EXPIRED):
        raise VisitError(
            f"Impossible d'annuler : statut « {visit.get_status_display()} »."
        )

    with transaction.atomic():
        pack = visit.pack
        visit.delete()
        _restore_physical_key(pack)


# ═══════════════════════════════════════════════════════════════
# 5. Expiration automatique (Tâche périodique)
# ═══════════════════════════════════════════════════════════════


def expire_unresponded_visits() -> int:
    """
    Expire les visites REQUESTED dont le deadline est passé.
    Restaure la clé physique (la clé virtuelle reste consommée).
    """
    now = timezone.now()
    expired_visits = (
        VisitRequest.objects
        .filter(
            status=VisitRequest.Status.REQUESTED,
            response_deadline__lt=now,
        )
        .select_related('pack')
    )

    count = 0
    for visit in expired_visits:
        with transaction.atomic():
            pack = visit.pack
            visit.delete()
            _restore_physical_key(pack)
            count += 1

    return count


# ═══════════════════════════════════════════════════════════════
# Utilitaire interne
# ═══════════════════════════════════════════════════════════════


def _restore_physical_key(pack: PackPurchase):
    """Restaure la clé physique et déverrouille le pack."""
    PackPurchase.objects.filter(pk=pack.pk).update(
        has_physical_key=True,
        is_locked_by_visit=False,
    )
