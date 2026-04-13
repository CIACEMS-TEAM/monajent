"""
Vues Packs & Visionnage — Monajent
───────────────────────────────────
Endpoints :
    GET  /api/client/packs/                   → Mes packs (avec clés restantes)
    POST /api/client/packs/                   → Acheter un pack (dev only)
    GET  /api/client/packs/{id}/              → Détail d'un pack
    POST /api/videos/{access_key}/watch/      → Consommer 1 clé, débloquer la vidéo
    GET  /api/client/views/                   → Mon historique de visionnage
    GET  /api/agent/views/                    → Vues reçues sur mes annonces (stats agent)
"""

from django.conf import settings as django_settings
from django.core import signing
from django.http import FileResponse

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.packs.models import PackPurchase, VirtualKeyUsage
from apps.listings.models import Video
from apps.core.permissions import IsClient, IsAgent, IsObjectOwner
from apps.api.throttles import PackPurchaseThrottle, VideoViewThrottle

VIDEO_TOKEN_MAX_AGE = 3600  # 1 hour
TEASER_TOKEN_MAX_AGE = 120  # 2 minutes (enough time to watch teaser + react)
from apps.api.serializers.packs import (
    PackPurchaseSerializer,
    PackPurchaseCreateSerializer,
    WatchVideoResponseSerializer,
    VirtualKeyUsageSerializer,
)
from apps.core.services.viewing import (
    consume_virtual_key,
    AlreadyWatchedError,
    NoActivePackError,
)


# ═══════════════════════════════════════════════════════════════
# Client : Mes packs
# ═══════════════════════════════════════════════════════════════


class ClientPackListCreateView(generics.ListCreateAPIView):
    """
    GET  → Liste des packs du client (avec clés restantes).
    POST → Acheter un pack (simplifié pour dev ; en prod, créé après paiement).
    """
    permission_classes = [IsAuthenticated, IsClient]
    serializer_class = PackPurchaseSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return PackPurchase.objects.none()
        return PackPurchase.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PackPurchaseCreateSerializer
        return PackPurchaseSerializer

    def get_throttles(self):
        if self.request.method == 'POST':
            return [PackPurchaseThrottle()]
        return []

    def create(self, request, *args, **kwargs):
        pack = PackPurchase.objects.create(user=request.user)
        serializer = PackPurchaseSerializer(pack)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ClientPackDetailView(generics.RetrieveAPIView):
    """Détail d'un pack du client."""
    permission_classes = [IsAuthenticated, IsClient, IsObjectOwner]
    serializer_class = PackPurchaseSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return PackPurchase.objects.none()
        return PackPurchase.objects.filter(user=self.request.user)


# ═══════════════════════════════════════════════════════════════
# Client : Visionnage (le coeur du pay-per-view)
# ═══════════════════════════════════════════════════════════════


