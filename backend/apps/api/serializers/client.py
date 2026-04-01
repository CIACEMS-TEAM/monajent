"""
Serializers Client — Monajent
─────────────────────────────
• ClientDashboardSerializer      → résumé consolidé du client
• ClientProfileSerializer        → profil client (lecture/mise à jour)
• FavoriteListingSerializer      → annonce en favori
• SavedSearchSerializer          → recherche sauvegardée
"""

from rest_framework import serializers

from apps.users.models import User, ClientProfile
from apps.favorites.models import FavoriteListing, SavedSearch
from apps.listings.models import Listing


# ═══════════════════════════════════════════════════════════════
# Profil client
# ═══════════════════════════════════════════════════════════════


class ClientProfileReadSerializer(serializers.ModelSerializer):
    """Lecture du profil client complet (user + client_profile)."""
    phone = serializers.CharField(source='user.phone', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    role = serializers.CharField(source='user.role', read_only=True)
    member_since = serializers.DateTimeField(source='user.created_at', read_only=True)

    class Meta:
        model = ClientProfile
        fields = [
            'phone', 'username', 'email', 'role', 'member_since',
            'whatsapp_phone', 'is_phone_verified',
            'language', 'preferences',
            'kyc_status',
        ]
        read_only_fields = fields


class ClientProfileUpdateSerializer(serializers.Serializer):
    """Mise à jour du profil client."""
    username = serializers.CharField(max_length=150, required=False)
    email = serializers.EmailField(required=False, allow_blank=True)
    whatsapp_phone = serializers.CharField(max_length=32, required=False, allow_blank=True)
    language = serializers.ChoiceField(choices=[('fr', 'Français'), ('en', 'English')], required=False)
    preferences = serializers.JSONField(required=False)


# ═══════════════════════════════════════════════════════════════
# Dashboard consolidé
# ═══════════════════════════════════════════════════════════════


class ClientDashboardSerializer(serializers.Serializer):
    """Résumé consolidé du client en un seul appel."""
    # Profil
    phone = serializers.CharField()
    username = serializers.CharField()
    member_since = serializers.DateTimeField()

    # Clés
    total_virtual_remaining = serializers.IntegerField(
        help_text='Total clés virtuelles restantes (tous packs).',
    )
    total_physical_available = serializers.IntegerField(
        help_text='Nombre de clés physiques disponibles.',
    )
    active_packs_count = serializers.IntegerField()

    # Activité
    total_videos_watched = serializers.IntegerField()
    total_visits_requested = serializers.IntegerField()
    visits_in_progress = serializers.IntegerField(
        help_text='Visites REQUESTED ou CONFIRMED.',
    )
    favorites_count = serializers.IntegerField()
    saved_searches_count = serializers.IntegerField()


# ═══════════════════════════════════════════════════════════════
# Favoris
# ═══════════════════════════════════════════════════════════════


class FavoriteListingSerializer(serializers.ModelSerializer):
    """Annonce en favori avec info résumée du listing."""
    listing_id = serializers.IntegerField(source='listing.id', read_only=True)
    listing_slug = serializers.CharField(source='listing.slug', read_only=True)
    listing_title = serializers.CharField(source='listing.title', read_only=True)
    listing_city = serializers.CharField(source='listing.city', read_only=True)
    listing_type = serializers.CharField(source='listing.listing_type', read_only=True)
    listing_price = serializers.DecimalField(
        source='listing.price', max_digits=12, decimal_places=2, read_only=True,
    )
    listing_status = serializers.CharField(source='listing.status', read_only=True)
    thumbnail = serializers.SerializerMethodField()

    class Meta:
        model = FavoriteListing
        fields = [
            'id', 'listing_id', 'listing_slug', 'listing_title', 'listing_city',
            'listing_type', 'listing_price', 'listing_status',
            'thumbnail', 'created_at',
        ]
        read_only_fields = fields

    def get_thumbnail(self, obj):
        first_image = obj.listing.images.first()
        if first_image and first_image.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(first_image.image.url)
            return first_image.image.url
        return None


class FavoriteToggleSerializer(serializers.Serializer):
    """Toggle favori (pas de champs — l'action est dans l'URL)."""
    pass


# ═══════════════════════════════════════════════════════════════
# Recherches sauvegardées
# ═══════════════════════════════════════════════════════════════


class SavedSearchSerializer(serializers.ModelSerializer):
    """CRUD recherche sauvegardée."""

    class Meta:
        model = SavedSearch
        fields = ['id', 'label', 'filters', 'notify', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
