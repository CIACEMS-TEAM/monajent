"""
Vues Wallet — Monajent
──────────────────────
Agent :
    GET   /api/agent/wallet/              → Solde, totaux, has_pin
    GET   /api/agent/wallet/entries/      → Historique mouvements (filtrable)
    POST  /api/agent/wallet/set-pin/      → Configurer le code PIN (1ère fois)
    POST  /api/agent/wallet/change-pin/   → Changer le code PIN
    POST  /api/agent/wallet/withdraw/     → Demander un retrait (avec PIN)
    GET   /api/agent/wallet/withdrawals/  → Historique demandes de retrait
"""

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.wallet.models import Wallet, WalletEntry, WithdrawalRequest
from apps.core.permissions import IsAgent
from apps.api.serializers.wallet import (
    WalletSerializer,
    WalletEntrySerializer,
    PinSetSerializer,
    PinChangeSerializer,
    WithdrawalCreateSerializer,
    WithdrawalDetailSerializer,
)
from apps.core.services.withdrawal import (
    set_withdrawal_pin,
    change_withdrawal_pin,
    request_withdrawal,
    InsufficientBalanceError,
    BelowMinimumError,
    PendingWithdrawalExistsError,
    PinNotSetError,
    InvalidPinError,
    PinAlreadySetError,
    WithdrawalError,
)


# ═══════════════════════════════════════════════════════════════
# Solde + stats
# ═══════════════════════════════════════════════════════════════


class AgentWalletView(APIView):
    """
    GET /api/agent/wallet/
    Solde, totaux, has_pin, retrait en attente.
    """
    permission_classes = [IsAuthenticated, IsAgent]

    def get(self, request):
        wallet, _ = Wallet.objects.get_or_create(agent=request.user)
        serializer = WalletSerializer(wallet)
        return Response(serializer.data)


# ═══════════════════════════════════════════════════════════════
# Historique mouvements
# ═══════════════════════════════════════════════════════════════


class AgentWalletEntryListView(generics.ListAPIView):
    """
    GET /api/agent/wallet/entries/
    Filtres : ?source=VIDEO_VIEW|PHYSICAL_VISIT|WITHDRAWAL|ADJUSTMENT
              ?entry_type=CREDIT|DEBIT
    """
    permission_classes = [IsAuthenticated, IsAgent]
    serializer_class = WalletEntrySerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return WalletEntry.objects.none()

        wallet, _ = Wallet.objects.get_or_create(agent=self.request.user)
        qs = WalletEntry.objects.filter(wallet=wallet).order_by('-created_at')

        source = self.request.query_params.get('source')
        if source:
            qs = qs.filter(source=source)

        entry_type = self.request.query_params.get('entry_type')
        if entry_type:
            qs = qs.filter(entry_type=entry_type)

        return qs


# ═══════════════════════════════════════════════════════════════
# Code PIN de retrait
# ═══════════════════════════════════════════════════════════════


class AgentWalletSetPinView(APIView):
    """
    POST /api/agent/wallet/set-pin/
    Configure le code PIN de retrait pour la première fois.
    Requis avant le premier retrait.
    """
    permission_classes = [IsAuthenticated, IsAgent]

    def post(self, request):
        ser = PinSetSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        wallet, _ = Wallet.objects.get_or_create(agent=request.user)

        try:
            set_withdrawal_pin(wallet, ser.validated_data['pin'])
        except PinAlreadySetError as e:
            return Response({'detail': str(e)}, status=status.HTTP_409_CONFLICT)
        except WithdrawalError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'detail': "Code PIN de retrait configuré avec succès.",
            'has_pin': True,
        })


class AgentWalletChangePinView(APIView):
    """
    POST /api/agent/wallet/change-pin/
    Change le code PIN existant (nécessite l'ancien PIN).
    """
    permission_classes = [IsAuthenticated, IsAgent]

    def post(self, request):
        ser = PinChangeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        wallet, _ = Wallet.objects.get_or_create(agent=request.user)

        try:
            change_withdrawal_pin(
                wallet,
                current_pin=ser.validated_data['current_pin'],
                new_pin=ser.validated_data['new_pin'],
            )
        except PinNotSetError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except InvalidPinError as e:
            return Response({'detail': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except WithdrawalError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'detail': "Code PIN de retrait modifié avec succès.",
        })


# ═══════════════════════════════════════════════════════════════
# Demande de retrait (avec PIN)
# ═══════════════════════════════════════════════════════════════


class AgentWithdrawalCreateView(APIView):
    """
    POST /api/agent/wallet/withdraw/
    Demande de retrait. Nécessite le code PIN.
    Le montant est bloqué immédiatement.
    """
    permission_classes = [IsAuthenticated, IsAgent]

    def post(self, request):
        ser = WithdrawalCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        wallet, _ = Wallet.objects.get_or_create(agent=request.user)

        try:
            withdrawal = request_withdrawal(
                wallet=wallet,
                amount=ser.validated_data['amount'],
                method=ser.validated_data['method'],
                phone_number=ser.validated_data['phone_number'],
                pin=ser.validated_data['pin'],
            )
        except PinNotSetError as e:
            return Response(
                {'detail': str(e), 'pin_required': True},
                status=status.HTTP_403_FORBIDDEN,
            )
        except InvalidPinError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_403_FORBIDDEN,
            )
        except BelowMinimumError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except InsufficientBalanceError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except PendingWithdrawalExistsError as e:
            return Response({'detail': str(e)}, status=status.HTTP_409_CONFLICT)

        return Response(
            WithdrawalDetailSerializer(withdrawal).data,
            status=status.HTTP_201_CREATED,
        )


# ═══════════════════════════════════════════════════════════════
# Historique retraits
# ═══════════════════════════════════════════════════════════════


class AgentWithdrawalListView(generics.ListAPIView):
    """
    GET /api/agent/wallet/withdrawals/
    Historique de mes demandes de retrait.
    """
    permission_classes = [IsAuthenticated, IsAgent]
    serializer_class = WithdrawalDetailSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return WithdrawalRequest.objects.none()

        wallet, _ = Wallet.objects.get_or_create(agent=self.request.user)
        return (
            WithdrawalRequest.objects
            .filter(wallet=wallet)
            .order_by('-created_at')
        )
