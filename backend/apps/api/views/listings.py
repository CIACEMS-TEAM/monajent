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
from rest_framework import generics, permissions, status, filters
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from apps.listings.models import Listing, ListingImage, Video
from apps.core.permissions import (
    IsAgent, IsVerifiedAgent, IsListingOwner, IsOwnerOrReadOnly,
)
from apps.core.services.video_dedup import validate_and_hash_video, DuplicateVideoError
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


# ═══════════════════════════════════════════════════════════════
# Public — Recherche et détail d'annonces
# ═══════════════════════════════════════════════════════════════


class PublicListingListView(generics.ListAPIView):
    """
    GET /api/listings/
    Liste des annonces actives avec recherche et filtrage.
    Réservé aux utilisateurs authentifiés (clients + agents).
    """
    serializer_class = ListingListSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = 'listing_search'

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
    search_fields = ['title', 'description', 'city', 'neighborhood']
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
    GET /api/listings/{id}/
    Détail d'une annonce active.
    Réservé aux utilisateurs authentifiés (clients + agents).
    """
    serializer_class = ListingDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'pk'

    def get_queryset(self):
        return (
            Listing.objects
            .filter(status=Listing.Status.ACTIF)
            .select_related('agent__agent_profile')
            .prefetch_related('images', 'videos')
        )


# ═══════════════════════════════════════════════════════════════
# Agent — CRUD sur ses propres annonces
# ═══════════════════════════════════════════════════════════════


class AgentListingListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/agent/listings/     Mes annonces (actives + inactives)
    POST /api/agent/listings/     Créer une annonce (tout agent, mais INACTIF si pas KYC)
    """
    serializer_class = ListingListSerializer
    permission_classes = [permissions.IsAuthenticated, IsAgent]
    throttle_scope = 'listing_create'

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
        serializer.save()

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Listing.objects.none()
        return (
            Listing.objects
            .filter(agent=self.request.user)
            .select_related('agent__agent_profile')
            .prefetch_related('images', 'videos')
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
            count = qs.filter(status__in=[Listing.Status.INACTIF]).update(status=Listing.Status.ACTIF)
            return Response({'detail': f'{count} annonce(s) activée(s).'})
        elif action == 'deactivate':
            count = qs.filter(status=Listing.Status.ACTIF).update(status=Listing.Status.INACTIF)
            return Response({'detail': f'{count} annonce(s) désactivée(s).'})
        elif action == 'delete':
            count, _ = qs.delete()
            return Response({'detail': f'{count} annonce(s) supprimée(s).'})


class AgentListingRenewView(APIView):
    """
    POST /api/agent/listings/{pk}/renew/
    Renouvelle une annonce expirée ou inactive pour 7 jours. KYC requis.
    """
    permission_classes = [permissions.IsAuthenticated, IsVerifiedAgent]

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

        # Anti-fraude : hash + déduplication
        file_hash = ''
        if video_file:
            try:
                file_hash = validate_and_hash_video(self.request.user, video_file)
            except DuplicateVideoError as e:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({
                    'file': f"Vidéo identique déjà présente sur l'annonce "
                            f"« {e.existing_video.listing.title} » "
                            f"(ID #{e.existing_video.listing_id})."
                })

        serializer.save(listing=listing, file_hash=file_hash)


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
