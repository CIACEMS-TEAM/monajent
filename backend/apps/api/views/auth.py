from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from apps.users.models import User, ClientProfile, AgentProfile
from apps.core.services.d7_verify import D7VerifyClient
from ..serializers.auth import (
    ClientRegisterSerializer,
    AgentRegisterSerializer,
    LoginSerializer,
    OTPRequestSerializer,
    OTPVerifySerializer,
    MeSerializer,
)


REFRESH_COOKIE_NAME = 'refresh_token'
REFRESH_COOKIE_PATH = '/api/auth/'


def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    max_age = int(settings.SIMPLE_JWT.get('REFRESH_TOKEN_LIFETIME', timedelta(days=14)).total_seconds())
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        max_age=max_age,
        httponly=True,
        secure=not settings.DEBUG,
        samesite='Lax',
        path=REFRESH_COOKIE_PATH,
    )


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path=REFRESH_COOKIE_PATH,
    )


def _issue_otp_for_user(user: User) -> str:
    """Demande un OTP via D7 et stocke l'otp_id externe."""
    recipient = user.phone
    if not recipient.startswith('+'):
        # Normalisation simple: préfixe pays par défaut (Côte d'Ivoire)
        recipient = f"+225{''.join(ch for ch in recipient if ch.isdigit())}"
    data = D7VerifyClient().send_otp(recipient)
    otp_id = data.get('otp_id') or data.get('request_id') or data.get('id')
    user.otp_provider = 'D7'
    user.otp_external_id = otp_id
    # D7 renvoie 'expiry' en secondes si présent
    seconds = int(data.get('expiry', 600))
    user.otp_expires_at = timezone.now() + timedelta(seconds=seconds)
    user.otp_code = None
    user.save(update_fields=['otp_provider', 'otp_external_id', 'otp_expires_at', 'otp_code'])
    return otp_id or ''


class RegisterClientView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ClientRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # Génération OTP immédiate via D7
        _issue_otp_for_user(user)
        return Response({'id': user.id, 'phone': user.phone, 'requires_otp': True}, status=status.HTTP_201_CREATED)


class RegisterAgentView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = AgentRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # Génération OTP immédiate via D7
        _issue_otp_for_user(user)
        return Response({'id': user.id, 'phone': user.phone, 'requires_otp': True}, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data['phone']
        password = serializer.validated_data['password']

        user = authenticate(request, username=phone, password=password)
        if not user:
            return Response({'detail': 'Identifiants invalides'}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)
        response = Response({'access': access}, status=status.HTTP_200_OK)
        set_refresh_cookie(response, str(refresh))
        return response


class RefreshView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        token = request.COOKIES.get(REFRESH_COOKIE_NAME)
        if not token:
            return Response({'detail': 'Refresh token manquant'}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            refresh = RefreshToken(token)
            user_id = refresh.get('user_id')
            user = User.objects.get(id=user_id)
        except Exception:
            return Response({'detail': 'Refresh token invalide'}, status=status.HTTP_401_UNAUTHORIZED)

        access = str(refresh.access_token)

        # Rotation optionnelle
        if settings.SIMPLE_JWT.get('ROTATE_REFRESH_TOKENS', False):
            try:
                if settings.SIMPLE_JWT.get('BLACKLIST_AFTER_ROTATION', False):
                    refresh.blacklist()  # type: ignore[attr-defined]
            except Exception:
                pass
            new_refresh = RefreshToken.for_user(user)
            response = Response({'access': access}, status=status.HTTP_200_OK)
            set_refresh_cookie(response, str(new_refresh))
            return response

        response = Response({'access': access}, status=status.HTTP_200_OK)
        return response


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Blacklist tous les refresh de l’utilisateur (optionnel)
        try:
            for token in OutstandingToken.objects.filter(user=request.user):
                BlacklistedToken.objects.get_or_create(token=token)
        except Exception:
            pass
        response = Response(status=status.HTTP_204_NO_CONTENT)
        clear_refresh_cookie(response)
        return response


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = MeSerializer(request.user)
        return Response(serializer.data)


class OTPRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = OTPRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data['phone']
        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            return Response({'detail': 'Utilisateur introuvable'}, status=status.HTTP_404_NOT_FOUND)

        # D7: si déjà un otp_id on fait un resend, sinon on en crée un
        if user.otp_provider == 'D7' and user.otp_external_id:
            D7VerifyClient().resend_otp(user.otp_external_id)
        else:
            _issue_otp_for_user(user)
        return Response({'detail': 'OTP envoyé'}, status=status.HTTP_200_OK)


class OTPVerifyView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data['phone']
        code = serializer.validated_data['code']
        otp_id = serializer.validated_data.get('otp_id') or None
        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            return Response({'detail': 'Utilisateur introuvable'}, status=status.HTTP_404_NOT_FOUND)

        # Si provider D7: vérifie côté D7
        if user.otp_provider == 'D7' and (user.otp_external_id or otp_id):
            d7 = D7VerifyClient()
            result = d7.verify_otp(otp_id or user.otp_external_id, code)
            status_str = str(result.get('status', '')).upper()
            if status_str not in {'APPROVED', 'ALREADY_VERIFIED'}:
                return Response({'detail': f'OTP {status_str or "FAILED"}'}, status=status.HTTP_400_BAD_REQUEST)
            # Consommer
            user.otp_external_id = None
            user.otp_expires_at = None
            user.save(update_fields=['otp_external_id', 'otp_expires_at'])
        else:
            # Fallback ancien flow local
            if not user.otp_code or not user.otp_expires_at:
                return Response({'detail': 'OTP non demandé'}, status=status.HTTP_400_BAD_REQUEST)
            if user.otp_code != code:
                return Response({'detail': 'OTP invalide'}, status=status.HTTP_400_BAD_REQUEST)
            if timezone.now() > user.otp_expires_at:
                return Response({'detail': "OTP expiré"}, status=status.HTTP_400_BAD_REQUEST)
            user.otp_code = None
            user.otp_expires_at = None
            user.save(update_fields=['otp_code', 'otp_expires_at'])

        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)
        response = Response({'access': access}, status=status.HTTP_200_OK)
        set_refresh_cookie(response, str(refresh))
        return response


