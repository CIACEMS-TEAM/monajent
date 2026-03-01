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

from django.core import signing
from django.http import FileResponse

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.packs.models import PackPurchase, VirtualKeyUsage
from apps.listings.models import Video
from apps.core.permissions import IsClient, IsAgent, IsObjectOwner
from apps.api.throttles import PackPurchaseThrottle, VideoViewThrottle

VIDEO_TOKEN_MAX_AGE = 3600  # 1 hour
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

    Consomme 1 clé virtuelle et retourne l'URL de la vidéo.
    Si la vidéo a déjà été vue, retourne l'URL sans consommer de clé.
    """
    permission_classes = [IsAuthenticated, IsClient]
    throttle_classes = [VideoViewThrottle]

    def post(self, request, access_key):
        # Récupérer la vidéo par access_key
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

        # Empêcher un agent de "se regarder" lui-même
        if video.listing.agent_id == request.user.id:
            return Response(
                {'detail': "Vous ne pouvez pas visionner vos propres vidéos."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = consume_virtual_key(user=request.user, video=video)
            pack = result['pack']
            already_watched = False

        except AlreadyWatchedError as e:
            # Déjà vu → retour gratuit de l'URL
            pack = e.usage.pack
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
            'pack_remaining': pack.virtual_remaining,
            'already_watched': already_watched,
        }
        response_serializer = WatchVideoResponseSerializer(data)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class VideoStreamView(APIView):
    """
    GET /api/videos/stream/{token}/
    Serve video file with a signed, time-limited token.
    No authentication required (token IS the auth).
    """
    permission_classes = []
    authentication_classes = []

    def get(self, request, token):
        try:
            payload = signing.loads(token, salt='video-stream', max_age=VIDEO_TOKEN_MAX_AGE)
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
