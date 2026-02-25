"""
Serializers Wallet — Monajent
─────────────────────────────
• WalletSerializer            → solde, totaux, stats, has_pin
• WalletEntrySerializer       → historique des mouvements
• PinSetSerializer            → configuration initiale du PIN
• PinChangeSerializer         → changement de PIN (ancien + nouveau)
• WithdrawalCreateSerializer  → demande de retrait (avec PIN)
• WithdrawalDetailSerializer  → détail d'une demande
"""

from rest_framework import serializers

from apps.wallet.models import (
    Wallet, WalletEntry, WithdrawalRequest, MINIMUM_WITHDRAWAL, PIN_LENGTH,
)


# ═══════════════════════════════════════════════════════════════
# Wallet (solde + stats)
# ═══════════════════════════════════════════════════════════════


class WalletSerializer(serializers.ModelSerializer):
    """Vue complète du portefeuille agent."""
    can_withdraw = serializers.BooleanField(read_only=True)
    has_pin = serializers.BooleanField(read_only=True)
    minimum_withdrawal = serializers.SerializerMethodField()
    pending_withdrawal = serializers.SerializerMethodField()

    class Meta:
        model = Wallet
        fields = [
            'balance', 'total_earned', 'total_withdrawn',
            'can_withdraw', 'has_pin', 'minimum_withdrawal',
            'pending_withdrawal',
            'created_at', 'updated_at',
        ]
        read_only_fields = fields

    def get_minimum_withdrawal(self, obj):
        return str(MINIMUM_WITHDRAWAL)

    def get_pending_withdrawal(self, obj):
        pending = (
            WithdrawalRequest.objects
            .filter(wallet=obj, status=WithdrawalRequest.Status.PENDING)
            .first()
        )
        if pending:
            return {
                'id': pending.pk,
                'amount': str(pending.amount),
                'method': pending.get_method_display(),
                'phone_number': pending.phone_number,
                'created_at': pending.created_at.isoformat(),
            }
        return None


# ═══════════════════════════════════════════════════════════════
# WalletEntry (historique mouvements)
# ═══════════════════════════════════════════════════════════════


class WalletEntrySerializer(serializers.ModelSerializer):
    """Ligne de mouvement (crédit ou débit)."""
    source_label = serializers.CharField(source='get_source_display', read_only=True)
    entry_type_label = serializers.CharField(source='get_entry_type_display', read_only=True)

    class Meta:
        model = WalletEntry
        fields = [
            'id', 'entry_type', 'entry_type_label',
            'source', 'source_label',
            'amount', 'label',
            'withdrawal_method', 'withdrawal_ref',
            'created_at',
        ]
        read_only_fields = fields


# ═══════════════════════════════════════════════════════════════
# Code PIN de retrait
# ═══════════════════════════════════════════════════════════════


class PinSetSerializer(serializers.Serializer):
    """Configuration initiale du code PIN (première fois)."""
    pin = serializers.CharField(
        min_length=PIN_LENGTH, max_length=PIN_LENGTH,
        help_text=f'Code PIN à {PIN_LENGTH} chiffres.',
    )
    pin_confirm = serializers.CharField(
        min_length=PIN_LENGTH, max_length=PIN_LENGTH,
        help_text='Confirmation du code PIN.',
    )

    def validate(self, attrs):
        if attrs['pin'] != attrs['pin_confirm']:
            raise serializers.ValidationError(
                {'pin_confirm': "Les deux codes PIN ne correspondent pas."}
            )
        if not attrs['pin'].isdigit():
            raise serializers.ValidationError(
                {'pin': f"Le code PIN doit contenir uniquement {PIN_LENGTH} chiffres."}
            )
        return attrs


class PinChangeSerializer(serializers.Serializer):
    """Changement de code PIN (nécessite l'ancien)."""
    current_pin = serializers.CharField(
        min_length=PIN_LENGTH, max_length=PIN_LENGTH,
        help_text='Code PIN actuel.',
    )
    new_pin = serializers.CharField(
        min_length=PIN_LENGTH, max_length=PIN_LENGTH,
        help_text=f'Nouveau code PIN à {PIN_LENGTH} chiffres.',
    )
    new_pin_confirm = serializers.CharField(
        min_length=PIN_LENGTH, max_length=PIN_LENGTH,
        help_text='Confirmation du nouveau code PIN.',
    )

    def validate(self, attrs):
        if attrs['new_pin'] != attrs['new_pin_confirm']:
            raise serializers.ValidationError(
                {'new_pin_confirm': "Les deux codes PIN ne correspondent pas."}
            )
        if not attrs['new_pin'].isdigit():
            raise serializers.ValidationError(
                {'new_pin': f"Le code PIN doit contenir uniquement {PIN_LENGTH} chiffres."}
            )
        return attrs


# ═══════════════════════════════════════════════════════════════
# Demande de retrait (avec PIN)
# ═══════════════════════════════════════════════════════════════


class WithdrawalCreateSerializer(serializers.Serializer):
    """
    Demande de retrait par l'agent.
    Nécessite le code PIN de retrait.
    """
    pin = serializers.CharField(
        min_length=PIN_LENGTH, max_length=PIN_LENGTH,
        help_text='Code PIN de retrait.',
    )
    amount = serializers.DecimalField(
        max_digits=12, decimal_places=2,
        help_text=f'Montant à retirer (minimum {MINIMUM_WITHDRAWAL} XOF).',
    )
    method = serializers.ChoiceField(
        choices=WithdrawalRequest.Method.choices,
        help_text='Méthode de retrait : ORANGE_MONEY, WAVE, MTN.',
    )
    phone_number = serializers.CharField(
        max_length=20,
        help_text='Numéro mobile money pour recevoir le virement.',
    )


class WithdrawalDetailSerializer(serializers.ModelSerializer):
    """Détail d'une demande de retrait."""
    method_label = serializers.CharField(source='get_method_display', read_only=True)
    status_label = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = WithdrawalRequest
        fields = [
            'id', 'amount',
            'method', 'method_label',
            'phone_number',
            'status', 'status_label',
            'transaction_ref', 'admin_note',
            'processed_at',
            'created_at',
        ]
        read_only_fields = fields
