"""
Serializers Payments — Monajent
───────────────────────────────
Serializers pour l'initiation de paiement, la lecture d'un paiement,
et la réponse post-checkout.
"""

from rest_framework import serializers

from apps.payments.models import Payment


# ═══════════════════════════════════════════════════════════════
# Initiation de paiement (Client → POST /api/client/packs/buy/)
# ═══════════════════════════════════════════════════════════════

class InitiatePaymentSerializer(serializers.Serializer):
    """
    Champs envoyés par le client pour initier un achat de pack.
    """
    provider = serializers.ChoiceField(
        choices=Payment.Provider.choices,
        help_text="Méthode de paiement : ORANGE_MONEY, WAVE, MTN, CARD.",
    )
    return_url = serializers.URLField(
        required=False,
        allow_blank=True,
        default='',
        help_text="URL de retour après paiement (optionnel, pour le frontend).",
    )


class InitiatePaymentResponseSerializer(serializers.Serializer):
    """Réponse après initiation du paiement."""
    payment_id = serializers.IntegerField(help_text="ID du paiement créé.")
    tx_ref = serializers.CharField(help_text="Référence de transaction unique.")
    checkout_url = serializers.URLField(help_text="URL de la page de paiement.")
    status = serializers.CharField(help_text="Statut initial : PENDING.")
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField()
    provider = serializers.CharField()


# ═══════════════════════════════════════════════════════════════
# Lecture d'un paiement (historique)
# ═══════════════════════════════════════════════════════════════

class PaymentSerializer(serializers.ModelSerializer):
    """Paiement en lecture (historique client)."""
    status_label = serializers.CharField(
        source='get_status_display', read_only=True,
    )
    provider_label = serializers.CharField(
        source='get_provider_display', read_only=True,
    )
    pack_id = serializers.IntegerField(
        source='pack.id', read_only=True, default=None,
    )
    has_pack = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = [
            'id', 'tx_ref', 'provider', 'provider_label',
            'status', 'status_label',
            'amount', 'currency',
            'pack_id', 'has_pack',
            'created_at', 'updated_at',
        ]
        read_only_fields = fields

    def get_has_pack(self, obj) -> bool:
        return obj.pack_id is not None
