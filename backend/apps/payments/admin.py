from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'client_phone', 'provider', 'tx_ref', 'provider_tx_id',
        'status', 'amount', 'currency', 'has_pack', 'created_at',
    )
    list_filter = ('status', 'provider', 'currency', 'created_at')
    search_fields = ('user__phone', 'user__username', 'tx_ref', 'provider_tx_id')
    list_select_related = ('user', 'pack')
    raw_id_fields = ('user', 'pack')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)

    fieldsets = (
        ('Client & Pack', {
            'fields': ('user', 'pack'),
        }),
        ('Paiement', {
            'fields': (
                'provider', 'tx_ref', 'provider_tx_id',
                'status', 'amount', 'currency', 'checkout_url',
            ),
        }),
        ('Métadonnées', {
            'fields': ('provider_metadata',),
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
        }),
    )

    @admin.display(description='Client', ordering='user__phone')
    def client_phone(self, obj):
        return obj.user.phone

    @admin.display(description='Pack créé', boolean=True)
    def has_pack(self, obj):
        return obj.pack_id is not None
