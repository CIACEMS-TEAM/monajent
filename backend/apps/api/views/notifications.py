"""
Vues Notifications — Monajent
─────────────────────────────
GET  /api/notifications/          Liste des notifications de l'utilisateur
POST /api/notifications/read/     Marquer des notifications comme lues
POST /api/notifications/read-all/ Marquer toutes comme lues
"""

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import Notification
from ..serializers.notifications import NotificationSerializer


class NotificationListView(generics.ListAPIView):
    """GET /api/notifications/ — paginated, most recent first."""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Notification.objects.filter(user=self.request.user)
        unread = self.request.query_params.get('unread')
        if unread == '1':
            qs = qs.filter(is_read=False)
        return qs


class NotificationReadView(APIView):
    """POST /api/notifications/read/ — mark specific IDs as read."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        ids = request.data.get('ids', [])
        if not isinstance(ids, list) or not ids:
            return Response({'detail': 'Fournissez une liste d\'ids.'}, status=status.HTTP_400_BAD_REQUEST)
        count = Notification.objects.filter(user=request.user, id__in=ids, is_read=False).update(is_read=True)
        return Response({'marked': count})


class NotificationReadAllView(APIView):
    """POST /api/notifications/read-all/ — mark all as read."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({'marked': count})


class NotificationUnreadCountView(APIView):
    """GET /api/notifications/unread-count/ — quick badge count."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({'count': count})
