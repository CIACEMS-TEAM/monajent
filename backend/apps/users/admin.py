from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User, ClientProfile, AgentProfile, AgentDocument


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ('-created_at',)
    list_display = ('phone', 'username', 'email', 'role', 'is_active', 'is_staff', 'created_at')
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('phone', 'username', 'email')

    fieldsets = (
        (None, {'fields': ('phone', 'username', 'email', 'password')}),
        (_('Rôles et statuts'), {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('OTP'), {'fields': ('otp_code', 'otp_expires_at')}),
        (_('Dates'), {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'username', 'email', 'role', 'password1', 'password2', 'is_staff', 'is_superuser'),
        }),
    )
    readonly_fields = ('created_at', 'updated_at', 'last_login')

    # Groupes et permissions
    filter_horizontal = ('groups', 'user_permissions',)


@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'whatsapp_phone', 'is_phone_verified', 'kyc_status', 'created_at')
    search_fields = ('user__email', 'user__phone', 'whatsapp_phone', 'id_number')
    list_filter = ('is_phone_verified', 'kyc_status')


@admin.register(AgentProfile)
class AgentProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'agency_name', 'verified', 'national_id_number', 'created_at'
    )
    search_fields = ('user__email', 'user__phone', 'agency_name', 'national_id_number')
    list_filter = ('verified',)


@admin.register(AgentDocument)
class AgentDocumentAdmin(admin.ModelAdmin):
    list_display = ('agent_profile', 'label', 'uploaded_at')
    search_fields = ('agent_profile__user__phone', 'agent_profile__user__email', 'label')

