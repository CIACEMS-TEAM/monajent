from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate
from django.utils import timezone
from django.core import signing
from django.contrib.auth.hashers import make_password
from django.core.cache import cache
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from apps.users.models import User, ClientProfile, AgentProfile
from apps.core.services.d7_verify import D7VerifyClient, D7VerifyError
from apps.core.utils.phone import normalize_to_e164
from ..serializers.auth import (
    ClientRegisterSerializer,
    AgentRegisterSerializer,
    LoginSerializer,
    OTPRequestSerializer,
    OTPVerifySerializer,
    PasswordResetRequestSerializer,
    PasswordResetVerifySerializer,
    PasswordResetFinalizeSerializer,
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
        samesite=getattr(settings, 'AUTH_COOKIE_SAMESITE', 'Lax'),
        path=REFRESH_COOKIE_PATH,
    )


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path=REFRESH_COOKIE_PATH,
    )


# Plus de fonction d'émission OTP liée au modèle: flux stateless avec pending_token


def _build_pending_token(payload: dict) -> str:
    return signing.dumps(payload, salt='signup')


def _read_pending_token(token: str) -> dict:
    data = signing.loads(token, salt='signup')
    exp_ts = data.get('exp_ts')
    if exp_ts and timezone.now().timestamp() > float(exp_ts):
        raise signing.BadSignature('pending token expired')
    return data


def _is_same_site_request(request) -> bool:
    """
    Renforce la protection CSRF pour endpoints cookie-only (refresh/logout):
    - Hors DEBUG: exige X-Requested-With: XMLHttpRequest
    - Hors DEBUG: exige Origin ou Referer présent et appartenant aux origines autorisées
    - En DEBUG: on reste permissif (utile pour CLI/tests)
    """
    allowed = set(getattr(settings, 'CORS_ALLOWED_ORIGINS', []))
    # En dev, tolère localhost
    if settings.DEBUG:
        allowed.update({'http://localhost:5173', 'http://localhost:3000', 'http://127.0.0.1:5173'})

    # Exiger X-Requested-With en prod
    if not settings.DEBUG:
        xrw = request.META.get('HTTP_X_REQUESTED_WITH', '')
        if xrw.lower() != 'xmlhttprequest':
            return False

    origin = request.META.get('HTTP_ORIGIN')
    referer = request.META.get('HTTP_REFERER')
    header = origin or referer

    # En prod, refuser si pas d'Origin/Referer
    if not settings.DEBUG and not header:
        return False

    # Si aucun header, autoriser en DEBUG uniquement (CLI)
    if not header:
        return True

    return any(str(header).startswith(a) for a in allowed)

def _build_reset_token(payload: dict) -> str:
    return signing.dumps(payload, salt='password-reset')


def _read_reset_token(token: str) -> dict:
    data = signing.loads(token, salt='password-reset')
    exp_ts = data.get('exp_ts')
    if exp_ts and timezone.now().timestamp() > float(exp_ts):
        raise signing.BadSignature('reset token expired')
    return data


def _build_reset_session_token(payload: dict) -> str:
    return signing.dumps(payload, salt='password-reset-session')


def _read_reset_session_token(token: str) -> dict:
    data = signing.loads(token, salt='password-reset-session')
    exp_ts = data.get('exp_ts')
    if exp_ts and timezone.now().timestamp() > float(exp_ts):
        raise signing.BadSignature('reset session token expired')
    return data


# --- Lockout login simple via cache ---
_LOGIN_FAIL_MAX = 5
_LOGIN_FAIL_WINDOW_SEC = 15 * 60  # 15 minutes
_LOGIN_LOCKOUT_SEC = 15 * 60


def _cache_key_login_fail(phone_e164: str) -> str:
    return f"auth:login:fail:{phone_e164}"


def _cache_key_login_lock(phone_e164: str) -> str:
    return f"auth:login:lock:{phone_e164}"


def _login_is_locked(phone_e164: str) -> int:
    """Retourne secondes restantes si verrouillé, sinon 0."""
    key = _cache_key_login_lock(phone_e164)
    ttl = cache.ttl(key)
    if ttl is None:
        # backend sans ttl natif, fallback
        return 1 if cache.get(key) else 0
    return max(ttl, 0)


