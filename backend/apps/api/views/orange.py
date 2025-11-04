from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status

from apps.core.models import SmsDeliveryLog


class OrangeDlrView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        # Orange enverra une structure JSON OneAPI avec l'état de livraison
        payload = request.data
        # Extraire des champs utiles si présents
        message_id = ''
        address = ''
        delivery_status = ''

        try:
            # Formats possibles selon la spec OneAPI / implémentation Orange
            # Exemple attendu: { "deliveryReceipt": { "address": "tel:+225...", "messageId": "...", "status": "DeliveredToTerminal" } }
            dr = payload.get('deliveryReceipt') or payload.get('deliveryInfoNotification', {}).get('deliveryInfo', {})
            if isinstance(dr, dict):
                address = dr.get('address', '') or dr.get('msisdn', '')
                message_id = dr.get('messageId', '') or dr.get('messageID', '')
                delivery_status = dr.get('status', '') or dr.get('deliveryStatus', '')
        except Exception:
            pass

        SmsDeliveryLog.objects.create(
            message_id=message_id,
            address=address,
            status=delivery_status,
            payload=payload,
        )

        # Toujours accuser réception 201/204
        return Response(status=status.HTTP_201_CREATED)



