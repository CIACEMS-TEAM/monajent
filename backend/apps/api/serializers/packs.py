"""
Serializers Packs & Visionnage — Monajent
─────────────────────────────────────────
Serializers pour PackPurchase, VirtualKeyUsage, et le flux de visionnage.
"""

from rest_framework import serializers

from apps.packs.models import PackPurchase, VirtualKeyUsage
from apps.listings.models import Video


# ═══════════════════════════════════════════════════════════════
# Pack
# ═══════════════════════════════════════════════════════════════


class PackPurchaseSerializer(serializers.ModelSerializer):
    """Pack du client avec clés restantes."""
    virtual_remaining = serializers.IntegerField(read_only=True)
    is_exhausted = serializers.BooleanField(read_only=True)

    class Meta:
        model = PackPurchase
        fields = [
            'id', 'amount', 'currency',
            'virtual_total', 'virtual_used', 'virtual_remaining',
            'has_physical_key', 'is_locked_by_visit', 'is_exhausted',
            'created_at',
        ]
        read_only_fields = fields


class PackPurchaseCreateSerializer(serializers.Serializer):
    """
    Création d'un pack (simplifié pour le dev).
    En production, le pack sera créé automatiquement après paiement validé.
    """
    pass  # Aucun champ requis : le pack standard est créé avec les valeurs par défaut


# ═══════════════════════════════════════════════════════════════
# Visionnage (Watch)
# ═══════════════════════════════════════════════════════════════


class WatchVideoSerializer(serializers.Serializer):
    """
    Demande de visionnage d'une vidéo.
    Le client envoie l'access_key de la vidéo ; le backend :
    - Trouve le pack actif
    - Consomme 1 clé virtuelle
    - Crédite l'agent + la plateforme
    - Retourne l'URL du fichier vidéo
    """
    access_key = serializers.UUIDField(
        help_text="Identifiant unique de la vidéo (access_key).",
    )


class WatchVideoResponseSerializer(serializers.Serializer):
    """Réponse après visionnage réussi."""
    video_url = serializers.URLField(help_text="URL du fichier vidéo (signée en prod).")
    video_id = serializers.IntegerField()
    listing_id = serializers.IntegerField()
    listing_title = serializers.CharField()
    pack_remaining = serializers.IntegerField(help_text="Clés virtuelles restantes sur le pack.")
    already_watched = serializers.BooleanField(
        help_text="True si le client avait déjà vu cette vidéo (pas de clé consommée).",
    )


# ═══════════════════════════════════════════════════════════════
# Historique de visionnage
# ═══════════════════════════════════════════════════════════════


class VirtualKeyUsageSerializer(serializers.ModelSerializer):
    """Historique d'un visionnage."""
    video_thumbnail = serializers.ImageField(source='video.thumbnail', read_only=True)
    video_duration = serializers.IntegerField(source='video.duration_sec', read_only=True)
    listing_id = serializers.IntegerField(source='video.listing_id', read_only=True, default=None)
    listing_title = serializers.CharField(source='video.listing.title', read_only=True, default='')
    listing_city = serializers.CharField(source='video.listing.city', read_only=True, default='')
    listing_status = serializers.CharField(source='video.listing.status', read_only=True, default='')
    agent_name = serializers.SerializerMethodField()
    agent_phone = serializers.CharField(source='agent.phone', read_only=True)

    class Meta:
        model = VirtualKeyUsage
        fields = [
            'id', 'video_id', 'listing_id', 'listing_title', 'listing_city',
            'listing_status', 'video_thumbnail', 'video_duration',
            'agent_name', 'agent_phone', 'amount_agent', 'amount_platform',
            'created_at',
        ]
        read_only_fields = fields

    def get_agent_name(self, obj) -> str:
        agent = obj.agent
        if hasattr(agent, 'agent_profile') and agent.agent_profile:
            p = agent.agent_profile
            return p.agency_name or p.contact_phone or agent.phone
        return agent.username or agent.phone
