from django.contrib import admin
from django.utils import timezone

from .models import Wallet, WalletEntry, PlatformRevenue, WithdrawalRequest
from apps.core.services.withdrawal import (
    approve_withdrawal,
    reject_withdrawal,
    WithdrawalAlreadyProcessedError,
)


# ═══════════════════════════════════════════════════════════════
# Wallet
# ═══════════════════════════════════════════════════════════════


class WalletEntryInline(admin.TabularInline):
    model = WalletEntry
    extra = 0
    fields = ('entry_type', 'source', 'amount', 'label', 'withdrawal_method', 'created_at')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'agent_phone', 'balance', 'total_earned',
        'total_withdrawn', 'can_withdraw_display', 'has_pin_display',
        'pending_count', 'updated_at',
    )
    list_filter = ('created_at',)
    search_fields = ('agent__phone', 'agent__username')
    list_select_related = ('agent',)
    raw_id_fields = ('agent',)
    readonly_fields = ('balance', 'total_earned', 'total_withdrawn', 'created_at', 'updated_at')
    ordering = ('-updated_at',)
    inlines = [WalletEntryInline]

    fieldsets = (
        ('Agent', {
            'fields': ('agent',),
        }),
        ('Solde', {
            'fields': ('balance', 'total_earned', 'total_withdrawn'),
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
        }),
    )

    @admin.display(description='Tél. agent', ordering='agent__phone')
    def agent_phone(self, obj):
        return obj.agent.phone

    @admin.display(description='Retrait possible', boolean=True)
    def can_withdraw_display(self, obj):
        return obj.can_withdraw

    @admin.display(description='PIN', boolean=True)
    def has_pin_display(self, obj):
        return obj.has_pin

    @admin.display(description='En attente')
    def pending_count(self, obj):
        count = obj.withdrawals.filter(status=WithdrawalRequest.Status.PENDING).count()
        return f'{count} demande(s)' if count else '—'


# ═══════════════════════════════════════════════════════════════
# WalletEntry
# ═══════════════════════════════════════════════════════════════


@admin.register(WalletEntry)
class WalletEntryAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'agent_phone', 'entry_type', 'source', 'amount', 'label',
        'withdrawal_method', 'created_at',
    )
    list_filter = ('entry_type', 'source', 'withdrawal_method', 'created_at')
    search_fields = ('wallet__agent__phone', 'label', 'withdrawal_ref')
    list_select_related = ('wallet__agent',)
    raw_id_fields = ('wallet', 'ref_usage', 'ref_visit')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

    @admin.display(description='Agent', ordering='wallet__agent__phone')
    def agent_phone(self, obj):
        return obj.wallet.agent.phone


# ═══════════════════════════════════════════════════════════════
# PlatformRevenue
# ═══════════════════════════════════════════════════════════════


@admin.register(PlatformRevenue)
class PlatformRevenueAdmin(admin.ModelAdmin):
    list_display = ('id', 'source', 'amount', 'ref_info', 'created_at')
    list_filter = ('source', 'created_at')
    search_fields = ('usage__video__listing__title',)
    list_select_related = ('usage', 'usage__video', 'visit')
    raw_id_fields = ('usage', 'visit')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

    @admin.display(description='Référence')
    def ref_info(self, obj):
        return str(obj.usage or obj.visit or '—')


# ═══════════════════════════════════════════════════════════════
# WithdrawalRequest — avec actions d'approbation/rejet
# ═══════════════════════════════════════════════════════════════


@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'agent_phone', 'amount', 'method', 'phone_number',
        'status', 'transaction_ref', 'processed_at', 'created_at',
    )
    list_filter = ('status', 'method', 'created_at')
    search_fields = (
        'wallet__agent__phone', 'phone_number',
        'transaction_ref',
    )
    list_select_related = ('wallet__agent', 'processed_by')
    raw_id_fields = ('wallet', 'wallet_entry', 'processed_by')
    readonly_fields = (
        'wallet', 'amount', 'method', 'phone_number',
        'status', 'wallet_entry', 'processed_by', 'processed_at',
        'created_at', 'updated_at',
    )
    ordering = ('-created_at',)
    actions = ['action_approve', 'action_reject']

    fieldsets = (
        ('Demande', {
            'fields': ('wallet', 'amount', 'method', 'phone_number', 'status'),
        }),
        ('Traitement admin', {
            'fields': ('transaction_ref', 'admin_note', 'processed_by', 'processed_at'),
        }),
        ('Liens', {
            'fields': ('wallet_entry',),
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
        }),
    )

    @admin.display(description='Agent', ordering='wallet__agent__phone')
    def agent_phone(self, obj):
        return obj.wallet.agent.phone

    # ── Actions d'admin ────────────────────────────────────

    @admin.action(description="Approuver les retraits sélectionnés")
    def action_approve(self, request, queryset):
        approved = 0
        errors = 0
        for withdrawal in queryset.filter(status=WithdrawalRequest.Status.PENDING):
            try:
                approve_withdrawal(
                    withdrawal,
                    admin_user=request.user,
                    admin_note=f"Approuvé en masse via admin par {request.user}",
                )
                approved += 1
            except WithdrawalAlreadyProcessedError:
                errors += 1

        self.message_user(
            request,
            f"{approved} retrait(s) approuvé(s). {errors} erreur(s)."
            if errors else f"{approved} retrait(s) approuvé(s).",
        )

    @admin.action(description="Rejeter les retraits sélectionnés")
    def action_reject(self, request, queryset):
        rejected = 0
        errors = 0
        for withdrawal in queryset.filter(status=WithdrawalRequest.Status.PENDING):
            try:
                reject_withdrawal(
                    withdrawal,
                    admin_user=request.user,
                    admin_note=f"Rejeté en masse via admin par {request.user}",
                )
                rejected += 1
            except WithdrawalAlreadyProcessedError:
                errors += 1

        self.message_user(
            request,
            f"{rejected} retrait(s) rejeté(s), montant restauré. {errors} erreur(s)."
            if errors else f"{rejected} retrait(s) rejeté(s), montant restauré.",
        )