class WatchVideoView(APIView):
    """
    POST /api/videos/{access_key}/watch/

    En mode PAYMENT_STANDBY : retourne l'URL de stream pour tout
    utilisateur authentifié, sans consommer de clé.
    Sinon : consomme 1 clé virtuelle (pay-per-view classique).
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [VideoViewThrottle]

    def post(self, request, access_key):
        try:
            video = (
                Video.objects
                .select_related('listing', 'listing__agent')
                .get(access_key=access_key)
            )
        except Video.DoesNotExist:
            return Response(
                {'detail': "Vidéo introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if video.listing.agent_id == request.user.id:
            return Response(
                {'detail': "Vous ne pouvez pas visionner vos propres vidéos."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payment_standby = getattr(django_settings, 'PAYMENT_STANDBY', False)

        if payment_standby:
            already_watched = True
            pack_remaining = 0
        else:
            try:
                result = consume_virtual_key(user=request.user, video=video)
                pack_remaining = result['pack'].virtual_remaining
                already_watched = False
            except AlreadyWatchedError as e:
                pack_remaining = e.usage.pack.virtual_remaining
                already_watched = True
            except NoActivePackError:
                return Response(
                    {'detail': "Aucun pack actif avec des clés restantes. Achetez un nouveau pack."},
                    status=status.HTTP_402_PAYMENT_REQUIRED,
                )

        token = signing.dumps({
            'v': video.pk,
            'u': request.user.pk,
        }, salt='video-stream')

        stream_url = request.build_absolute_uri(
            f'/api/videos/stream/{token}/'
        )

        data = {
            'video_url': stream_url,
            'video_id': video.pk,
            'listing_id': video.listing_id,
            'listing_title': video.listing.title,
            'pack_remaining': pack_remaining,
            'already_watched': already_watched,
        }
        response_serializer = WatchVideoResponseSerializer(data)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class VideoTeaserView(APIView):
    """
    GET /api/videos/{access_key}/teaser/

    Public endpoint (no auth required).
    Returns a short-lived stream URL for the teaser preview,
    plus contextual info so the frontend knows which CTA to show.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, access_key):
        from rest_framework_simplejwt.authentication import JWTAuthentication

        try:
            video = (
                Video.objects
                .select_related('listing', 'listing__agent')
                .get(access_key=access_key)
            )
        except Video.DoesNotExist:
            return Response(
                {'detail': 'Vidéo introuvable.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        user = None
        try:
            auth_result = JWTAuthentication().authenticate(request)
            if auth_result:
                user = auth_result[0]
        except Exception:
            pass

        is_authenticated = user is not None
        is_agent_owner = (
            is_authenticated
            and hasattr(user, 'role')
            and user.role == 'AGENT'
            and video.listing.agent_id == user.id
        )
        payment_standby = getattr(django_settings, 'PAYMENT_STANDBY', False)
        is_unlocked = False
        keys_available = 0

        if payment_standby and is_authenticated and not is_agent_owner:
            keys_available = 1
        elif is_authenticated and not is_agent_owner:
            is_unlocked = VirtualKeyUsage.objects.filter(
                user=user, video=video,
            ).exists()

            if not is_unlocked:
                packs = PackPurchase.objects.filter(user=user)
                keys_available = sum(
                    max(p.virtual_total - p.virtual_used, 0) for p in packs
                )

        teaser_seconds = getattr(django_settings, 'TEASER_SECONDS', 15)

        teaser_token = signing.dumps(
            {'v': video.pk, 't': True},
            salt='video-stream',
        )
        stream_url = request.build_absolute_uri(
            f'/api/videos/stream/{teaser_token}/'
        )

        return Response({
            'stream_url': stream_url,
            'teaser_seconds': teaser_seconds,
            'is_authenticated': is_authenticated,
            'is_agent_owner': is_agent_owner,
            'is_unlocked': is_unlocked,
            'keys_available': keys_available,
            'video_id': video.pk,
            'listing_id': video.listing_id,
            'listing_title': video.listing.title,
            'duration_sec': video.duration_sec,
        })


class VideoStreamView(APIView):
    """
    GET /api/videos/stream/{token}/
    Serve video file with a signed, time-limited token.
    No authentication required (token IS the auth).
    """
    permission_classes = []
    authentication_classes = []

    def get(self, request, token):
        is_teaser = False
        try:
            payload = signing.loads(token, salt='video-stream', max_age=VIDEO_TOKEN_MAX_AGE)
            is_teaser = payload.get('t', False)
        except signing.BadSignature:
            return Response(
                {'detail': 'Lien vidéo expiré ou invalide. Rechargez la page.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            video = Video.objects.get(pk=payload['v'])
        except Video.DoesNotExist:
            return Response({'detail': 'Vidéo introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        if not video.file:
            return Response({'detail': 'Fichier vidéo manquant.'}, status=status.HTTP_404_NOT_FOUND)

        response = FileResponse(video.file.open('rb'), content_type='video/mp4')
        response['Cache-Control'] = 'private, no-store, no-cache, must-revalidate'
        response['Content-Disposition'] = 'inline'
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Robots-Tag'] = 'noindex, nofollow'
        return response


# ═══════════════════════════════════════════════════════════════
# Client : Historique de visionnage
# ═══════════════════════════════════════════════════════════════


class ClientViewHistoryListView(generics.ListAPIView):
    """
    GET /api/client/views/ → Historique de visionnage du client.
    Liste triée du plus récent au plus ancien.
    """
    permission_classes = [IsAuthenticated, IsClient]
    serializer_class = VirtualKeyUsageSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return VirtualKeyUsage.objects.none()
        return (
            VirtualKeyUsage.objects
            .filter(user=self.request.user)
            .select_related('video', 'video__listing', 'agent')
            .order_by('-created_at')
        )


# ═══════════════════════════════════════════════════════════════
# Agent : Vues reçues (stats)
# ═══════════════════════════════════════════════════════════════


class AgentViewsReceivedListView(generics.ListAPIView):
    """
    GET /api/agent/views/ → Liste des visionnages sur les vidéos de l'agent.
    Permet à l'agent de voir qui a vu ses vidéos et les revenus générés.
    """
    permission_classes = [IsAuthenticated, IsAgent]
    serializer_class = VirtualKeyUsageSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return VirtualKeyUsage.objects.none()
        return (
            VirtualKeyUsage.objects
            .filter(agent=self.request.user)
            .select_related('video', 'video__listing', 'user')
            .order_by('-created_at')
        )
