"""
Vues Listings — Monajent
────────────────────────
Endpoints REST pour les annonces immobilières.

Public :
  GET  /api/listings/              Recherche / liste des annonces actives
  GET  /api/listings/{id}/         Détail d'une annonce

Agent (CRUD) :
  GET    /api/agent/listings/                      Mes annonces
  POST   /api/agent/listings/                      Créer une annonce
  GET    /api/agent/listings/{id}/                  Détail (avec vidéos complètes)
  PATCH  /api/agent/listings/{id}/                  Modifier
  DELETE /api/agent/listings/{id}/                  Supprimer

  POST   /api/agent/listings/{id}/images/           Upload image
  DELETE /api/agent/listings/{id}/images/{img_id}/  Supprimer image

  POST   /api/agent/listings/{id}/videos/           Upload vidéo
  DELETE /api/agent/listings/{id}/videos/{vid_id}/  Supprimer vidéo
"""

from django.shortcuts import get_object_or_404
from django.core.cache import cache
from django.db.models import F

from rest_framework import generics, permissions, status, filters
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from apps.listings.models import Listing, ListingImage, ListingVisit, Video
from apps.core.permissions import (
    IsAgent, IsVerifiedAgent, IsListingOwner, IsOwnerOrReadOnly,
)
from apps.core.services.video_dedup import (
    validate_and_hash_video, DuplicateVideoError, check_hash_exists,
)
from apps.core.services.video_thumbnail import generate_thumbnail, get_video_duration
from ..serializers.listings import (
    ListingListSerializer,
    ListingDetailSerializer,
    ListingCreateSerializer,
    AgentListingDetailSerializer,
    ListingImageSerializer,
    ListingImageUploadSerializer,
    VideoUploadSerializer,
    VideoAgentSerializer,
)


def _get_client_ip(request) -> str:
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    return xff.split(',')[0].strip() if xff else request.META.get('REMOTE_ADDR', '')


# ═══════════════════════════════════════════════════════════════
# Public — Recherche et détail d'annonces
# ═══════════════════════════════════════════════════════════════


class PublicListingPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


class PublicListingListView(generics.ListAPIView):
    """
    GET /api/listings/
    Liste des annonces actives avec recherche et filtrage.
    Accessible à tous (public).
    """
    serializer_class = ListingListSerializer
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'listing_search'
    pagination_class = PublicListingPagination

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'listing_type': ['exact'],
        'city': ['exact', 'icontains'],
        'neighborhood': ['exact', 'icontains'],
        'furnishing': ['exact'],
        'rooms': ['exact', 'gte', 'lte'],
        'bedrooms': ['exact', 'gte', 'lte'],
        'price': ['gte', 'lte'],
        'surface_m2': ['gte', 'lte'],
    }
    search_fields = ['title', 'description', 'city', 'neighborhood', 'address']
    ordering_fields = ['price', 'created_at', 'views_count']
    ordering = ['-created_at']

    def get_queryset(self):
        return (
            Listing.objects
            .filter(status=Listing.Status.ACTIF)
            .select_related('agent__agent_profile')
            .prefetch_related('images', 'videos')
        )


