from datetime import timedelta
import random

from django.conf import settings
from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from apps.users.models import User, ClientProfile, AgentProfile
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
    """Génère et assigne un OTP 6 chiffres au user (dev: affiché en console)."""
    code = f"{random.randint(0, 999999):06d}"
    user.otp_code = code
    user.otp_expires_at = timezone.now() + timedelta(minutes=10)
    user.save(update_fields=['otp_code', 'otp_expires_at'])
    # Simulation: affichage console pour tests en attendant le provider SMS
    print('[OTP][DEV]', user.phone, code, user.otp_expires_at)  # noqa: T201 (print intentionnel en dev)
    return code


class RegisterClientView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ClientRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # Génération OTP immédiate pour le flux d'inscription (simulation console)
        _issue_otp_for_user(user)
        return Response({'id': user.id, 'phone': user.phone, 'requires_otp': True}, status=status.HTTP_201_CREATED)


class RegisterAgentView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = AgentRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # Génération OTP immédiate pour le flux d'inscription (simulation console)
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

        user.otp_code = serializer.validated_data['code']  # code généré par le serializer
        user.otp_expires_at = timezone.now() + timedelta(minutes=10)
        user.save(update_fields=['otp_code', 'otp_expires_at'])

        print(user.otp_code)
        print(user.otp_expires_at)

        # TODO: envoyer SMS via provider (OM/MTN/Wave ou agrégateur)
        return Response({'detail': 'OTP envoyé'}, status=status.HTTP_200_OK)


class OTPVerifyView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data['phone']
        code = serializer.validated_data['code']
        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            return Response({'detail': 'Utilisateur introuvable'}, status=status.HTTP_404_NOT_FOUND)

        if not user.otp_code or not user.otp_expires_at:
            return Response({'detail': 'OTP non demandé'}, status=status.HTTP_400_BAD_REQUEST)
        if user.otp_code != code:
            return Response({'detail': 'OTP invalide'}, status=status.HTTP_400_BAD_REQUEST)
        if timezone.now() > user.otp_expires_at:
            return Response({'detail': "OTP expiré"}, status=status.HTTP_400_BAD_REQUEST)

        print(user.otp_code)
        print(user.otp_expires_at)

        # Consommer l’OTP
        user.otp_code = None
        user.otp_expires_at = None
        user.save(update_fields=['otp_code', 'otp_expires_at'])

        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)
        response = Response({'access': access}, status=status.HTTP_200_OK)
        set_refresh_cookie(response, str(refresh))
        return response


