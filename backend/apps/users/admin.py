from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.hashers import identify_hasher

from .models import User, ClientProfile, AgentProfile, AgentDocument


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'phone', 'username', 'email', 'role', 'is_active', 'is_staff', 'created_at')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('phone', 'username', 'email')
    ordering = ('-created_at',)
    readonly_fields = ('last_login', 'created_at', 'updated_at')
    fieldsets = (
        (_('Identité'), {
            'fields': ('phone', 'username', 'email', 'role'),
        }),
        (_('Sécurité'), {
            'fields': ('password', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Meta'), {
            'fields': ('last_login', 'created_at', 'updated_at'),
        }),
    )

    def save_model(self, request, obj, form, change):
        """
        Si un mot de passe en clair est saisi dans le champ `password`,
        le convertir en hash sécurisé avant sauvegarde.
        """
        raw_password = form.cleaned_data.get('password')
        if raw_password:
            try:
                # Si déjà un hash valide reconnu par Django, ne rien faire
                identify_hasher(raw_password)
            except Exception:
                # Sinon, on hash le mot de passe
                obj.set_password(raw_password)
        super().save_model(request, obj, form, change)


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
