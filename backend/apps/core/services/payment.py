"""
Service Payment — Monajent
──────────────────────────
Orchestration du paiement pour l'achat de packs.

Flux pay-in :
  1. initiate_pack_purchase()  → Payment(PENDING) + checkout_url
  2. process_webhook()         → Payment(PAID) + PackPurchase créé

Flux payout (retrait agent) :
  → execute_payout()  — appelé par approve_withdrawal()
"""

from __future__ import annotations

import logging
import uuid
from decimal import Decimal

from django.conf import settings
from django.db import transaction

from apps.payments.models import Payment
from apps.packs.models import PackPurchase, PACK_PRICE

from .payment_gateway import get_payment_gateway

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# Exceptions
# ═══════════════════════════════════════════════════════════════

class PaymentError(Exception):
    """Erreur métier liée aux paiements."""


class PaymentAlreadyProcessedError(PaymentError):
    """Le paiement a déjà été traité."""


class PaymentNotFoundError(PaymentError):
    """Paiement introuvable pour cette référence."""


class InvalidWebhookError(PaymentError):
    """Données webhook invalides ou signature rejetée."""


# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════

def _generate_tx_ref() -> str:
    """Génère une référence de transaction unique."""
    return f"MNAJ-{uuid.uuid4().hex[:16].upper()}"


def _build_notify_url() -> str:
    """URL du webhook pour le provider."""
    base = getattr(settings, 'PAYMENT_WEBHOOK_BASE_URL', 'http://localhost:8000')
    return f"{base}/api/payments/webhook/"


# ═══════════════════════════════════════════════════════════════
# 1. Initiation du paiement (Client)
# ═══════════════════════════════════════════════════════════════

def initiate_pack_purchase(
    user,
    provider: str,
    return_url: str = '',
) -> dict:
    """
    Le client demande à acheter un pack.
    Crée un Payment(PENDING) et retourne le checkout_url du provider.

    Returns :
        {
            'payment': Payment,
            'checkout_url': str,
        }
    """
    tx_ref = _generate_tx_ref()
    amount = PACK_PRICE
    currency = 'XOF'

    gateway = get_payment_gateway()

    customer_name = user.username or user.phone
    customer_phone = user.phone
    customer_email = user.email or f"{user.phone.replace('+', '')}@monajent.app"

    if not return_url:
        return_url = getattr(settings, 'PAYMENT_DEFAULT_RETURN_URL', 'http://localhost:5173/home/packs')

    notify_url = _build_notify_url()

    checkout_result = gateway.create_checkout(
        tx_ref=tx_ref,
        amount=amount,
        currency=currency,
        description=f"Pack Monajent — 33 clés virtuelles + 1 clé physique",
        customer_name=customer_name,
        customer_phone=customer_phone,
        return_url=return_url,
        notify_url=notify_url,
        metadata={'customer_email': customer_email},
    )

    payment = Payment.objects.create(
        user=user,
        provider=provider,
        tx_ref=tx_ref,
        provider_tx_id=checkout_result.provider_tx_id,
        amount=amount,
        currency=currency,
        checkout_url=checkout_result.checkout_url,
        status=Payment.Status.PENDING,
        provider_metadata=checkout_result.raw,
    )

    logger.info(
        "Payment initié : id=%s tx_ref=%s provider=%s amount=%s %s",
        payment.pk, tx_ref, provider, amount, currency,
    )

    return {
        'payment': payment,
        'checkout_url': checkout_result.checkout_url,
    }


# ═══════════════════════════════════════════════════════════════
# 2. Traitement du webhook (Provider → Backend)
# ═══════════════════════════════════════════════════════════════

