"""
Service de retrait — Monajent
─────────────────────────────
Gère le flux complet du retrait agent :

0. set_withdrawal_pin() / change_withdrawal_pin() — Gestion du PIN
   → Le PIN est hashé (make_password), jamais stocké en clair
   → Requis avant le premier retrait

1. request_withdrawal() — Agent demande un retrait
   → Vérifie le PIN, le seuil (2 000 XOF), pas de demande PENDING existante
   → Déduit le montant du wallet IMMÉDIATEMENT (anti-double-retrait)
   → Crée WalletEntry(DEBIT) + WithdrawalRequest(PENDING)

2. approve_withdrawal() — Admin approuve
   → Exécute le payout via le payment gateway (mobile money)
   → Incrémente total_withdrawn, marque COMPLETED

3. reject_withdrawal() — Admin rejette
   → Restaure le montant au wallet, marque REJECTED
"""

import logging
from decimal import Decimal

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.wallet.models import (
    Wallet, WalletEntry, WithdrawalRequest, MINIMUM_WITHDRAWAL, PIN_LENGTH,
)

logger = logging.getLogger(__name__)


class WithdrawalError(Exception):
    """Erreur métier liée aux retraits."""
    pass


class InsufficientBalanceError(WithdrawalError):
    """Solde insuffisant pour le retrait demandé."""
    pass


class BelowMinimumError(WithdrawalError):
    """Montant en dessous du seuil minimum de retrait."""
    pass


class PendingWithdrawalExistsError(WithdrawalError):
    """L'agent a déjà une demande de retrait en attente."""
    pass


class WithdrawalAlreadyProcessedError(WithdrawalError):
    """Le retrait a déjà été traité."""
    pass


class PinNotSetError(WithdrawalError):
    """L'agent n'a pas encore configuré son code PIN de retrait."""
    pass


class InvalidPinError(WithdrawalError):
    """Code PIN incorrect."""
    pass


class PinAlreadySetError(WithdrawalError):
    """L'agent a déjà configuré son code PIN."""
    pass


# ═══════════════════════════════════════════════════════════════
# 0. Gestion du code PIN
# ═══════════════════════════════════════════════════════════════


def _validate_pin_format(pin: str) -> None:
    """Vérifie que le PIN est composé de exactement N chiffres."""
    if not pin.isdigit() or len(pin) != PIN_LENGTH:
        raise WithdrawalError(
            f"Le code PIN doit contenir exactement {PIN_LENGTH} chiffres."
        )


def set_withdrawal_pin(wallet: Wallet, new_pin: str) -> None:
    """
    Configure le code PIN pour la première fois.
    Bloque si un PIN existe déjà (utiliser change_withdrawal_pin).
    """
    _validate_pin_format(new_pin)

    if wallet.has_pin:
        raise PinAlreadySetError(
            "Un code PIN est déjà configuré. "
            "Utilisez le changement de PIN pour le modifier."
        )

    wallet.set_pin(new_pin)


def change_withdrawal_pin(wallet: Wallet, current_pin: str, new_pin: str) -> None:
    """
    Change le code PIN existant.
    Requiert le PIN actuel pour sécuriser l'opération.
    """
    _validate_pin_format(new_pin)

    if not wallet.has_pin:
        raise PinNotSetError("Aucun code PIN configuré. Configurez-le d'abord.")

    if not wallet.check_pin(current_pin):
        raise InvalidPinError("Code PIN actuel incorrect.")

    wallet.set_pin(new_pin)


# ═══════════════════════════════════════════════════════════════
# 1. Demande de retrait (Agent)
# ═══════════════════════════════════════════════════════════════


def request_withdrawal(
    wallet: Wallet,
    amount: Decimal,
    method: str,
    phone_number: str,
    pin: str,
) -> WithdrawalRequest:
    """
    L'agent demande un retrait.

    Validation :
      • PIN configuré et correct
      • Montant ≥ 2 000 XOF
      • Solde suffisant
      • Pas de demande PENDING existante

    Le montant est déduit du solde IMMÉDIATEMENT pour empêcher
    les doubles retraits (anti-fraude).
    """
    # ── Vérifier le PIN ──────────────────────────────────
    if not wallet.has_pin:
        raise PinNotSetError(
            "Vous devez configurer votre code PIN de retrait "
            "avant de pouvoir effectuer un retrait."
        )

    if not wallet.check_pin(pin):
        raise InvalidPinError("Code PIN de retrait incorrect.")

    if amount < MINIMUM_WITHDRAWAL:
        raise BelowMinimumError(
            f"Le montant minimum de retrait est de {MINIMUM_WITHDRAWAL} XOF. "
            f"Vous avez demandé {amount} XOF."
        )

    with transaction.atomic():
        # Verrouiller le wallet
        wallet_locked = (
            Wallet.objects
            .select_for_update()
            .get(pk=wallet.pk)
        )

        if wallet_locked.balance < amount:
            raise InsufficientBalanceError(
                f"Solde insuffisant. Disponible : {wallet_locked.balance} XOF, "
                f"demandé : {amount} XOF."
            )

        # Vérifier qu'il n'y a pas déjà un retrait PENDING
        if WithdrawalRequest.objects.filter(
            wallet=wallet, status=WithdrawalRequest.Status.PENDING,
        ).exists():
            raise PendingWithdrawalExistsError(
                "Vous avez déjà une demande de retrait en attente. "
                "Attendez qu'elle soit traitée avant d'en soumettre une nouvelle."
            )

        # Déduire le montant du solde (blocage immédiat)
        Wallet.objects.filter(pk=wallet.pk).update(
            balance=F('balance') - amount,
        )

        # Créer l'entrée DEBIT dans le wallet
        entry = WalletEntry.objects.create(
            wallet=wallet,
            entry_type=WalletEntry.EntryType.DEBIT,
            source=WalletEntry.Source.WITHDRAWAL,
            amount=amount,
            label=f"Retrait {method} → {phone_number}",
            withdrawal_method=method,
            withdrawal_ref='',  # Sera rempli par l'admin après transfert
        )

        # Créer la demande de retrait
        withdrawal = WithdrawalRequest.objects.create(
            wallet=wallet,
            amount=amount,
            method=method,
            phone_number=phone_number,
            wallet_entry=entry,
        )

    return withdrawal


