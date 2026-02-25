"""
Vues Client — Monajent
──────────────────────
Profil & Dashboard :
    GET    /api/client/dashboard/           → Résumé consolidé
    GET    /api/client/profile/             → Profil complet
    PATCH  /api/client/profile/             → Modifier le profil

Favoris :
    GET    /api/client/favorites/           → Liste des favoris
    POST   /api/client/favorites/{id}/      → Ajouter en favori
    DELETE /api/client/favorites/{id}/      → Retirer des favoris

Recherches sauvegardées :
    GET    /api/client/saved-searches/      → Liste
    POST   /api/client/saved-searches/      → Créer
    GET    /api/client/saved-searches/{id}/ → Détail
    PUT    /api/client/saved-searches/{id}/ → Modifier
    DELETE /api/client/saved-searches/{id}/ → Supprimer
"""

from django.db.models import Q, Sum, F
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import ClientProfile
from apps.packs.models import PackPurchase, VirtualKeyUsage
from apps.visits.models import VisitRequest
from apps.favorites.models import FavoriteListing, SavedSearch
from apps.listings.models import Listing
from apps.core.permissions import IsClient
from apps.api.serializers.client import (
    ClientProfileReadSerializer,
    ClientProfileUpdateSerializer,
    ClientDashboardSerializer,
    FavoriteListingSerializer,
    SavedSearchSerializer,
)


# ═══════════════════════════════════════════════════════════════
# Dashboard consolidé
# ═══════════════════════════════════════════════════════════════


class ClientDashboardView(APIView):
    """
    GET /api/client/dashboard/
    Résumé complet en un seul appel :
    clés restantes, activité, favoris, recherches.
    """
    permission_classes = [IsAuthenticated, IsClient]

    def get(self, request):
        user = request.user

        # Clés restantes (tous packs non verrouillés)
        packs = PackPurchase.objects.filter(user=user)
        active_packs = packs.filter(is_locked_by_visit=False)
        total_virtual = sum(
            max(p.virtual_total - p.virtual_used, 0) for p in active_packs
        )
        total_physical = packs.filter(
            has_physical_key=True, is_locked_by_visit=False,
        ).count()

        data = {
            'phone': user.phone,
            'username': user.username or '',
            'member_since': user.created_at,
            'total_virtual_remaining': total_virtual,
            'total_physical_available': total_physical,
            'active_packs_count': active_packs.count(),
            'total_videos_watched': VirtualKeyUsage.objects.filter(user=user).count(),
            'total_visits_requested': VisitRequest.objects.filter(user=user).count(),
            'visits_in_progress': VisitRequest.objects.filter(
                user=user,
                status__in=[VisitRequest.Status.REQUESTED, VisitRequest.Status.CONFIRMED],
            ).count(),
            'favorites_count': FavoriteListing.objects.filter(user=user).count(),
            'saved_searches_count': SavedSearch.objects.filter(user=user).count(),
        }

        serializer = ClientDashboardSerializer(data)
        return Response(serializer.data)


# ═══════════════════════════════════════════════════════════════
# Profil client
# ═══════════════════════════════════════════════════════════════


class ClientProfileView(APIView):
    """
    GET   /api/client/profile/  → Profil complet
    PATCH /api/client/profile/  → Mise à jour partielle
    """
    permission_classes = [IsAuthenticated, IsClient]

    def get(self, request):
        profile, _ = ClientProfile.objects.get_or_create(user=request.user)
        serializer = ClientProfileReadSerializer(profile)
        return Response(serializer.data)

    def patch(self, request):
        ser = ClientProfileUpdateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        user = request.user
        profile, _ = ClientProfile.objects.get_or_create(user=user)

        # Champs User
        if 'username' in data:
            user.username = data['username']
        if 'email' in data:
            user.email = data['email'] or None
        user.save(update_fields=['username', 'email', 'updated_at'])

        # Champs ClientProfile
        updated_fields = []
        if 'whatsapp_phone' in data:
            profile.whatsapp_phone = data['whatsapp_phone']
            updated_fields.append('whatsapp_phone')
        if 'language' in data:
            profile.language = data['language']
            updated_fields.append('language')
        if 'preferences' in data:
            profile.preferences = data['preferences']
            updated_fields.append('preferences')
        if updated_fields:
            updated_fields.append('updated_at')
            profile.save(update_fields=updated_fields)

        return Response(ClientProfileReadSerializer(profile).data)


# ═══════════════════════════════════════════════════════════════
# Favoris
# ═══════════════════════════════════════════════════════════════


class ClientFavoriteListView(generics.ListAPIView):
    """
    GET /api/client/favorites/
    Liste des annonces en favori.
    """
    permission_classes = [IsAuthenticated, IsClient]
    serializer_class = FavoriteListingSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return FavoriteListing.objects.none()
        return (
            FavoriteListing.objects
            .filter(user=self.request.user)
            .select_related('listing')
            .prefetch_related('listing__images')
            .order_by('-created_at')
        )


class ClientFavoriteToggleView(APIView):
    """
    POST   /api/client/favorites/{listing_id}/  → Ajouter
    DELETE /api/client/favorites/{listing_id}/  → Retirer
    """
    permission_classes = [IsAuthenticated, IsClient]

    def post(self, request, listing_id):
        listing = get_object_or_404(Listing, pk=listing_id)
        fav, created = FavoriteListing.objects.get_or_create(
            user=request.user, listing=listing,
        )
        if created:
            return Response(
                {'detail': "Ajouté aux favoris.", 'favorited': True},
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {'detail': "Déjà en favori.", 'favorited': True},
            status=status.HTTP_200_OK,
        )

    def delete(self, request, listing_id):
        deleted, _ = FavoriteListing.objects.filter(
            user=request.user, listing_id=listing_id,
        ).delete()
        if deleted:
            return Response(
                {'detail': "Retiré des favoris.", 'favorited': False},
            )
        return Response(
            {'detail': "Cette annonce n'était pas en favori.", 'favorited': False},
        )


# ═══════════════════════════════════════════════════════════════
# Recherches sauvegardées
# ═══════════════════════════════════════════════════════════════


class ClientSavedSearchListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/client/saved-searches/  → Mes recherches
    POST /api/client/saved-searches/  → Sauvegarder une recherche
    """
    permission_classes = [IsAuthenticated, IsClient]
    serializer_class = SavedSearchSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return SavedSearch.objects.none()
        return SavedSearch.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ClientSavedSearchDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET/PUT/PATCH/DELETE /api/client/saved-searches/{id}/
    """
    permission_classes = [IsAuthenticated, IsClient]
    serializer_class = SavedSearchSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return SavedSearch.objects.none()
        return SavedSearch.objects.filter(user=self.request.user)
