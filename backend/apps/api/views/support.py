"""
Views Support — Monajent
────────────────────────
Endpoints pour le système de tickets support (clients + agents).
"""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.support.models import SupportTicket, SupportMessage
from apps.api.serializers.support import (
    SupportTicketListSerializer,
    SupportTicketDetailSerializer,
    SupportTicketCreateSerializer,
    SupportMessageCreateSerializer,
    SupportMessageSerializer,
)


class SupportTicketListCreateView(APIView):
    """
    GET  → lister les tickets de l'utilisateur connecté
    POST → créer un nouveau ticket (subject, category, content)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tickets = SupportTicket.objects.filter(
            user=request.user,
        ).order_by('-updated_at')
        status_filter = request.query_params.get('status')
        if status_filter:
            tickets = tickets.filter(status=status_filter)
        from rest_framework.pagination import PageNumberPagination
        paginator = PageNumberPagination()
        paginator.page_size = 20
        page = paginator.paginate_queryset(tickets, request)
        serializer = SupportTicketListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = SupportTicketCreateSerializer(
            data=request.data, context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        ticket = serializer.save()

        from apps.support.tasks import send_ticket_created_email
        send_ticket_created_email.delay(ticket.id)

        return Response(
            SupportTicketDetailSerializer(ticket).data,
            status=status.HTTP_201_CREATED,
        )


class SupportTicketDetailView(APIView):
    """
    GET  → détail d'un ticket + tous les messages
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            ticket = SupportTicket.objects.prefetch_related('messages').get(
                pk=pk, user=request.user,
            )
        except SupportTicket.DoesNotExist:
            return Response(
                {'detail': 'Ticket non trouvé.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(SupportTicketDetailSerializer(ticket).data)


class SupportTicketMessageCreateView(APIView):
    """
    POST → ajouter un message à un ticket existant
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            ticket = SupportTicket.objects.get(pk=pk, user=request.user)
        except SupportTicket.DoesNotExist:
            return Response(
                {'detail': 'Ticket non trouvé.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if ticket.status == SupportTicket.Status.CLOSED:
            return Response(
                {'detail': 'Ce ticket est fermé. Vous ne pouvez plus y répondre.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = SupportMessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        msg = SupportMessage.objects.create(
            ticket=ticket,
            author=request.user,
            content=serializer.validated_data['content'],
            is_staff_reply=False,
        )

        if ticket.status == SupportTicket.Status.RESOLVED:
            ticket.status = SupportTicket.Status.OPEN
            ticket.save(update_fields=['status', 'updated_at'])

        return Response(
            SupportMessageSerializer(msg).data,
            status=status.HTTP_201_CREATED,
        )


class SupportTicketCloseView(APIView):
    """
    POST → fermer un ticket (par l'utilisateur)
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            ticket = SupportTicket.objects.get(pk=pk, user=request.user)
        except SupportTicket.DoesNotExist:
            return Response(
                {'detail': 'Ticket non trouvé.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        ticket.status = SupportTicket.Status.CLOSED
        ticket.save(update_fields=['status', 'updated_at'])
        return Response({'detail': 'Ticket fermé.', 'status': 'CLOSED'})
