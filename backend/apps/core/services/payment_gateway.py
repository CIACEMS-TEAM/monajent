"""
Payment Gateway — Monajent
──────────────────────────
Interface abstraite pour l'intégration de providers de paiement.
Chaque provider (Paystack, CinetPay, Moneroo, Flutterwave…) implémente
BasePaymentGateway. Le code métier ne manipule que l'interface.

Architecture :
  BasePaymentGateway (ABC)
      ├── SimulationGateway    — dev / tests (aucun appel externe)
      ├── PaystackGateway      — Paystack (CI : Orange, MTN, Wave, Card)
      ├── CinetPayGateway      — placeholder prêt à compléter
      ├── MonerooGateway       — placeholder prêt à compléter
      └── FlutterwaveGateway   — placeholder prêt à compléter
"""

from __future__ import annotations

import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from django.conf import settings

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# Résultats standardisés
# ═══════════════════════════════════════════════════════════════

@dataclass
class CheckoutResult:
    """Résultat de la création d'un checkout."""
    checkout_url: str
    provider_tx_id: str
    raw: dict


@dataclass
class WebhookResult:
    """Résultat du parsing / vérification d'un webhook."""
    tx_ref: str
    provider_tx_id: str
    status: str            # 'PAID' | 'FAILED'
    amount: Decimal
    currency: str
    raw: dict


@dataclass
class PayoutResult:
    """Résultat d'un payout (retrait agent)."""
    success: bool
    provider_tx_id: str
    message: str
    raw: dict


# ═══════════════════════════════════════════════════════════════
# Interface abstraite
# ═══════════════════════════════════════════════════════════════

