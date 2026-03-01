from django.contrib import admin

from .models import FavoriteListing, SavedSearch


@admin.register(FavoriteListing)
class FavoriteListingAdmin(admin.ModelAdmin):
    list_display = ('id', 'client_phone', 'listing_title', 'created_at')
    list_filter = ('created_at',)
    search_fields = (
        'user__phone', 'user__username',
        'listing__title', 'listing__city',
    )
    list_select_related = ('user', 'listing')
    raw_id_fields = ('user', 'listing')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

    @admin.display(description='Client', ordering='user__phone')
    def client_phone(self, obj):
        return obj.user.phone

    @admin.display(description='Annonce', ordering='listing__title')
    def listing_title(self, obj):
        return obj.listing.title


@admin.register(SavedSearch)
class SavedSearchAdmin(admin.ModelAdmin):
    list_display = ('id', 'client_phone', 'label', 'notify', 'created_at')
    list_filter = ('notify', 'created_at')
    search_fields = ('user__phone', 'user__username', 'label')
    list_select_related = ('user',)
    raw_id_fields = ('user',)
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)

    @admin.display(description='Client', ordering='user__phone')
    def client_phone(self, obj):
        return obj.user.phone
