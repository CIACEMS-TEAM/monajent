from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User, ClientProfile, AgentProfile, AgentDocument, Notification


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('id', 'phone', 'username', 'email', 'role', 'is_active', 'is_staff', 'created_at')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('phone', 'username', 'email')
    ordering = ('-created_at',)
    readonly_fields = ('last_login', 'created_at', 'updated_at')

    fieldsets = (
        (_('Identité'), {
            'fields': ('phone', 'username', 'email', 'role'),
        }),
        (_('Mot de passe'), {
            'fields': ('password',),
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Meta'), {
            'fields': ('last_login', 'created_at', 'updated_at'),
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'role', 'password1', 'password2'),
        }),
    )


@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'whatsapp_phone', 'is_phone_verified', 'kyc_status', 'created_at')
    list_filter = ('is_phone_verified', 'kyc_status', 'language')
    search_fields = ('user__phone', 'user__username', 'whatsapp_phone', 'id_number', 'referral_code')
    ordering = ('-created_at',)


@admin.register(AgentProfile)
class AgentProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'agency_name', 'verified', 'created_at')
    list_filter = ('verified',)
    search_fields = ('user__phone', 'user__username', 'agency_name', 'national_id_number')
    ordering = ('-created_at',)


@admin.register(AgentDocument)
class AgentDocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'agent_profile', 'label', 'uploaded_at')
    search_fields = ('agent_profile__user__phone', 'agent_profile__user__username', 'label')
    ordering = ('-uploaded_at',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'category', 'title', 'is_read', 'created_at')
    list_filter = ('category', 'is_read')
    search_fields = ('user__phone', 'title', 'message')
    ordering = ('-created_at',)
