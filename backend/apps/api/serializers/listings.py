"""
Serializers Listings — Monajent
───────────────────────────────
Serializers pour Listing, ListingImage, Video.
Deux jeux : Agent (CRUD complet) et Public (lecture, sans vidéo complète).
"""

from rest_framework import serializers

from apps.listings.models import Listing, ListingImage, Video
from apps.users.models import User, AgentProfile


# ═══════════════════════════════════════════════════════════════
# Serializers imbriqués légers
# ═══════════════════════════════════════════════════════════════


class AgentMiniSerializer(serializers.ModelSerializer):
    """Info agent compacte pour les listes d'annonces."""
    agency_name = serializers.CharField(source='agent_profile.agency_name', default='')
    profile_photo = serializers.ImageField(source='agent_profile.profile_photo', default=None)
    verified = serializers.BooleanField(source='agent_profile.verified', default=False)
    is_partner = serializers.BooleanField(source='agent_profile.is_partner', default=False)

    class Meta:
        model = User
        fields = ['id', 'phone', 'username', 'agency_name', 'profile_photo', 'verified', 'is_partner']
        read_only_fields = fields


class ListingImageSerializer(serializers.ModelSerializer):
    """Serializer pour une photo d'annonce."""

    class Meta:
        model = ListingImage
        fields = ['id', 'image', 'caption', 'order', 'created_at']
        read_only_fields = ['id', 'created_at']


class VideoReadSerializer(serializers.ModelSerializer):
    """
    Serializer vidéo en lecture.
    Inclut le thumbnail (gratuit) mais PAS le fichier vidéo.
    Le fichier est délivré uniquement après consommation d'une clé virtuelle.
    """

    class Meta:
        model = Video
        fields = [
            'id', 'thumbnail', 'duration_sec', 'access_key',
            'views_count', 'created_at',
        ]
        read_only_fields = fields


class VideoAgentSerializer(serializers.ModelSerializer):
    """
    Serializer vidéo pour l'agent propriétaire.
    Génère une URL de streaming signée (token temporaire 1h)
    pour que le tag <video> puisse lire sans header JWT.
    """
    stream_url = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = [
            'id', 'file', 'stream_url', 'thumbnail', 'duration_sec', 'access_key',
            'views_count', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'access_key', 'views_count', 'created_at', 'updated_at']

    def get_stream_url(self, obj) -> str | None:
        from django.core import signing
        request = self.context.get('request')
        token = signing.dumps(
            {'v': obj.pk, 'u': request.user.pk if request else 0},
            salt='video-stream',
        )
        path = f'/api/videos/stream/{token}/'
        if request:
            return request.build_absolute_uri(path)
        return path


# ═══════════════════════════════════════════════════════════════
# Serializers Listing principaux
# ═══════════════════════════════════════════════════════════════


class ListingListSerializer(serializers.ModelSerializer):
    """
    Serializer compact pour les listes d'annonces (recherche publique + agent).
    Inclut l'agent (mini) et la première image comme couverture.
    agent_note est renvoyé uniquement si l'utilisateur est le propriétaire.
    """
    agent = AgentMiniSerializer(read_only=True)
    cover_image = serializers.SerializerMethodField()
    videos_count = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()
    agent_note = serializers.SerializerMethodField()

    class Meta:
        model = Listing
        fields = [
            'id', 'slug', 'title', 'listing_type', 'status',
            'city', 'neighborhood', 'price',
            'rooms', 'bedrooms', 'surface_m2', 'furnishing',
            'deposit_months', 'advance_months', 'agency_fee_months',
            'views_count', 'visits_count', 'favorites_count', 'reports_count',
            'agent', 'cover_image', 'videos_count',
            'published_at', 'expires_at', 'days_remaining',
            'agent_note', 'created_at',
        ]
        read_only_fields = fields

    def get_agent_note(self, obj) -> str | None:
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user == obj.agent:
            return obj.agent_note
        return None

    def get_cover_image(self, obj) -> str | None:
        first = obj.images.first()
        if first and first.image:
            return self.context['request'].build_absolute_uri(first.image.url)
        first_vid = obj.videos.first()
        if first_vid and first_vid.thumbnail:
            return self.context['request'].build_absolute_uri(first_vid.thumbnail.url)
        return None

    def get_videos_count(self, obj) -> int:
        return obj.videos.count()

    def get_days_remaining(self, obj) -> int:
        return obj.days_remaining


class AgentDetailSerializer(serializers.ModelSerializer):
    """Info agent enrichie pour la page détail (inclut coordonnées de contact)."""
    agency_name = serializers.CharField(source='agent_profile.agency_name', default='')
    profile_photo = serializers.ImageField(source='agent_profile.profile_photo', default=None)
    verified = serializers.BooleanField(source='agent_profile.verified', default=False)
    is_partner = serializers.BooleanField(source='agent_profile.is_partner', default=False)
    contact_phone = serializers.CharField(source='agent_profile.contact_phone', default='')
    contact_email = serializers.EmailField(source='agent_profile.contact_email', default='')

    class Meta:
        model = User
        fields = [
            'id', 'phone', 'username', 'agency_name', 'profile_photo', 'verified',
            'is_partner', 'contact_phone', 'contact_email',
        ]
        read_only_fields = fields


