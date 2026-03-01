from django.contrib import admin

from .models import VisitRequest, AgentAvailabilitySlot


@admin.register(AgentAvailabilitySlot)
class AgentAvailabilitySlotAdmin(admin.ModelAdmin):
    list_display = ('id', 'agent_phone', 'day_of_week', 'start_time', 'end_time', 'is_active')
    list_filter = ('day_of_week', 'is_active')
    list_select_related = ('agent',)
    raw_id_fields = ('agent',)
    search_fields = ('agent__phone',)
    ordering = ('agent', 'day_of_week', 'start_time')

    @admin.display(description='Agent', ordering='agent__phone')
    def agent_phone(self, obj):
        return obj.agent.phone


@admin.register(VisitRequest)
class VisitRequestAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'client_phone', 'listing_title', 'status',
        'verification_code', 'slot_label',
        'scheduled_at', 'code_validated_at', 'created_at',
    )
    list_filter = ('status', 'created_at', 'scheduled_at')
    search_fields = (
        'user__phone', 'user__username',
        'listing__title', 'listing__city',
        'verification_code',
    )
    list_select_related = ('user', 'listing', 'pack', 'slot')
    raw_id_fields = ('user', 'listing', 'pack', 'slot')
    readonly_fields = (
        'verification_code', 'code_validated_at',
        'consumed_physical_key_at', 'response_deadline',
        'created_at', 'updated_at',
    )
    ordering = ('-created_at',)

    fieldsets = (
        ('Demande', {
            'fields': ('user', 'listing', 'pack', 'slot', 'status'),
        }),
        ('Planification', {
            'fields': ('scheduled_at', 'response_deadline', 'consumed_physical_key_at'),
        }),
        ('Vérification', {
            'fields': ('verification_code', 'code_validated_at'),
        }),
        ('Notes', {
            'fields': ('client_note', 'agent_note'),
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
        }),
    )

    @admin.display(description='Client', ordering='user__phone')
    def client_phone(self, obj):
        return obj.user.phone

    @admin.display(description='Annonce', ordering='listing__title')
    def listing_title(self, obj):
        return obj.listing.title

    @admin.display(description='Créneau')
    def slot_label(self, obj):
        return str(obj.slot) if obj.slot else '—'