class PublicListingDetailView(generics.RetrieveAPIView):
    """
    GET /api/listings/{slug}/
    Détail d'une annonce active (lookup par slug).
    Accessible à tous (public).
    Incrémente views_count (dédupliqué par IP, TTL 30 min).
    """
    serializer_class = ListingDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'

    def get_queryset(self):
        return (
            Listing.objects
            .filter(status=Listing.Status.ACTIF)
            .select_related('agent__agent_profile')
            .prefetch_related('images', 'videos')
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        cache_key = f"lv_{instance.pk}_{_get_client_ip(request)}"
        if not cache.get(cache_key):
            Listing.objects.filter(pk=instance.pk).update(views_count=F('views_count') + 1)
            cache.set(cache_key, True, 1800)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class RegisterListingVisitView(APIView):
    """
    POST /api/listings/{slug}/visit/
    Enregistre une visite (première interaction média) pour l'utilisateur
    connecté. Idempotent : renvoie already_visited=true si déjà enregistré.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slug):
        listing = Listing.objects.filter(
            slug=slug, status=Listing.Status.ACTIF,
        ).first()
        if not listing:
            return Response(
                {'detail': 'Annonce introuvable.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        _, created = ListingVisit.objects.get_or_create(
            listing=listing, user=request.user,
        )
        if created:
            Listing.objects.filter(pk=listing.pk).update(
                visits_count=F('visits_count') + 1,
            )
        return Response({
            'already_visited': not created,
            'visits_count': listing.visits_count + (1 if created else 0),
        })


# ═══════════════════════════════════════════════════════════════
# Agent — CRUD sur ses propres annonces
# ═══════════════════════════════════════════════════════════════


class AgentListingListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/agent/listings/     Mes annonces (actives + inactives)
    POST /api/agent/listings/     Créer une annonce (tout agent, mais INACTIF si pas KYC)

    Throttle : GET utilise agent_listing_read (dashboard / actualisations fréquentes) ;
    POST seul utilise listing_create (quota création d'annonces).
    """
    serializer_class = ListingListSerializer
    permission_classes = [permissions.IsAuthenticated, IsAgent]
    pagination_class = None

    def get_throttles(self):
        if getattr(self, 'swagger_fake_view', False):
            return super().get_throttles()
        if self.request.method == 'GET':
            self.throttle_scope = 'agent_listing_read'
        else:
            self.throttle_scope = 'listing_create'
        return super().get_throttles()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ListingCreateSerializer
        return ListingListSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Listing.objects.none()
        return (
            Listing.objects
            .filter(agent=self.request.user)
            .exclude(status=Listing.Status.DELETED)
            .select_related('agent__agent_profile')
            .prefetch_related('images', 'videos')
        )

    def perform_create(self, serializer):
        profile = getattr(self.request.user, 'agent_profile', None)
        is_verified = profile and profile.verified
        forced_status = None if is_verified else Listing.Status.INACTIF
        if forced_status:
            serializer.save(agent=self.request.user, status=forced_status)
        else:
            serializer.save(agent=self.request.user)


class AgentListingDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/agent/listings/{id}/   Détail (avec vidéos complètes + stats)
    PATCH  /api/agent/listings/{id}/   Modifier (activation bloquée sans KYC)
    DELETE /api/agent/listings/{id}/   Supprimer
    """
    serializer_class = AgentListingDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsAgent, IsListingOwner]
    lookup_field = 'pk'

    def get_throttles(self):
        if getattr(self, 'swagger_fake_view', False):
            return super().get_throttles()
        if self.request.method == 'GET':
            self.throttle_scope = 'agent_listing_read'
        else:
            self.throttle_scope = 'agent_listing_mutate'
        return super().get_throttles()

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return ListingCreateSerializer
        return AgentListingDetailSerializer

    def perform_update(self, serializer):
        new_status = serializer.validated_data.get('status')
        if new_status == Listing.Status.ACTIF:
            profile = getattr(self.request.user, 'agent_profile', None)
            if not (profile and profile.verified):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied(
                    "Votre identité doit être vérifiée (KYC) avant de pouvoir publier une annonce."
                )
            listing = self.get_object()
            if listing.images.count() < 1 and listing.videos.count() < 1:
                from rest_framework.exceptions import ValidationError
                raise ValidationError(
                    "Pour publier, votre annonce doit contenir au moins 1 photo ou 1 vidéo."
                )
        serializer.save()

    def perform_destroy(self, instance):
        instance.soft_delete()

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Listing.objects.none()
        return (
            Listing.objects
            .filter(agent=self.request.user)
            .exclude(status=Listing.Status.DELETED)
            .select_related('agent__agent_profile')
            .prefetch_related('images', 'videos', 'reports__user', 'favorited_by__user')
        )


# ═══════════════════════════════════════════════════════════════
# Agent — Renouvellement d'annonce
# ═══════════════════════════════════════════════════════════════


class AgentListingBulkActionView(APIView):
    """
    POST /api/agent/listings/bulk/
    Body: { "ids": [1, 2, 3], "action": "activate" | "deactivate" | "delete" }
    """
    permission_classes = [permissions.IsAuthenticated, IsAgent]
    throttle_scope = 'agent_listing_mutate'

    def post(self, request):
        ids = request.data.get('ids', [])
        action = request.data.get('action', '')

        if not isinstance(ids, list) or not ids:
            return Response({'detail': 'Fournissez une liste d\'ids.'}, status=status.HTTP_400_BAD_REQUEST)

        if action not in ('activate', 'deactivate', 'delete'):
            return Response({'detail': 'Action invalide. Utilisez activate, deactivate ou delete.'}, status=status.HTTP_400_BAD_REQUEST)

        qs = Listing.objects.filter(agent=request.user, pk__in=ids)

        if action == 'activate':
            profile = getattr(request.user, 'agent_profile', None)
            if not (profile and profile.verified):
                return Response(
                    {'detail': 'Vérification KYC requise pour activer des annonces.'},
                    status=status.HTTP_403_FORBIDDEN,
                )
            from django.db.models import Count, Q
            inactif_qs = qs.filter(status__in=[Listing.Status.INACTIF])
            eligible = (
                inactif_qs
                .annotate(
                    img_count=Count('images'),
                    vid_count=Count('videos'),
                )
                .filter(Q(img_count__gte=1) | Q(vid_count__gte=1))
            )
            skipped = inactif_qs.count() - eligible.count()
            count = Listing.objects.filter(pk__in=eligible.values_list('pk', flat=True)).update(status=Listing.Status.ACTIF)
            msg = f'{count} annonce(s) activée(s).'
            if skipped:
                msg += f' {skipped} annonce(s) ignorée(s) (photo ou vidéo manquante).'
            return Response({'detail': msg})
        elif action == 'deactivate':
            count = qs.filter(status=Listing.Status.ACTIF).update(status=Listing.Status.INACTIF)
            return Response({'detail': f'{count} annonce(s) désactivée(s).'})
        elif action == 'delete':
            from django.utils import timezone as tz
            count = qs.exclude(status=Listing.Status.DELETED).update(
                status=Listing.Status.DELETED, deleted_at=tz.now(),
            )
            return Response({'detail': f'{count} annonce(s) supprimée(s).'})


class AgentListingRenewView(APIView):
    """
    POST /api/agent/listings/{pk}/renew/
    Renouvelle une annonce expirée ou inactive pour 7 jours. KYC requis.
    """
    permission_classes = [permissions.IsAuthenticated, IsVerifiedAgent]
    throttle_scope = 'agent_listing_mutate'

    def post(self, request, pk):
        listing = get_object_or_404(Listing, pk=pk, agent=request.user)

        if listing.status == Listing.Status.SUSPENDED:
            return Response(
                {'detail': "Annonce suspendue par modération. Contactez l'administration."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if listing.status == Listing.Status.ACTIF and not listing.is_expired:
            return Response(
                {'detail': f"Annonce encore active ({listing.days_remaining} jours restants)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        listing.renew()
        return Response({
            'detail': "Annonce renouvelée pour 7 jours.",
            'expires_at': listing.expires_at.isoformat(),
            'status': listing.status,
        })


# ═══════════════════════════════════════════════════════════════
# Agent — Upload / suppression d'images
# ═══════════════════════════════════════════════════════════════


class AgentListingImageUploadView(generics.CreateAPIView):
    """
    POST /api/agent/listings/{listing_id}/images/
    Upload d'une image pour une annonce.
    """
    serializer_class = ListingImageUploadSerializer
    permission_classes = [permissions.IsAuthenticated, IsAgent]
    parser_classes = [MultiPartParser, FormParser]

    def get_listing(self):
        return get_object_or_404(
            Listing, pk=self.kwargs['listing_id'], agent=self.request.user,
        )

    def perform_create(self, serializer):
        listing = self.get_listing()
        serializer.save(listing=listing)


class AgentListingImageReorderView(APIView):
    """
    POST /api/agent/listings/{listing_id}/images/reorder/
    Body: { "order": [id1, id2, id3, ...] }
    """
    permission_classes = [permissions.IsAuthenticated, IsAgent]

    def post(self, request, listing_id):
        listing = get_object_or_404(Listing, pk=listing_id, agent=request.user)
        ordered_ids = request.data.get('order', [])
        if not isinstance(ordered_ids, list):
            return Response({'detail': 'Le champ order doit être une liste.'}, status=status.HTTP_400_BAD_REQUEST)

        images = ListingImage.objects.filter(listing=listing)
        image_map = {img.id: img for img in images}

        for idx, img_id in enumerate(ordered_ids):
            if img_id in image_map:
                image_map[img_id].order = idx
                image_map[img_id].save(update_fields=['order'])

        return Response({'detail': 'Ordre mis à jour.'})


class AgentListingImageDeleteView(generics.DestroyAPIView):
    """
    DELETE /api/agent/listings/{listing_id}/images/{pk}/
    Supprimer une image.
    """
    serializer_class = ListingImageSerializer
    permission_classes = [permissions.IsAuthenticated, IsAgent]

    def get_queryset(self):
        return ListingImage.objects.filter(
            listing_id=self.kwargs['listing_id'],
            listing__agent=self.request.user,
        )


# ═══════════════════════════════════════════════════════════════
# Agent — Upload / suppression de vidéos
# ═══════════════════════════════════════════════════════════════


class AgentListingVideoUploadView(generics.CreateAPIView):
    """
    POST /api/agent/listings/{listing_id}/videos/
    Upload d'une vidéo pour une annonce. KYC requis.

    Anti-fraude : calcule le SHA-256 du fichier et vérifie qu'aucune
    vidéo identique n'existe déjà chez cet agent (cross-listings).
    """
    serializer_class = VideoUploadSerializer
    permission_classes = [permissions.IsAuthenticated, IsAgent]
    parser_classes = [MultiPartParser, FormParser]
    throttle_scope = 'video_upload'

    def get_listing(self):
        return get_object_or_404(
            Listing, pk=self.kwargs['listing_id'], agent=self.request.user,
        )

    def perform_create(self, serializer):
        listing = self.get_listing()
        video_file = serializer.validated_data.get('file')

        file_hash = ''
        perceptual_hash = ''
        if video_file:
            try:
                file_hash, perceptual_hash = validate_and_hash_video(
                    self.request.user, video_file,
                    exclude_listing_id=listing.pk,
                )
            except DuplicateVideoError as e:
                from rest_framework.exceptions import ValidationError
                label = 'identique' if e.method == 'exact' else 'visuellement similaire'
                raise ValidationError({
                    'file': f"Vidéo {label} déjà utilisée sur l'annonce "
                            f"« {e.existing_video.listing.title} » "
                            f"(ID #{e.existing_video.listing_id}). "
                            f"Chaque annonce doit avoir sa propre vidéo."
                })

        extra = {
            'listing': listing,
            'file_hash': file_hash,
            'perceptual_hash': perceptual_hash,
        }

        if video_file:
            thumb = generate_thumbnail(video_file)
            if thumb:
                extra['thumbnail'] = thumb

            duration = get_video_duration(video_file)
            if duration:
                extra['duration_sec'] = duration

        video = serializer.save(**extra)

        if not video.thumbnail and video.file:
            from apps.core.tasks import generate_video_thumbnail_task
            generate_video_thumbnail_task.delay(video.pk)


class AgentListingVideoDeleteView(generics.DestroyAPIView):
    """
    DELETE /api/agent/listings/{listing_id}/videos/{pk}/
    Supprimer une vidéo.
    """
    serializer_class = VideoAgentSerializer
    permission_classes = [permissions.IsAuthenticated, IsAgent]

    def get_queryset(self):
        return Video.objects.filter(
            listing_id=self.kwargs['listing_id'],
            listing__agent=self.request.user,
        )


class AgentVideoStreamView(APIView):
    """
    GET /api/agent/videos/{pk}/stream/
    L'agent peut lire ses propres vidéos sans restriction.
    """
    permission_classes = [permissions.IsAuthenticated, IsAgent]

    def get(self, request, pk):
        from django.http import FileResponse
        try:
            video = Video.objects.select_related('listing').get(
                pk=pk, listing__agent=request.user,
            )
        except Video.DoesNotExist:
            return Response(
                {'detail': 'Vidéo introuvable.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not video.file:
            return Response(
                {'detail': 'Fichier vidéo manquant.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        response = FileResponse(video.file.open('rb'), content_type='video/mp4')
        response['Cache-Control'] = 'private, max-age=3600'
        response['Content-Disposition'] = 'inline'
        return response


class VideoHashPreCheckView(APIView):
    """
    POST /api/agent/videos/precheck/
    Pré-vérification SHA-256 côté client AVANT l'upload.
    Body : { "file_hash": "<sha256hex>" }
    Retourne 200 { "duplicate": false } ou 200 { "duplicate": true, "listing_title": ..., "listing_id": ... }
    """
    permission_classes = [permissions.IsAuthenticated, IsAgent]

    def post(self, request):
        file_hash = request.data.get('file_hash', '').strip().lower()
        if not file_hash or len(file_hash) != 64:
            return Response(
                {'detail': 'file_hash SHA-256 (64 hex chars) requis.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        existing = check_hash_exists(request.user, file_hash)
        if existing:
            return Response({
                'duplicate': True,
                'listing_id': existing.listing_id,
                'listing_title': existing.listing.title,
            })
        return Response({'duplicate': False})
