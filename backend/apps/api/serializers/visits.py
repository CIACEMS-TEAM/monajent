"""
Serializers Visites, Disponibilités & Signalements — Monajent
─────────────────────────────────────────────────────────────
"""

from rest_framework import serializers

from apps.visits.models import VisitRequest, AgentAvailabilitySlot, AgentDateSlot
from apps.listings.models import ListingReport


# ═══════════════════════════════════════════════════════════════
# Disponibilités agent
# ═══════════════════════════════════════════════════════════════


class AgentAvailabilitySlotSerializer(serializers.ModelSerializer):
    """CRUD des créneaux de disponibilité de l'agent."""
    day_label = serializers.CharField(source='get_day_of_week_display', read_only=True)

    class Meta:
        model = AgentAvailabilitySlot
        fields = [
            'id', 'day_of_week', 'day_label',
            'start_time', 'end_time', 'is_active',
        ]
        read_only_fields = ['id', 'day_label']


class AgentAvailabilityPublicSerializer(serializers.ModelSerializer):
    """Vue publique des créneaux (visible par les clients)."""
    day_label = serializers.CharField(source='get_day_of_week_display', read_only=True)

    class Meta:
        model = AgentAvailabilitySlot
        fields = ['id', 'day_of_week', 'day_label', 'start_time', 'end_time']
        read_only_fields = fields


class AgentDateSlotSerializer(serializers.ModelSerializer):
    """CRUD des créneaux ponctuels (agenda) de l'agent."""
    class Meta:
        model = AgentDateSlot
        fields = ['id', 'date', 'start_time', 'end_time', 'is_active', 'note']
        read_only_fields = ['id']


class AgentDateSlotPublicSerializer(serializers.ModelSerializer):
    """Vue publique des créneaux ponctuels (visible par les clients)."""
    class Meta:
        model = AgentDateSlot
        fields = ['id', 'date', 'start_time', 'end_time', 'note']
        read_only_fields = fields


# ═══════════════════════════════════════════════════════════════
# Visite physique
# ═══════════════════════════════════════════════════════════════


class VisitRequestClientSerializer(serializers.ModelSerializer):
    """Vue client : inclut le code de vérification (visible par le client)."""
    listing_title = serializers.CharField(source='listing.title', read_only=True)
    listing_city = serializers.CharField(source='listing.city', read_only=True)
    agent_phone = serializers.CharField(source='listing.agent.phone', read_only=True)
    slot_label = serializers.SerializerMethodField()
    meeting_map_url = serializers.SerializerMethodField()

    class Meta:
        model = VisitRequest
        fields = [
            'id', 'listing_id', 'listing_title', 'listing_city',
            'agent_phone', 'status',
            'verification_code', 'virtual_key_consumed',
            'slot_id', 'slot_label', 'scheduled_at', 'response_deadline',
            'client_note', 'agent_note', 'cancel_reason',
            'meeting_address', 'meeting_latitude', 'meeting_longitude',
            'meeting_map_url',
            'created_at',
        ]
        read_only_fields = [
            'id', 'listing_title', 'listing_city', 'agent_phone',
            'status', 'verification_code', 'virtual_key_consumed',
            'slot_label', 'scheduled_at', 'response_deadline',
            'agent_note', 'cancel_reason', 'meeting_address',
            'meeting_latitude', 'meeting_longitude', 'meeting_map_url',
            'created_at',
        ]

    def get_slot_label(self, obj):
        if obj.slot:
            return str(obj.slot)
        return None

    def get_meeting_map_url(self, obj) -> str | None:
        if obj.meeting_latitude and obj.meeting_longitude:
            return f"https://www.google.com/maps?q={obj.meeting_latitude},{obj.meeting_longitude}"
        return None


class VisitRequestAgentSerializer(serializers.ModelSerializer):
    """Vue agent : PAS de code visible (l'agent doit le recevoir du client)."""
    client_phone = serializers.CharField(source='user.phone', read_only=True)
    listing_title = serializers.CharField(source='listing.title', read_only=True)
    is_deadline_passed = serializers.BooleanField(read_only=True)
    slot_label = serializers.SerializerMethodField()
    meeting_map_url = serializers.SerializerMethodField()

    class Meta:
        model = VisitRequest
        fields = [
            'id', 'listing_id', 'listing_title',
            'client_phone', 'status',
            'slot_id', 'slot_label', 'scheduled_at',
            'response_deadline', 'is_deadline_passed',
            'client_note', 'agent_note', 'cancel_reason',
            'meeting_address', 'meeting_latitude', 'meeting_longitude',
            'meeting_map_url',
            'created_at',
        ]
        read_only_fields = fields

    def get_slot_label(self, obj):
        if obj.slot:
            return str(obj.slot)
        return None

    def get_meeting_map_url(self, obj) -> str | None:
        if obj.meeting_latitude and obj.meeting_longitude:
            return f"https://www.google.com/maps?q={obj.meeting_latitude},{obj.meeting_longitude}"
        return None


class VisitRequestCreateSerializer(serializers.Serializer):
    """
    Demande de visite physique par le client.
    Le client choisit un créneau parmi les disponibilités de l'agent.
    """
    listing_id = serializers.IntegerField()
    slot_id = serializers.IntegerField(
        help_text="ID du créneau AgentAvailabilitySlot choisi par le client.",
    )
    scheduled_at = serializers.DateTimeField(
        required=False,
        help_text="Date/heure souhaitée (doit correspondre au créneau choisi).",
    )
    client_note = serializers.CharField(required=False, allow_blank=True, default='')


class VisitConfirmSerializer(serializers.Serializer):
    """Agent confirme la visite (peut ajuster la date et indiquer le lieu de RDV)."""
    scheduled_at = serializers.DateTimeField(required=False)
    agent_note = serializers.CharField(required=False, allow_blank=True, default='')
    meeting_address = serializers.CharField(required=False, allow_blank=True, default='')
    meeting_latitude = serializers.DecimalField(
        max_digits=9, decimal_places=6, required=False, allow_null=True, default=None,
    )
    meeting_longitude = serializers.DecimalField(
        max_digits=9, decimal_places=6, required=False, allow_null=True, default=None,
    )


class VisitValidateCodeSerializer(serializers.Serializer):
    """Agent entre le code communiqué par le client (5 caractères)."""
    code = serializers.CharField(max_length=5, min_length=5)


# ═══════════════════════════════════════════════════════════════
# Signalement
# ═══════════════════════════════════════════════════════════════


class ListingReportCreateSerializer(serializers.ModelSerializer):
    """Signalement d'une annonce par un client."""

    class Meta:
        model = ListingReport
        fields = ['listing', 'reason', 'description']


class ListingReportSerializer(serializers.ModelSerializer):
    """Détail d'un signalement (lecture)."""
    listing_title = serializers.CharField(source='listing.title', read_only=True)

    class Meta:
        model = ListingReport
        fields = [
            'id', 'listing_id', 'listing_title',
            'reason', 'description', 'status',
            'created_at',
        ]
        read_only_fields = fields