def process_webhook(payload: dict, headers: dict, raw_body: bytes = b'') -> Payment:
    """
    Traite la notification du provider après paiement.

    1. Vérifie le webhook via le gateway
    2. Retrouve le Payment par tx_ref
    3. Si PAID → crée le PackPurchase et lie au Payment
    4. Si FAILED → marque le Payment comme échoué
    """
    gateway = get_payment_gateway()

    webhook_result = gateway.verify_webhook(
        payload=payload,
        headers=headers,
        raw_body=raw_body,
    )

    tx_ref = webhook_result.tx_ref
    if not tx_ref:
        raise InvalidWebhookError("tx_ref manquant dans le webhook.")

    try:
        payment = Payment.objects.get(tx_ref=tx_ref)
    except Payment.DoesNotExist:
        raise PaymentNotFoundError(f"Aucun paiement trouvé pour tx_ref={tx_ref}")

    if payment.status != Payment.Status.PENDING:
        logger.warning(
            "Webhook reçu pour payment déjà traité : id=%s status=%s",
            payment.pk, payment.status,
        )
        raise PaymentAlreadyProcessedError(
            f"Payment {tx_ref} déjà en statut {payment.status}."
        )

    with transaction.atomic():
        payment = Payment.objects.select_for_update().get(pk=payment.pk)

        if payment.status != Payment.Status.PENDING:
            raise PaymentAlreadyProcessedError(
                f"Payment {tx_ref} déjà traité (race condition évitée)."
            )

        payment.provider_tx_id = webhook_result.provider_tx_id or payment.provider_tx_id
        payment.provider_metadata = webhook_result.raw

        if webhook_result.status == 'PAID':
            pack = PackPurchase.objects.create(user=payment.user)
            payment.pack = pack
            payment.status = Payment.Status.PAID
            payment.save(update_fields=[
                'pack', 'status', 'provider_tx_id',
                'provider_metadata', 'updated_at',
            ])

            logger.info(
                "Payment PAID : id=%s tx_ref=%s → PackPurchase id=%s créé",
                payment.pk, tx_ref, pack.pk,
            )

        else:
            payment.status = Payment.Status.FAILED
            payment.save(update_fields=[
                'status', 'provider_tx_id',
                'provider_metadata', 'updated_at',
            ])

            logger.info(
                "Payment FAILED : id=%s tx_ref=%s",
                payment.pk, tx_ref,
            )

    return payment


# ═══════════════════════════════════════════════════════════════
# 3. Vérification directe (callback retour client)
# ═══════════════════════════════════════════════════════════════

def verify_and_process(tx_ref: str) -> Payment:
    """
    Vérifie le statut d'une transaction auprès du provider et traite le résultat.
    Utilisé quand le client revient du checkout (callback_url).
    Complément au webhook pour garantir le traitement.
    """
    gateway = get_payment_gateway()

    result = gateway.verify_transaction(tx_ref=tx_ref)

    try:
        payment = Payment.objects.get(tx_ref=tx_ref)
    except Payment.DoesNotExist:
        raise PaymentNotFoundError(f"Aucun paiement trouvé pour tx_ref={tx_ref}")

    if payment.status != Payment.Status.PENDING:
        return payment

    with transaction.atomic():
        payment = Payment.objects.select_for_update().get(pk=payment.pk)

        if payment.status != Payment.Status.PENDING:
            return payment

        payment.provider_tx_id = result.provider_tx_id or payment.provider_tx_id
        payment.provider_metadata = result.raw

        if result.status == 'PAID':
            pack = PackPurchase.objects.create(user=payment.user)
            payment.pack = pack
            payment.status = Payment.Status.PAID
            payment.save(update_fields=[
                'pack', 'status', 'provider_tx_id',
                'provider_metadata', 'updated_at',
            ])
            logger.info(
                "Payment vérifié PAID : id=%s tx_ref=%s → PackPurchase id=%s",
                payment.pk, tx_ref, pack.pk,
            )
        elif result.status == 'FAILED':
            payment.status = Payment.Status.FAILED
            payment.save(update_fields=[
                'status', 'provider_tx_id',
                'provider_metadata', 'updated_at',
            ])
            logger.info("Payment vérifié FAILED : id=%s tx_ref=%s", payment.pk, tx_ref)
        else:
            logger.info(
                "Payment toujours PENDING : id=%s tx_ref=%s (provider status=%s)",
                payment.pk, tx_ref, result.status,
            )

    return payment


# ═══════════════════════════════════════════════════════════════
# 4. Payout (retrait agent → mobile money)
# ═══════════════════════════════════════════════════════════════

def execute_payout(
    *,
    amount: Decimal,
    currency: str,
    phone_number: str,
    method: str,
    description: str = '',
) -> dict:
    """
    Exécute un payout via le gateway configuré.
    Appelé par approve_withdrawal() dans le service withdrawal.

    Returns :
        {
            'success': bool,
            'provider_tx_id': str,
            'message': str,
        }
    """
    gateway = get_payment_gateway()

    result = gateway.create_payout(
        amount=amount,
        currency=currency,
        phone_number=phone_number,
        method=method,
        description=description or f"Retrait Monajent {amount} {currency}",
    )

    logger.info(
        "Payout exécuté : success=%s tx_id=%s amount=%s %s → %s (%s)",
        result.success, result.provider_tx_id,
        amount, currency, phone_number, method,
    )

    return {
        'success': result.success,
        'provider_tx_id': result.provider_tx_id,
        'message': result.message,
    }