# ═══════════════════════════════════════════════════════════════
# 2. Approbation (Admin)
# ═══════════════════════════════════════════════════════════════


def approve_withdrawal(
    withdrawal: WithdrawalRequest,
    admin_user,
    transaction_ref: str = '',
    admin_note: str = '',
) -> WithdrawalRequest:
    """
    L'admin approuve le retrait.
    Exécute le payout via le payment gateway puis met à jour total_withdrawn.
    """
    if withdrawal.status != WithdrawalRequest.Status.PENDING:
        raise WithdrawalAlreadyProcessedError(
            f"Ce retrait est déjà en statut « {withdrawal.get_status_display()} »."
        )

    # Exécuter le payout via le gateway
    from apps.core.services.payment import execute_payout

    payout_result = execute_payout(
        amount=withdrawal.amount,
        currency='XOF',
        phone_number=withdrawal.phone_number,
        method=withdrawal.method,
        description=f"Retrait Monajent #{withdrawal.pk} — {withdrawal.wallet.agent.phone}",
    )

    payout_tx_ref = payout_result.get('provider_tx_id', '')
    final_tx_ref = transaction_ref or payout_tx_ref

    if not payout_result.get('success', False):
        logger.warning(
            "Payout échoué pour withdrawal #%s : %s",
            withdrawal.pk, payout_result.get('message', ''),
        )
        raise WithdrawalError(
            f"Le payout a échoué : {payout_result.get('message', 'Erreur inconnue')}. "
            "Le retrait reste en attente."
        )

    with transaction.atomic():
        withdrawal.status = WithdrawalRequest.Status.COMPLETED
        withdrawal.processed_by = admin_user
        withdrawal.processed_at = timezone.now()
        withdrawal.transaction_ref = final_tx_ref
        withdrawal.admin_note = admin_note
        withdrawal.save(update_fields=[
            'status', 'processed_by', 'processed_at',
            'transaction_ref', 'admin_note', 'updated_at',
        ])

        if withdrawal.wallet_entry and final_tx_ref:
            withdrawal.wallet_entry.withdrawal_ref = final_tx_ref
            withdrawal.wallet_entry.save(update_fields=['withdrawal_ref'])

        Wallet.objects.filter(pk=withdrawal.wallet_id).update(
            total_withdrawn=F('total_withdrawn') + withdrawal.amount,
        )

    logger.info(
        "Withdrawal #%s approuvé : %s XOF → %s (%s) ref=%s",
        withdrawal.pk, withdrawal.amount,
        withdrawal.phone_number, withdrawal.method, final_tx_ref,
    )

    return withdrawal


# ═══════════════════════════════════════════════════════════════
# 3. Rejet (Admin)
# ═══════════════════════════════════════════════════════════════


def reject_withdrawal(
    withdrawal: WithdrawalRequest,
    admin_user,
    admin_note: str = '',
) -> WithdrawalRequest:
    """
    L'admin rejette le retrait. Le montant est restauré au wallet.
    """
    if withdrawal.status != WithdrawalRequest.Status.PENDING:
        raise WithdrawalAlreadyProcessedError(
            f"Ce retrait est déjà en statut « {withdrawal.get_status_display()} »."
        )

    with transaction.atomic():
        withdrawal.status = WithdrawalRequest.Status.REJECTED
        withdrawal.processed_by = admin_user
        withdrawal.processed_at = timezone.now()
        withdrawal.admin_note = admin_note
        withdrawal.save(update_fields=[
            'status', 'processed_by', 'processed_at',
            'admin_note', 'updated_at',
        ])

        # Restaurer le montant au wallet
        Wallet.objects.filter(pk=withdrawal.wallet_id).update(
            balance=F('balance') + withdrawal.amount,
        )

        # Marquer l'entrée DEBIT comme annulée
        if withdrawal.wallet_entry:
            withdrawal.wallet_entry.label += ' [REJETÉ — montant restauré]'
            withdrawal.wallet_entry.save(update_fields=['label'])

    return withdrawal
