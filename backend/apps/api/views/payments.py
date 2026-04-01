"""
Vues Payments — Monajent
────────────────────────
Endpoints :
    POST /api/client/packs/buy/                          → Initier un achat de pack
    POST /api/payments/webhook/                          → Webhook provider (non authentifié)
    POST /api/payments/simulate/{tx_ref}/confirm/        → Confirmer paiement (dev only)
    GET  /api/client/payments/                           → Historique paiements client
"""

import logging

from django.conf import settings
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsClient
from apps.api.throttles import PackPurchaseThrottle
from apps.api.serializers.payments import (
    InitiatePaymentSerializer,
    InitiatePaymentResponseSerializer,
    PaymentSerializer,
)
from apps.payments.models import Payment
from apps.core.services.payment import (
    initiate_pack_purchase,
    process_webhook,
    verify_and_process,
    PaymentError,
    PaymentAlreadyProcessedError,
    PaymentNotFoundError,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# 1. Initier un achat de pack
# ═══════════════════════════════════════════════════════════════


class InitiatePackPurchaseView(APIView):
    """
    POST /api/client/packs/buy/

    Le client choisit un provider (ORANGE_MONEY, WAVE, MTN, CARD)
    et reçoit une URL de checkout pour payer.
    """
    permission_classes = [IsAuthenticated, IsClient]
    throttle_classes = [PackPurchaseThrottle]

    def post(self, request):
        serializer = InitiatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        provider = serializer.validated_data['provider']
        return_url = serializer.validated_data.get('return_url', '')

        try:
            result = initiate_pack_purchase(
                user=request.user,
                provider=provider,
                return_url=return_url,
            )
        except PaymentError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payment = result['payment']
        response_data = {
            'payment_id': payment.pk,
            'tx_ref': payment.tx_ref,
            'checkout_url': result['checkout_url'],
            'access_code': payment.provider_tx_id,
            'status': payment.status,
            'amount': payment.amount,
            'currency': payment.currency,
            'provider': payment.provider,
        }
        response_serializer = InitiatePaymentResponseSerializer(response_data)

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


# ═══════════════════════════════════════════════════════════════
# 2. Webhook provider (non authentifié)
# ═══════════════════════════════════════════════════════════════


PAYSTACK_WEBHOOK_IPS = frozenset({
    '52.31.139.75',
    '52.49.173.169',
    '52.214.14.220',
})


def _get_client_ip(request) -> str:
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    xri = request.META.get('HTTP_X_REAL_IP')
    if xri:
        return xri.strip()
    return request.META.get('REMOTE_ADDR', '')


class PaymentWebhookView(APIView):
    """
    POST /api/payments/webhook/

    Endpoint appelé par le provider de paiement après confirmation ou échec.
    Non authentifié — validation via signature HMAC + IP whitelisting (prod).
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        if not settings.DEBUG:
            client_ip = _get_client_ip(request)
            logger.info(
                "Webhook reçu — REMOTE_ADDR=%s, X-Forwarded-For=%s, X-Real-Ip=%s, IP résolue=%s",
                request.META.get('REMOTE_ADDR', ''),
                request.META.get('HTTP_X_FORWARDED_FOR', ''),
                request.META.get('HTTP_X_REAL_IP', ''),
                client_ip,
            )
            if client_ip not in PAYSTACK_WEBHOOK_IPS:
                logger.warning(
                    "Webhook rejeté : IP %s non autorisée", client_ip,
                )
                return Response(
                    {'detail': 'IP non autorisée.'},
                    status=status.HTTP_403_FORBIDDEN,
                )

        payload = request.data if isinstance(request.data, dict) else {}
        headers = dict(request.headers)
        raw_body = request.body if hasattr(request, 'body') else b''

        try:
            payment = process_webhook(payload=payload, headers=headers, raw_body=raw_body)
        except PaymentAlreadyProcessedError:
            return Response(
                {'detail': 'Paiement déjà traité.'},
                status=status.HTTP_200_OK,
            )
        except PaymentNotFoundError:
            ref = payload.get('tx_ref') or payload.get('data', {}).get('reference', '?')
            logger.warning("Webhook reçu pour tx_ref inconnu : %s", ref)
            return Response(
                {'detail': 'Transaction inconnue.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        except (PaymentError, ValueError) as e:
            logger.error("Erreur webhook : %s", e)
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({
            'detail': 'Webhook traité.',
            'tx_ref': payment.tx_ref,
            'status': payment.status,
        })


# ═══════════════════════════════════════════════════════════════
# 3. Simulation de confirmation (dev only)
# ═══════════════════════════════════════════════════════════════


class SimulatePaymentConfirmView(APIView):
    """
    POST /api/payments/simulate/{tx_ref}/confirm/

    Simule la confirmation de paiement (remplace le webhook réel).
    Disponible uniquement en mode DEBUG.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, tx_ref):
        if not settings.DEBUG:
            return Response(
                {'detail': "Cet endpoint n'est disponible qu'en mode développement."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            payment = Payment.objects.get(tx_ref=tx_ref)
        except Payment.DoesNotExist:
            return Response(
                {'detail': f"Aucun paiement trouvé pour tx_ref={tx_ref}"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if payment.status != Payment.Status.PENDING:
            return Response({
                'detail': f"Paiement déjà en statut {payment.get_status_display()}.",
                'tx_ref': payment.tx_ref,
                'status': payment.status,
            })

        import hashlib, hmac as hmac_mod, json

        simulated_payload = {
            'event': 'charge.success',
            'data': {
                'reference': payment.tx_ref,
                'id': payment.provider_tx_id,
                'status': 'success',
                'amount': int(payment.amount * 100),
                'currency': payment.currency,
            },
        }
        raw_body = json.dumps(simulated_payload).encode()
        secret = settings.PAYMENT_CONFIG.get('paystack', {}).get('secret_key', '')
        sig = hmac_mod.HMAC(secret.encode(), raw_body, hashlib.sha512).hexdigest()

        try:
            payment = process_webhook(
                payload=simulated_payload,
                headers={'X-Paystack-Signature': sig},
                raw_body=raw_body,
            )
        except PaymentError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        pack_info = None
        if payment.pack:
            pack_info = {
                'pack_id': payment.pack.pk,
                'virtual_total': payment.pack.virtual_total,
                'has_physical_key': payment.pack.has_physical_key,
            }

        return Response({
            'detail': 'Paiement simulé avec succès. Pack créé.',
            'tx_ref': payment.tx_ref,
            'status': payment.status,
            'pack': pack_info,
        })


# ═══════════════════════════════════════════════════════════════
# 4. Vérification de paiement (callback retour client)
# ═══════════════════════════════════════════════════════════════


class PaymentVerifyView(APIView):
    """
    POST /api/payments/verify/{tx_ref}/

    Vérifie le statut d'un paiement directement auprès du provider.
    Utilisé quand le client revient du checkout Paystack.
    """
    permission_classes = [IsAuthenticated, IsClient]

    def post(self, request, tx_ref):
        try:
            payment = Payment.objects.get(tx_ref=tx_ref, user=request.user)
        except Payment.DoesNotExist:
            return Response(
                {'detail': 'Paiement introuvable.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if payment.status != Payment.Status.PENDING:
            pack_info = None
            if payment.pack:
                pack_info = {
                    'pack_id': payment.pack.pk,
                    'virtual_total': payment.pack.virtual_total,
                    'has_physical_key': payment.pack.has_physical_key,
                }
            return Response({
                'tx_ref': payment.tx_ref,
                'status': payment.status,
                'pack': pack_info,
            })

        try:
            payment = verify_and_process(tx_ref=tx_ref)
        except PaymentError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except NotImplementedError:
            return Response({
                'tx_ref': payment.tx_ref,
                'status': payment.status,
                'detail': 'Vérification en temps réel non disponible pour ce provider.',
            })

        pack_info = None
        if payment.pack:
            pack_info = {
                'pack_id': payment.pack.pk,
                'virtual_total': payment.pack.virtual_total,
                'has_physical_key': payment.pack.has_physical_key,
            }

        return Response({
            'tx_ref': payment.tx_ref,
            'status': payment.status,
            'pack': pack_info,
        })


# ═══════════════════════════════════════════════════════════════
# 5. Historique des paiements (Client)
# ═══════════════════════════════════════════════════════════════


class ClientPaymentHistoryView(generics.ListAPIView):
    """
    GET /api/client/payments/

    Liste paginée des paiements du client (tous statuts).
    """
    permission_classes = [IsAuthenticated, IsClient]
    serializer_class = PaymentSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Payment.objects.none()
        return (
            Payment.objects
            .filter(user=self.request.user)
            .select_related('pack')
            .order_by('-created_at')
        )