class ListingDetailSerializer(serializers.ModelSerializer):
    """
    Serializer détaillé pour la page d'une annonce (public).
    Inclut toutes les images + vidéos (thumbnails uniquement, pas le fichier).
    """
    agent = AgentDetailSerializer(read_only=True)
    images = ListingImageSerializer(many=True, read_only=True)
    videos = VideoReadSerializer(many=True, read_only=True)

    class Meta:
        model = Listing
        fields = [
            'id', 'slug', 'title', 'description', 'listing_type', 'status',
            'city', 'neighborhood', 'address', 'latitude', 'longitude',
            'price', 'rooms', 'bedrooms', 'bathrooms', 'surface_m2',
            'furnishing', 'amenities',
            'deposit_months', 'advance_months', 'agency_fee_months',
            'other_conditions',
            'views_count', 'visits_count', 'favorites_count',
            'agent', 'images', 'videos',
            'created_at', 'updated_at',
        ]
        read_only_fields = fields


class AgentListingDetailSerializer(serializers.ModelSerializer):
    """
    Serializer détaillé pour l'agent propriétaire.
    Inclut les vidéos complètes (avec fichier), toutes les stats,
    les signalements détaillés et les utilisateurs qui ont mis en favori.
    """
    images = ListingImageSerializer(many=True, read_only=True)
    videos = VideoAgentSerializer(many=True, read_only=True)
    days_remaining = serializers.SerializerMethodField()
    reports_detail = serializers.SerializerMethodField()
    favorites_detail = serializers.SerializerMethodField()

    class Meta:
        model = Listing
        fields = [
            'id', 'slug', 'title', 'description', 'listing_type', 'status',
            'city', 'neighborhood', 'address', 'latitude', 'longitude',
            'price', 'rooms', 'bedrooms', 'bathrooms', 'surface_m2',
            'furnishing', 'amenities',
            'deposit_months', 'advance_months', 'agency_fee_months',
            'other_conditions', 'agent_note',
            'views_count', 'visits_count', 'favorites_count', 'reports_count',
            'published_at', 'expires_at', 'days_remaining',
            'images', 'videos',
            'reports_detail', 'favorites_detail',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'views_count', 'visits_count', 'favorites_count', 'reports_count',
            'published_at', 'expires_at', 'created_at', 'updated_at',
        ]

    def get_days_remaining(self, obj) -> int:
        return obj.days_remaining

    def get_reports_detail(self, obj) -> list:
        from apps.listings.models import ListingReport
        reports = (
            ListingReport.objects
            .filter(listing=obj)
            .select_related('user')
            .order_by('-created_at')
        )
        return [
            {
                'id': r.id,
                'reason': r.reason,
                'reason_label': r.get_reason_display(),
                'description': r.description,
                'status': r.status,
                'status_label': r.get_status_display(),
                'user_phone': r.user.phone,
                'user_name': r.user.username or r.user.phone,
                'created_at': r.created_at.isoformat(),
            }
            for r in reports
        ]

    def get_favorites_detail(self, obj) -> list:
        from apps.favorites.models import FavoriteListing
        favs = (
            FavoriteListing.objects
            .filter(listing=obj)
            .select_related('user')
            .order_by('-created_at')
        )
        return [
            {
                'id': f.id,
                'user_phone': f.user.phone,
                'user_name': f.user.username or f.user.phone,
                'created_at': f.created_at.isoformat(),
            }
            for f in favs
        ]


class ListingCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pour la création / modification d'une annonce.
    L'agent est assigné automatiquement par la vue.
    """

    class Meta:
        model = Listing
        fields = [
            'id', 'slug', 'title', 'description', 'listing_type', 'status',
            'city', 'neighborhood', 'address', 'latitude', 'longitude',
            'price', 'rooms', 'bedrooms', 'bathrooms', 'surface_m2',
            'furnishing', 'amenities',
            'deposit_months', 'advance_months', 'agency_fee_months',
            'other_conditions', 'agent_note',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Le prix doit être supérieur à 0.")
        return value

    def validate_amenities(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Les commodités doivent être une liste.")
        if not all(isinstance(item, str) for item in value):
            raise serializers.ValidationError("Chaque commodité doit être une chaîne de caractères.")
        return value


# ═══════════════════════════════════════════════════════════════
# Serializers upload (images + vidéos)
# ═══════════════════════════════════════════════════════════════


class ListingImageUploadSerializer(serializers.ModelSerializer):
    """Upload d'une image pour une annonce."""

    class Meta:
        model = ListingImage
        fields = ['id', 'image', 'caption', 'order', 'created_at']
        read_only_fields = ['id', 'created_at']


class VideoUploadSerializer(serializers.ModelSerializer):
    """Upload d'une vidéo pour une annonce."""

    class Meta:
        model = Video
        fields = ['id', 'file', 'thumbnail', 'duration_sec', 'access_key', 'created_at']
        read_only_fields = ['id', 'access_key', 'created_at']
