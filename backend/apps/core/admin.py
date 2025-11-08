from django.contrib import admin
from .models import SmsDeliveryLog, AuthEventLog


@admin.register(SmsDeliveryLog)
class SmsDeliveryLogAdmin(admin.ModelAdmin):
    list_display = ('message_id', 'address', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('message_id', 'address')
    date_hierarchy = 'created_at'
    readonly_fields = ('message_id', 'address', 'status', 'payload', 'created_at')


@admin.register(AuthEventLog)
class AuthEventLogAdmin(admin.ModelAdmin):
    list_display = ('event', 'user', 'success', 'ip_address', 'created_at')
    list_filter = ('success', 'event')
    search_fields = ('event', 'user__phone', 'phone_hash', 'ip_address', 'user__username', 'user__email')
    date_hierarchy = 'created_at'
    readonly_fields = ('event', 'user', 'phone_hash', 'ip_address', 'user_agent', 'success', 'metadata', 'created_at')