def _register_login_failure(phone_e164: str) -> int:
    """Incrémente les échecs et retourne le total actuel."""
    key = _cache_key_login_fail(phone_e164)
    try:
        # incr atomique si supporté
        count = cache.incr(key)
    except Exception:
        # initialise
        count = 1
        cache.set(key, count, timeout=_LOGIN_FAIL_WINDOW_SEC)
    if count == 1:
        cache.expire(key, _LOGIN_FAIL_WINDOW_SEC) if hasattr(cache, 'expire') else None
    if count >= _LOGIN_FAIL_MAX:
        cache.set(_cache_key_login_lock(phone_e164), True, timeout=_LOGIN_LOCKOUT_SEC)
    return count


def _reset_login_failures(phone_e164: str) -> None:
    cache.delete_many([_cache_key_login_fail(phone_e164), _cache_key_login_lock(phone_e164)])


class RegisterClientView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'otp_request'

    def post(self, request):
        serializer = ClientRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vd = serializer.validated_data
        phone_e164 = normalize_to_e164(vd['phone'])
        # Appel D7
        d7 = D7VerifyClient()
        try:
            data = d7.send_otp(phone_e164)
        except D7VerifyError:
            return Response({'detail': 'Service OTP indisponible, réessayez plus tard'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        otp_id = data.get('otp_id') or data.get('request_id')
        expiry = int(data.get('expiry', 600))
        pending = {
            'role': 'CLIENT',
            'phone': phone_e164,
            'username': vd['username'],
            'email': None,
            'password_hash': make_password(vd['password']),
            'otp_id': otp_id,
            'exp_sec': expiry,
            'exp_ts': (timezone.now() + timedelta(seconds=expiry)).timestamp(),
        }
        token = _build_pending_token(pending)
        return Response({'requires_otp': True, 'pending_token': token}, status=status.HTTP_201_CREATED)


class RegisterAgentView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'otp_request'

    def post(self, request):
        serializer = AgentRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vd = serializer.validated_data
        phone_e164 = normalize_to_e164(vd['phone'])
        d7 = D7VerifyClient()
        try:
            data = d7.send_otp(phone_e164)
        except D7VerifyError:
            return Response({'detail': 'Service OTP indisponible, réessayez plus tard'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        otp_id = data.get('otp_id') or data.get('request_id')
        expiry = int(data.get('expiry', 600))
        pending = {
            'role': 'AGENT',
            'phone': phone_e164,
            'username': vd.get('username') or '',
            'email': vd.get('email') or None,
            'agency_name': vd.get('agency_name') or '',
            'password_hash': make_password(vd['password']),
            'otp_id': otp_id,
            'exp_sec': expiry,
            'exp_ts': (timezone.now() + timedelta(seconds=expiry)).timestamp(),
        }
        token = _build_pending_token(pending)
        return Response({'requires_otp': True, 'pending_token': token}, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'auth_login'

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data['phone']
        password = serializer.validated_data['password']

        phone_e164 = normalize_to_e164(phone)
        # Lockout check
        locked_ttl = _login_is_locked(phone_e164)
        if locked_ttl:
            return Response({'detail': 'Trop de tentatives. Réessayez plus tard.'}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        user = authenticate(request, username=phone_e164, password=password)
        if not user:
            _register_login_failure(phone_e164)
            return Response({'detail': 'Identifiants invalides'}, status=status.HTTP_401_UNAUTHORIZED)

        _reset_login_failures(phone_e164)
        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)
        response = Response({'access': access}, status=status.HTTP_200_OK)
        set_refresh_cookie(response, str(refresh))
        return response


class RefreshView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'auth_refresh'

    def post(self, request):
        if not _is_same_site_request(request):
            return Response({'detail': 'Origine non autorisée'}, status=status.HTTP_403_FORBIDDEN)
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
    throttle_scope = 'auth_logout'

    def post(self, request):
        if not _is_same_site_request(request):
            return Response({'detail': 'Origine non autorisée'}, status=status.HTTP_403_FORBIDDEN)
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
    throttle_scope = 'otp_request'

    def post(self, request):
        serializer = OTPRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pending = _read_pending_token(serializer.validated_data['pending_token'])
        otp_id = pending.get('otp_id')
        d7 = D7VerifyClient()
        try:
            if otp_id:
                d7.resend_otp(otp_id)
            else:
                data = d7.send_otp(pending['phone'])
                pending['otp_id'] = data.get('otp_id') or data.get('request_id')
        except D7VerifyError:
            return Response({'detail': 'Service OTP indisponible, réessayez plus tard'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        token = _build_pending_token(pending)
        return Response({'detail': 'OTP envoyé', 'pending_token': token}, status=status.HTTP_200_OK)


class OTPVerifyView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'otp_verify'

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data['code']
        pending = _read_pending_token(serializer.validated_data['pending_token'])
        otp_id = serializer.validated_data.get('otp_id') or pending.get('otp_id')
        if not otp_id:
            return Response({'detail': 'OTP non initialisé'}, status=status.HTTP_400_BAD_REQUEST)
        # Vérifier D7
        d7 = D7VerifyClient()
        try:
            result = d7.verify_otp(otp_id, code)
        except D7VerifyError:
            return Response({'detail': 'Service OTP indisponible, réessayez plus tard'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        status_str = str(result.get('status', '')).upper()
        if status_str not in {'APPROVED', 'ALREADY_VERIFIED'}:
            return Response({'detail': f'OTP {status_str or "FAILED"}'}, status=status.HTTP_400_BAD_REQUEST)

        # Créer l'utilisateur réel
        role = pending.get('role')
        phone_e164 = pending.get('phone')
        username = pending.get('username') or None
        email = pending.get('email') or None
        password_hash = pending.get('password_hash')

        # On ne passe pas le mot de passe brut, on l'assigne via set_password après création
        user = User(
            phone=phone_e164,
            username=username,
            email=email,
            role=role,
        )
        user.password = password_hash
        user.save()

        if role == 'CLIENT':
            ClientProfile.objects.create(user=user)
        elif role == 'AGENT':
            AgentProfile.objects.create(user=user, agency_name=pending.get('agency_name') or '')

        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)
        response = Response({'access': access}, status=status.HTTP_200_OK)
        set_refresh_cookie(response, str(refresh))
        return response


class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'password_reset_request'

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data['phone']
        phone_e164 = normalize_to_e164(phone)
        try:
            user = User.objects.get(phone=phone_e164)
        except User.DoesNotExist:
            # ne pas divulguer l'existence
            return Response({'detail': 'OTP envoyé'}, status=status.HTTP_200_OK)

        d7 = D7VerifyClient()
        try:
            data = d7.send_otp(phone_e164)
        except D7VerifyError:
            return Response({'detail': 'Service OTP indisponible, réessayez plus tard'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        otp_id = data.get('otp_id') or data.get('request_id')
        expiry = int(data.get('expiry', 600))
        reset = {
            'phone': phone_e164,
            'otp_id': otp_id,
            'exp_ts': (timezone.now() + timedelta(seconds=expiry)).timestamp(),
        }
        token = _build_reset_token(reset)
        return Response({'reset_token': token, 'detail': 'OTP envoyé'}, status=status.HTTP_200_OK)


class PasswordResetVerifyView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'password_reset_verify'

    def post(self, request):
        serializer = PasswordResetVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data['reset_token']
        code = serializer.validated_data['code']
        try:
            reset = _read_reset_token(token)
        except signing.BadSignature:
            return Response({'detail': 'Jeton invalide ou expiré'}, status=status.HTTP_400_BAD_REQUEST)

        otp_id = reset.get('otp_id')
        if not otp_id:
            return Response({'detail': 'OTP non initialisé'}, status=status.HTTP_400_BAD_REQUEST)

        d7 = D7VerifyClient()
        try:
            result = d7.verify_otp(otp_id, code)
        except D7VerifyError:
            return Response({'detail': 'Service OTP indisponible, réessayez plus tard'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        status_str = str(result.get('status', '')).upper()
        if status_str not in {'APPROVED', 'ALREADY_VERIFIED'}:
            return Response({'detail': f'OTP {status_str or "FAILED"}'}, status=status.HTTP_400_BAD_REQUEST)

        # Construire un reset_session_token court (10 minutes)
        phone_e164 = reset.get('phone')
        session = {
            'phone': phone_e164,
            'exp_ts': (timezone.now() + timedelta(minutes=10)).timestamp(),
        }
        rst = _build_reset_session_token(session)
        return Response({'reset_session_token': rst}, status=status.HTTP_200_OK)


class PasswordResetFinalizeView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'password_reset_finalize'

    def post(self, request):
        serializer = PasswordResetFinalizeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rst = serializer.validated_data['reset_session_token']
        new_password = serializer.validated_data['new_password']
        try:
            session = _read_reset_session_token(rst)
        except signing.BadSignature:
            return Response({'detail': 'Session de réinitialisation invalide ou expirée'}, status=status.HTTP_400_BAD_REQUEST)

        phone_e164 = session.get('phone')
        try:
            user = User.objects.get(phone=phone_e164)
        except User.DoesNotExist:
            return Response({'detail': 'Utilisateur introuvable'}, status=status.HTTP_404_NOT_FOUND)

        user.set_password(new_password)
        user.save(update_fields=['password'])
        return Response({'detail': 'Mot de passe mis à jour'}, status=status.HTTP_200_OK)