class BasePaymentGateway(ABC):
    """Interface commune à tous les providers de paiement."""

    @abstractmethod
    def create_checkout(
        self,
        *,
        tx_ref: str,
        amount: Decimal,
        currency: str,
        description: str,
        customer_name: str,
        customer_phone: str,
        return_url: str,
        notify_url: str,
        metadata: dict | None = None,
    ) -> CheckoutResult:
        """
        Initialise un paiement et retourne l'URL de checkout du provider.
        """

    @abstractmethod
    def verify_webhook(
        self,
        *,
        payload: dict,
        headers: dict,
        raw_body: bytes = b'',
    ) -> WebhookResult:
        """
        Valide et parse le webhook entrant du provider.
        Lève une exception si la signature est invalide.
        raw_body est nécessaire pour la vérification HMAC (Paystack).
        """

    def verify_transaction(self, *, tx_ref: str) -> WebhookResult:
        """
        Vérifie le statut d'une transaction auprès du provider.
        Utile pour le callback (retour client) sans attendre le webhook.
        Implémentation par défaut : raise NotImplementedError.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__}.verify_transaction() non implémenté."
        )

    @abstractmethod
    def create_payout(
        self,
        *,
        amount: Decimal,
        currency: str,
        phone_number: str,
        method: str,
        description: str,
    ) -> PayoutResult:
        """
        Envoie un paiement vers un numéro mobile money (retrait agent).
        """


# ═══════════════════════════════════════════════════════════════
# Simulation Gateway (dev / tests)
# ═══════════════════════════════════════════════════════════════

class SimulationGateway(BasePaymentGateway):
    """
    Gateway de simulation pour le développement.
    Aucun appel réseau, tout est local.
    Le checkout_url pointe vers un endpoint local de confirmation.
    """

    def create_checkout(
        self,
        *,
        tx_ref: str,
        amount: Decimal,
        currency: str,
        description: str,
        customer_name: str,
        customer_phone: str,
        return_url: str,
        notify_url: str,
        metadata: dict | None = None,
    ) -> CheckoutResult:
        sim_tx_id = f"SIM-{uuid.uuid4().hex[:12].upper()}"
        base_url = getattr(settings, 'PAYMENT_SIMULATION_BASE_URL', 'http://localhost:8000')
        checkout_url = f"{base_url}/api/payments/simulate/{tx_ref}/confirm/"

        logger.info(
            "[SimulationGateway] Checkout créé : tx_ref=%s amount=%s %s → %s",
            tx_ref, amount, currency, checkout_url,
        )

        return CheckoutResult(
            checkout_url=checkout_url,
            provider_tx_id=sim_tx_id,
            raw={
                'simulation': True,
                'tx_ref': tx_ref,
                'amount': str(amount),
                'currency': currency,
            },
        )

    def verify_webhook(
        self,
        *,
        payload: dict,
        headers: dict,
        raw_body: bytes = b'',
    ) -> WebhookResult:
        return WebhookResult(
            tx_ref=payload.get('tx_ref', ''),
            provider_tx_id=payload.get('provider_tx_id', ''),
            status='PAID',
            amount=Decimal(str(payload.get('amount', '0'))),
            currency=payload.get('currency', 'XOF'),
            raw=payload,
        )

    def create_payout(
        self,
        *,
        amount: Decimal,
        currency: str,
        phone_number: str,
        method: str,
        description: str,
    ) -> PayoutResult:
        sim_tx_id = f"SIM-PAYOUT-{uuid.uuid4().hex[:12].upper()}"

        logger.info(
            "[SimulationGateway] Payout simulé : %s %s → %s (%s) ref=%s",
            amount, currency, phone_number, method, sim_tx_id,
        )

        return PayoutResult(
            success=True,
            provider_tx_id=sim_tx_id,
            message=f"Payout simulé de {amount} {currency} vers {phone_number}",
            raw={
                'simulation': True,
                'amount': str(amount),
                'currency': currency,
                'phone_number': phone_number,
                'method': method,
            },
        )


# ═══════════════════════════════════════════════════════════════
# CinetPay Gateway (placeholder)
# ═══════════════════════════════════════════════════════════════

class CinetPayGateway(BasePaymentGateway):
    """
    Intégration CinetPay — à compléter avec les clés API.
    Doc : https://docs.cinetpay.com/api/1.0-en/checkout/overview
    """

    def __init__(self) -> None:
        config = getattr(settings, 'PAYMENT_CONFIG', {}).get('cinetpay', {})
        self.api_key = config.get('api_key', '')
        self.site_id = config.get('site_id', '')
        self.secret_key = config.get('secret_key', '')

        if not self.api_key or not self.site_id:
            raise RuntimeError(
                "CinetPayGateway requiert CINETPAY_API_KEY et CINETPAY_SITE_ID "
                "dans PAYMENT_CONFIG['cinetpay']."
            )

    def create_checkout(self, **kwargs: Any) -> CheckoutResult:
        raise NotImplementedError(
            "CinetPayGateway.create_checkout() : à implémenter avec l'API CinetPay. "
            "Voir https://docs.cinetpay.com/api/1.0-en/checkout/overview"
        )

    def verify_webhook(self, **kwargs: Any) -> WebhookResult:
        raise NotImplementedError(
            "CinetPayGateway.verify_webhook() : à implémenter."
        )

    def create_payout(self, **kwargs: Any) -> PayoutResult:
        raise NotImplementedError(
            "CinetPayGateway.create_payout() : à implémenter. "
            "Voir https://docs.cinetpay.com/api/1.0-en/transfert/utilisation"
        )


# ═══════════════════════════════════════════════════════════════
# Moneroo Gateway (placeholder)
# ═══════════════════════════════════════════════════════════════

class MonerooGateway(BasePaymentGateway):
    """
    Intégration Moneroo — à compléter avec les clés API.
    Doc : https://docs.moneroo.io/
    """

    def __init__(self) -> None:
        config = getattr(settings, 'PAYMENT_CONFIG', {}).get('moneroo', {})
        self.secret_key = config.get('secret_key', '')

        if not self.secret_key:
            raise RuntimeError(
                "MonerooGateway requiert MONEROO_SECRET_KEY "
                "dans PAYMENT_CONFIG['moneroo']."
            )

    def create_checkout(self, **kwargs: Any) -> CheckoutResult:
        raise NotImplementedError(
            "MonerooGateway.create_checkout() : à implémenter avec l'API Moneroo. "
            "Voir https://docs.moneroo.io/payments/initialize-payment"
        )

    def verify_webhook(self, **kwargs: Any) -> WebhookResult:
        raise NotImplementedError(
            "MonerooGateway.verify_webhook() : à implémenter."
        )

    def create_payout(self, **kwargs: Any) -> PayoutResult:
        raise NotImplementedError(
            "MonerooGateway.create_payout() : à implémenter. "
            "Voir https://docs.moneroo.io/payouts/initialize-payout"
        )


# ═══════════════════════════════════════════════════════════════
# Flutterwave Gateway (placeholder)
# ═══════════════════════════════════════════════════════════════

class FlutterwaveGateway(BasePaymentGateway):
    """
    Intégration Flutterwave — à compléter avec les clés API.
    Doc : https://developer.flutterwave.com/
    """

    def __init__(self) -> None:
        config = getattr(settings, 'PAYMENT_CONFIG', {}).get('flutterwave', {})
        self.secret_key = config.get('secret_key', '')
        self.public_key = config.get('public_key', '')

        if not self.secret_key:
            raise RuntimeError(
                "FlutterwaveGateway requiert FLW_SECRET_KEY "
                "dans PAYMENT_CONFIG['flutterwave']."
            )

    def create_checkout(self, **kwargs: Any) -> CheckoutResult:
        raise NotImplementedError(
            "FlutterwaveGateway.create_checkout() : à implémenter. "
            "Voir https://developer.flutterwave.com/docs/mobile-money"
        )

    def verify_webhook(self, **kwargs: Any) -> WebhookResult:
        raise NotImplementedError(
            "FlutterwaveGateway.verify_webhook() : à implémenter."
        )

    def create_payout(self, **kwargs: Any) -> PayoutResult:
        raise NotImplementedError(
            "FlutterwaveGateway.create_payout() : à implémenter. "
            "Voir https://developer.flutterwave.com/v3.0/docs/c%C3%B4te-divoire"
        )


# ═══════════════════════════════════════════════════════════════
# Paystack Gateway (CI : Orange Money, MTN, Wave, Visa, MC)
# ═══════════════════════════════════════════════════════════════

class PaystackGateway(BasePaymentGateway):
    """
    Intégration Paystack — Côte d'Ivoire.
    Supporte : Orange Money, MTN MoMo, Wave, Visa, Mastercard.
    Doc : https://docs-v2.paystack.com/api/transaction/
    """

    BASE_URL = 'https://api.paystack.co'

    def __init__(self) -> None:
        config = getattr(settings, 'PAYMENT_CONFIG', {}).get('paystack', {})
        self.secret_key = config.get('secret_key', '')
        self.public_key = config.get('public_key', '')

        if not self.secret_key:
            raise RuntimeError(
                "PaystackGateway requiert PAYSTACK_SECRET_KEY "
                "dans PAYMENT_CONFIG['paystack']."
            )

    def _headers(self) -> dict:
        return {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/json',
        }

    def create_checkout(
        self,
        *,
        tx_ref: str,
        amount: Decimal,
        currency: str,
        description: str,
        customer_name: str,
        customer_phone: str,
        return_url: str,
        notify_url: str,
        metadata: dict | None = None,
    ) -> CheckoutResult:
        import requests

        amount_subunit = int(amount * 100)

        customer_email = (metadata or {}).pop('customer_email', None) or \
            f"{customer_phone.replace('+', '')}@monajent.app"

        payload = {
            'email': customer_email,
            'amount': str(amount_subunit),
            'currency': currency,
            'reference': tx_ref,
            'callback_url': return_url,
            'channels': ['card', 'mobile_money'],
            'metadata': {
                'custom_fields': [
                    {'display_name': 'Client', 'variable_name': 'customer_name', 'value': customer_name},
                    {'display_name': 'Téléphone', 'variable_name': 'customer_phone', 'value': customer_phone},
                    {'display_name': 'Description', 'variable_name': 'description', 'value': description},
                ],
                **(metadata or {}),
            },
        }

        logger.info("[Paystack] Initializing checkout: ref=%s amount=%s %s", tx_ref, amount, currency)

        resp = requests.post(
            f'{self.BASE_URL}/transaction/initialize',
            json=payload,
            headers=self._headers(),
            timeout=30,
        )

        body = resp.json()

        if resp.status_code != 200 or not body.get('status'):
            msg = body.get('message', resp.text)
            logger.error("[Paystack] Checkout failed: %s", msg)
            raise RuntimeError(f"Paystack checkout échoué : {msg}")

        data = body['data']

        logger.info(
            "[Paystack] Checkout créé : ref=%s → %s",
            tx_ref, data['authorization_url'],
        )

        return CheckoutResult(
            checkout_url=data['authorization_url'],
            provider_tx_id=data.get('access_code', ''),
            raw=body,
        )

    def verify_webhook(
        self,
        *,
        payload: dict,
        headers: dict,
        raw_body: bytes = b'',
    ) -> WebhookResult:
        import hashlib
        import hmac

        signature = headers.get(
            'x-paystack-signature',
            headers.get('X-Paystack-Signature', ''),
        )

        if not raw_body or not signature:
            raise ValueError(
                "Webhook Paystack rejeté : signature ou body absent."
            )

        expected = hmac.HMAC(
            self.secret_key.encode('utf-8'),
            raw_body,
            hashlib.sha512,
        ).hexdigest()

        if not hmac.compare_digest(expected, signature):
            raise ValueError("Signature Paystack invalide.")

        event = payload.get('event', '')
        data = payload.get('data', {})

        if event == 'charge.success' and data.get('status') == 'success':
            ps_status = 'PAID'
        else:
            ps_status = 'FAILED'

        raw_amount = Decimal(str(data.get('amount', 0)))
        base_amount = raw_amount / 100

        return WebhookResult(
            tx_ref=data.get('reference', ''),
            provider_tx_id=str(data.get('id', '')),
            status=ps_status,
            amount=base_amount,
            currency=data.get('currency', 'XOF'),
            raw=payload,
        )

    def verify_transaction(self, *, tx_ref: str) -> WebhookResult:
        """Vérifie le statut d'une transaction via l'API Paystack."""
        import requests

        logger.info("[Paystack] Verifying transaction: ref=%s", tx_ref)

        resp = requests.get(
            f'{self.BASE_URL}/transaction/verify/{tx_ref}',
            headers=self._headers(),
            timeout=30,
        )

        body = resp.json()

        if resp.status_code != 200 or not body.get('status'):
            msg = body.get('message', resp.text)
            logger.error("[Paystack] Verification failed: %s", msg)
            raise RuntimeError(f"Paystack vérification échouée : {msg}")

        data = body['data']

        if data.get('status') == 'success':
            ps_status = 'PAID'
        elif data.get('status') in ('failed', 'reversed'):
            ps_status = 'FAILED'
        else:
            ps_status = 'PENDING'

        raw_amount = Decimal(str(data.get('amount', 0)))

        return WebhookResult(
            tx_ref=data.get('reference', tx_ref),
            provider_tx_id=str(data.get('id', '')),
            status=ps_status,
            amount=raw_amount / 100,
            currency=data.get('currency', 'XOF'),
            raw=body,
        )

    def create_payout(
        self,
        *,
        amount: Decimal,
        currency: str,
        phone_number: str,
        method: str,
        description: str,
    ) -> PayoutResult:
        """
        Payout via Paystack Transfers.
        TODO: implémenter avec create_transfer_recipient + initiate_transfer.
        """
        raise NotImplementedError(
            "PaystackGateway.create_payout() : à implémenter avec l'API Paystack Transfers. "
            "Voir https://docs-v2.paystack.com/api/transfer/"
        )


# ═══════════════════════════════════════════════════════════════
# Factory
# ═══════════════════════════════════════════════════════════════

_GATEWAY_MAP: dict[str, type[BasePaymentGateway]] = {
    'simulation': SimulationGateway,
    'paystack': PaystackGateway,
    'cinetpay': CinetPayGateway,
    'moneroo': MonerooGateway,
    'flutterwave': FlutterwaveGateway,
}

_gateway_instance: BasePaymentGateway | None = None


def get_payment_gateway() -> BasePaymentGateway:
    """
    Factory singleton : retourne le gateway configuré via
    settings.PAYMENT_GATEWAY (default: 'simulation').
    """
    global _gateway_instance

    if _gateway_instance is not None:
        return _gateway_instance

    gateway_name = getattr(settings, 'PAYMENT_GATEWAY', 'simulation')

    gateway_cls = _GATEWAY_MAP.get(gateway_name)
    if gateway_cls is None:
        raise ValueError(
            f"Gateway inconnu : '{gateway_name}'. "
            f"Valeurs acceptées : {list(_GATEWAY_MAP.keys())}"
        )

    _gateway_instance = gateway_cls()
    logger.info("Payment gateway initialisé : %s", gateway_name)
    return _gateway_instance


def reset_gateway() -> None:
    """Réinitialise le singleton (utile pour les tests)."""
    global _gateway_instance
    _gateway_instance = None
