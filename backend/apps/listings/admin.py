from django.contrib import admin
from django.utils.html import format_html

from .models import Listing, ListingImage, Video, ListingReport


class ListingImageInline(admin.TabularInline):
    model = ListingImage
    extra = 1
    fields = ('image', 'caption', 'order')
    ordering = ('order',)


class VideoInline(admin.TabularInline):
    model = Video
    extra = 0
    fields = ('file', 'thumbnail', 'duration_sec', 'access_key', 'file_hash', 'views_count', 'created_at')
    readonly_fields = ('access_key', 'file_hash', 'views_count', 'created_at')


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'title', 'agent_phone', 'listing_type', 'status',
        'city', 'neighborhood', 'price', 'rooms',
        'views_count', 'favorites_count', 'reports_count',
        'expires_at', 'created_at',
    )
    list_filter = ('status', 'listing_type', 'furnishing', 'city', 'created_at')
    search_fields = (
        'title', 'description', 'city', 'neighborhood',
        'agent__phone', 'agent__username',
    )
    list_select_related = ('agent',)
    raw_id_fields = ('agent',)
    readonly_fields = ('views_count', 'favorites_count', 'reports_count', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    inlines = [ListingImageInline, VideoInline]

    fieldsets = (
        ('Annonce', {
            'fields': ('agent', 'title', 'description', 'listing_type', 'status'),
        }),
        ('Localisation', {
            'fields': ('city', 'neighborhood', 'address', 'latitude', 'longitude'),
        }),
        ('Caractéristiques', {
            'fields': ('price', 'rooms', 'bedrooms', 'bathrooms', 'surface_m2', 'furnishing', 'amenities'),
        }),
        ('Cycle de vie', {
            'fields': ('published_at', 'expires_at'),
        }),
        ('Compteurs', {
            'fields': ('views_count', 'favorites_count', 'reports_count'),
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
        }),
    )

    @admin.display(description='Tél. agent', ordering='agent__phone')
    def agent_phone(self, obj):
        return obj.agent.phone


@admin.register(ListingImage)
class ListingImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'listing_title', 'caption', 'order', 'created_at')
    list_select_related = ('listing',)
    raw_id_fields = ('listing',)
    search_fields = ('listing__title', 'caption')
    ordering = ('listing', 'order')

    @admin.display(description='Annonce', ordering='listing__title')
    def listing_title(self, obj):
        return obj.listing.title


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('id', 'listing_title', 'duration_sec', 'views_count', 'access_key_short', 'hash_short', 'created_at')
    list_select_related = ('listing',)
    raw_id_fields = ('listing',)
    search_fields = ('listing__title', 'listing__agent__phone', 'file_hash')
    readonly_fields = ('access_key', 'file_hash', 'views_count', 'created_at', 'updated_at')
    ordering = ('-created_at',)

    @admin.display(description='Annonce', ordering='listing__title')
    def listing_title(self, obj):
        return obj.listing.title

    @admin.display(description='Clé accès')
    def access_key_short(self, obj):
        return str(obj.access_key)[:8] + '…'

    @admin.display(description='Hash')
    def hash_short(self, obj):
        return (obj.file_hash[:12] + '…') if obj.file_hash else '—'


@admin.register(ListingReport)
class ListingReportAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'reporter_phone', 'listing_title', 'reason',
        'status', 'created_at', 'reviewed_at',
    )
    list_filter = ('status', 'reason', 'created_at')
    search_fields = ('user__phone', 'listing__title', 'description')
    list_select_related = ('user', 'listing')
    raw_id_fields = ('user', 'listing')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

    fieldsets = (
        ('Signalement', {
            'fields': ('user', 'listing', 'reason', 'description'),
        }),
        ('Modération', {
            'fields': ('status', 'admin_note', 'reviewed_at'),
        }),
        ('Dates', {
            'fields': ('created_at',),
        }),
    )

    @admin.display(description='Signalé par', ordering='user__phone')
    def reporter_phone(self, obj):
        return obj.user.phone

    @admin.display(description='Annonce', ordering='listing__title')
    def listing_title(self, obj):
        return obj.listing.title
