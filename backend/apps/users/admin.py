from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm as BaseUserChangeForm
from django.utils.translation import gettext_lazy as _

from .models import User, ClientProfile, AgentProfile, AgentDocument, LegalConsent, Notification


class CustomUserChangeForm(BaseUserChangeForm):
    """username est nullable sur notre modèle ; empêche len(None) dans UsernameField."""

    def clean_username(self):
        return self.cleaned_data.get('username') or None


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = CustomUserChangeForm
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
    list_display = ('id', 'user', 'agency_name', 'verified', 'is_partner', 'kyc_status', 'created_at')
    list_filter = ('verified', 'is_partner', 'kyc_status')
    search_fields = ('user__phone', 'user__username', 'agency_name', 'national_id_number')
    ordering = ('-created_at',)
    actions = ['mark_as_partner', 'remove_partner']

    @admin.action(description='Marquer comme partenaire')
    def mark_as_partner(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(is_partner=False).update(
            is_partner=True, partner_since=timezone.now(),
        )
        self.message_user(request, f'{updated} agent(s) marqué(s) comme partenaire(s).')

    @admin.action(description='Retirer le statut partenaire')
    def remove_partner(self, request, queryset):
        updated = queryset.filter(is_partner=True).update(
            is_partner=False, partner_since=None,
        )
        self.message_user(request, f'{updated} agent(s) retiré(s) du statut partenaire.')


@admin.register(AgentDocument)
class AgentDocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'agent_profile', 'label', 'uploaded_at')
    search_fields = ('agent_profile__user__phone', 'agent_profile__user__username', 'label')
    ordering = ('-uploaded_at',)


@admin.register(LegalConsent)
class LegalConsentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'document_type', 'document_version', 'ip_address', 'accepted_at')
    list_filter = ('document_type', 'document_version')
    search_fields = ('user__phone', 'user__username', 'ip_address')
    ordering = ('-accepted_at',)
    readonly_fields = ('user', 'document_type', 'document_version', 'ip_address', 'user_agent', 'accepted_at')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'category', 'title', 'link', 'is_read', 'created_at')
    list_filter = ('category', 'is_read')
    search_fields = ('user__phone', 'title', 'message')
    ordering = ('-created_at',)
