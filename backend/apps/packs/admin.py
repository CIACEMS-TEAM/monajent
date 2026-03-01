from django.contrib import admin

from .models import PackPurchase, VirtualKeyUsage


class VirtualKeyUsageInline(admin.TabularInline):
    model = VirtualKeyUsage
    extra = 0
    fields = ('video', 'user', 'agent', 'amount_agent', 'amount_platform', 'created_at')
    readonly_fields = ('created_at',)
    raw_id_fields = ('video', 'user', 'agent')


@admin.register(PackPurchase)
class PackPurchaseAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user_phone', 'amount', 'currency',
        'virtual_total', 'virtual_used', 'remaining_display',
        'has_physical_key', 'is_locked_by_visit', 'created_at',
    )
    list_filter = ('is_locked_by_visit', 'has_physical_key', 'currency', 'created_at')
    search_fields = ('user__phone', 'user__username')
    list_select_related = ('user',)
    raw_id_fields = ('user',)
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    inlines = [VirtualKeyUsageInline]

    fieldsets = (
        ('Client', {
            'fields': ('user',),
        }),
        ('Pack', {
            'fields': ('amount', 'currency', 'virtual_total', 'virtual_used'),
        }),
        ('Clé physique', {
            'fields': ('has_physical_key', 'is_locked_by_visit'),
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
        }),
    )

    @admin.display(description='Tél. client', ordering='user__phone')
    def user_phone(self, obj):
        return obj.user.phone

    @admin.display(description='Restantes')
    def remaining_display(self, obj):
        return f"{obj.virtual_remaining}/{obj.virtual_total}"


@admin.register(VirtualKeyUsage)
class VirtualKeyUsageAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user_phone', 'agent_phone', 'video',
        'amount_agent', 'amount_platform', 'created_at',
    )
    list_filter = ('created_at',)
    search_fields = (
        'user__phone', 'agent__phone',
        'video__listing__title',
    )
    list_select_related = ('user', 'agent', 'video', 'pack')
    raw_id_fields = ('pack', 'video', 'user', 'agent')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

    @admin.display(description='Client', ordering='user__phone')
    def user_phone(self, obj):
        return obj.user.phone

    @admin.display(description='Agent', ordering='agent__phone')
    def agent_phone(self, obj):
        return obj.agent.phone
