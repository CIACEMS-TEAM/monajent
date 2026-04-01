"""
Vues Visites, Disponibilités & Signalements — Monajent
──────────────────────────────────────────────────────

Agent — Disponibilités :
    GET/POST   /api/agent/availability/              → CRUD créneaux
    PUT/DELETE  /api/agent/availability/{id}/          → Modifier/supprimer

Client — Visites :
    GET    /api/listings/{id}/availability/       → Créneaux dispo de l'agent
    POST   /api/client/visits/                    → Demander visite (choisir créneau)
    GET    /api/client/visits/                    → Mes visites
    POST   /api/client/visits/{id}/cancel/        → Annuler

Agent — Visites :
    GET    /api/agent/visits/                     → Visites à traiter
    POST   /api/agent/visits/{id}/confirm/        → Confirmer
    POST   /api/agent/visits/{id}/validate-code/  → Valider le code (AVANT la visite)

Signalements :
    POST   /api/listings/{id}/report/             → Signaler
    GET    /api/client/reports/                    → Mes signalements
"""

from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.visits.models import VisitRequest, AgentAvailabilitySlot, AgentDateSlot
from apps.listings.models import Listing, ListingReport
from apps.core.permissions import IsClient, IsAgent
from apps.api.throttles import VisitRequestThrottle
from apps.api.serializers.visits import (
    AgentAvailabilitySlotSerializer,
    AgentAvailabilityPublicSerializer,
    AgentDateSlotSerializer,
    AgentDateSlotPublicSerializer,
    VisitRequestClientSerializer,
    VisitRequestAgentSerializer,
    VisitRequestCreateSerializer,
    VisitConfirmSerializer,
    VisitValidateCodeSerializer,
    ListingReportCreateSerializer,
    ListingReportSerializer,
)
from apps.core.services.visits import (
    request_visit,
    confirm_visit,
    validate_visit_code,
    cancel_visit,
    mark_no_show,
    NoPhysicalKeyError,
    InvalidVisitCodeError,
    VisitNotConfirmedError,
    VisitError,
)
from apps.core.services.listing_lifecycle import process_report
from apps.users.models import Notification


# ═══════════════════════════════════════════════════════════════
# Agent : Gestion des disponibilités
# ═══════════════════════════════════════════════════════════════


class AgentAvailabilityListCreateView(generics.ListCreateAPIView):
    """
    GET  → Mes créneaux de disponibilité.
    POST → Ajouter un créneau (ex: Lundi 9h-12h).
    """
    permission_classes = [IsAuthenticated, IsAgent]
    serializer_class = AgentAvailabilitySlotSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return AgentAvailabilitySlot.objects.none()
        return AgentAvailabilitySlot.objects.filter(agent=self.request.user)

    def perform_create(self, serializer):
        serializer.save(agent=self.request.user)


class AgentAvailabilityDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET/PUT/PATCH/DELETE /api/agent/availability/{id}/
    """
    permission_classes = [IsAuthenticated, IsAgent]
    serializer_class = AgentAvailabilitySlotSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return AgentAvailabilitySlot.objects.none()
        return AgentAvailabilitySlot.objects.filter(agent=self.request.user)


# ═══════════════════════════════════════════════════════════════
# Agent : Créneaux ponctuels (agenda)
# ═══════════════════════════════════════════════════════════════


class AgentDateSlotListCreateView(generics.ListCreateAPIView):
    """
    GET  → Créneaux ponctuels de l'agent.
    POST → Ajouter un créneau ponctuel (date + horaire).
    """
    permission_classes = [IsAuthenticated, IsAgent]
    serializer_class = AgentDateSlotSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return AgentDateSlot.objects.none()
        return AgentDateSlot.objects.filter(agent=self.request.user)

    def perform_create(self, serializer):
        serializer.save(agent=self.request.user)


class AgentDateSlotDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PUT/PATCH/DELETE /api/agent/date-slots/{id}/"""
    permission_classes = [IsAuthenticated, IsAgent]
    serializer_class = AgentDateSlotSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return AgentDateSlot.objects.none()
        return AgentDateSlot.objects.filter(agent=self.request.user)


# ═══════════════════════════════════════════════════════════════
# Client : Voir les disponibilités d'un agent (via listing)
# ═══════════════════════════════════════════════════════════════


class ListingAvailabilityView(generics.ListAPIView):
    """
    GET /api/listings/{listing_id}/availability/
    Créneaux de disponibilité de l'agent propriétaire de l'annonce.
    Accessible à tous (même non-authentifié, pour info).
    """
    permission_classes = [AllowAny]
    serializer_class = AgentAvailabilityPublicSerializer

    def get_queryset(self):
        listing = get_object_or_404(
            Listing, pk=self.kwargs['listing_id'], status=Listing.Status.ACTIF,
        )
        return (
            AgentAvailabilitySlot.objects
            .filter(agent=listing.agent, is_active=True)
            .order_by('day_of_week', 'start_time')
        )


# ═══════════════════════════════════════════════════════════════
# Client : Demandes de visite
# ═══════════════════════════════════════════════════════════════


class ClientVisitListCreateView(APIView):
    """
    GET  → Mes visites (historique client).
    POST → Demander une visite physique (choisir un créneau).
         Si le client n'a pas encore vu la vidéo → consomme clé physique + 1 clé virtuelle.
         Si le client a déjà vu la vidéo → consomme SEULEMENT la clé physique.
    """
    permission_classes = [IsAuthenticated, IsClient]

    def get_throttles(self):
        if self.request.method == 'POST':
            return [VisitRequestThrottle()]
        return []

    def get(self, request):
        visits = (
            VisitRequest.objects
            .filter(user=request.user)
            .select_related('listing', 'listing__agent', 'slot')
            .order_by('-created_at')
        )
        from rest_framework.pagination import PageNumberPagination
        paginator = PageNumberPagination()
        paginator.page_size = 20
        page = paginator.paginate_queryset(visits, request)
        serializer = VisitRequestClientSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        ser = VisitRequestCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        listing = get_object_or_404(
            Listing.objects.select_related('agent'),
            pk=ser.validated_data['listing_id'],
            status=Listing.Status.ACTIF,
        )

        slot = get_object_or_404(
            AgentAvailabilitySlot,
            pk=ser.validated_data['slot_id'],
            agent=listing.agent,
            is_active=True,
        )

        try:
            result = request_visit(
                user=request.user,
                listing=listing,
                slot=slot,
                scheduled_at=ser.validated_data.get('scheduled_at'),
                client_note=ser.validated_data.get('client_note', ''),
            )
        except NoPhysicalKeyError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_402_PAYMENT_REQUIRED,
            )

        visit = (
            VisitRequest.objects
            .select_related('listing', 'listing__agent', 'slot')
            .get(pk=result['visit'].pk)
        )

        Notification.objects.create(
            user=listing.agent,
            category=Notification.Category.VISIT,
            title='Nouvelle demande de visite',
            message=f'Un client a demandé une visite pour « {listing.title} ».',
            link='/agent/visits',
        )

        response_data = VisitRequestClientSerializer(visit).data
        response_data['virtual_key_consumed'] = result['virtual_key_consumed']
        response_data['already_interacted'] = result['already_interacted']

        if result['virtual_key_consumed']:
            response_data['revenue_info'] = "Clé virtuelle consommée. Agent crédité de 10 XOF."
        else:
            response_data['revenue_info'] = "Vidéo déjà visionnée. Aucune clé virtuelle consommée."

        return Response(response_data, status=status.HTTP_201_CREATED)


class ClientVisitCancelView(APIView):
    """POST /api/client/visits/{id}/cancel/ → Annuler (clé physique restaurée)."""
    permission_classes = [IsAuthenticated, IsClient]

    def post(self, request, pk):
        visit = get_object_or_404(
            VisitRequest.objects.select_related('pack'),
            pk=pk,
            user=request.user,
        )
        was_confirmed = visit.status == 'CONFIRMED'
        reason = request.data.get('reason', '')
        try:
            cancel_visit(visit, reason=reason)
        except VisitError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        if was_confirmed:
            msg = (
                "Visite annulée. L'agent avait déjà confirmé le rendez-vous, "
                "votre clé physique n'est pas restaurée."
            )
        else:
            msg = "Visite annulée. Clé physique restaurée."

        Notification.objects.create(
            user=visit.listing.agent,
            category=Notification.Category.VISIT,
            title='Visite annulée par le client',
            message=f'Le client a annulé sa visite pour « {visit.listing.title} ».'
                    + (f' Motif : {reason}' if reason.strip() else ''),
            link='/agent/visits',
        )

        return Response({
            'detail': msg,
            'physical_key_restored': not was_confirmed,
        })


# ═══════════════════════════════════════════════════════════════
# Agent : Gestion des visites
# ═══════════════════════════════════════════════════════════════


class AgentVisitListView(generics.ListAPIView):
    """GET /api/agent/visits/ → Visites à traiter sur mes annonces."""
    permission_classes = [IsAuthenticated, IsAgent]
    serializer_class = VisitRequestAgentSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return VisitRequest.objects.none()
        return (
            VisitRequest.objects
            .filter(listing__agent=self.request.user)
            .select_related('user', 'listing', 'slot')
            .order_by('-created_at')
        )


class AgentVisitConfirmView(APIView):
    """POST /api/agent/visits/{id}/confirm/ → Confirmer la visite."""
    permission_classes = [IsAuthenticated, IsAgent]

    def post(self, request, pk):
        visit = get_object_or_404(
            VisitRequest.objects.select_related('listing'),
            pk=pk,
            listing__agent=request.user,
        )

        ser = VisitConfirmSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        try:
            confirm_visit(
                visit,
                scheduled_at=ser.validated_data.get('scheduled_at'),
                agent_note=ser.validated_data.get('agent_note', ''),
                meeting_address=ser.validated_data.get('meeting_address', ''),
                meeting_latitude=ser.validated_data.get('meeting_latitude'),
                meeting_longitude=ser.validated_data.get('meeting_longitude'),
            )
        except VisitError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        scheduled_info = f' pour le {visit.scheduled_at.strftime("%d/%m/%Y à %H:%M")}' if visit.scheduled_at else ''
        Notification.objects.create(
            user=visit.user,
            category=Notification.Category.VISIT,
            title='Visite confirmée',
            message=f'Votre visite pour « {visit.listing.title} » a été confirmée{scheduled_info}.',
            link='/client/visits',
        )

        return Response({
            'detail': "Visite confirmée.",
            'scheduled_at': str(visit.scheduled_at) if visit.scheduled_at else None,
        })


class AgentVisitValidateCodeView(APIView):
    """
    POST /api/agent/visits/{id}/validate-code/
    L'agent demande le code au client AVANT de commencer la visite.
    """
    permission_classes = [IsAuthenticated, IsAgent]

    def post(self, request, pk):
        visit = get_object_or_404(
            VisitRequest.objects.select_related('listing'),
            pk=pk,
            listing__agent=request.user,
        )

        ser = VisitValidateCodeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        try:
            validate_visit_code(visit, code=ser.validated_data['code'])
        except InvalidVisitCodeError:
            return Response(
                {'detail': "Code de vérification incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except VisitNotConfirmedError:
            return Response(
                {'detail': "Confirmez d'abord la visite avant de valider le code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        Notification.objects.create(
            user=visit.user,
            category=Notification.Category.VISIT,
            title='Visite effectuée',
            message=f'Votre visite pour « {visit.listing.title} » a bien été réalisée. Merci !',
            link='/client/visits',
        )

        return Response({'detail': "Code validé. Visite effectuée. Merci !"})


class AgentVisitNoShowView(APIView):
    """POST /api/agent/visits/{id}/no-show/ → Marquer le client comme absent."""
    permission_classes = [IsAuthenticated, IsAgent]

    def post(self, request, pk):
        visit = get_object_or_404(
            VisitRequest.objects.select_related('listing'),
            pk=pk,
            listing__agent=request.user,
        )
        reason = request.data.get('reason', '')
        try:
            mark_no_show(visit, reason=reason)
        except VisitError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        Notification.objects.create(
            user=visit.user,
            category=Notification.Category.VISIT,
            title='Absence signalée',
            message=f'Vous avez été marqué(e) absent(e) pour la visite de « {visit.listing.title} ».',
            link='/client/visits',
        )

        return Response({'detail': "Client marqué comme absent (NO_SHOW)."})


# ═══════════════════════════════════════════════════════════════
# Signalement d'annonce
# ═══════════════════════════════════════════════════════════════


class ListingReportCreateView(APIView):
    """POST /api/listings/{listing_id}/report/ → Signaler une annonce."""
    permission_classes = [IsAuthenticated, IsClient]

    def post(self, request, listing_id):
        listing = get_object_or_404(Listing, pk=listing_id)

        data = {**request.data, 'listing': listing.pk}
        ser = ListingReportCreateSerializer(data=data)
        ser.is_valid(raise_exception=True)

        if ListingReport.objects.filter(user=request.user, listing=listing).exists():
            return Response(
                {'detail': "Vous avez déjà signalé cette annonce."},
                status=status.HTTP_409_CONFLICT,
            )

        report = ser.save(user=request.user)
        auto_suspended = process_report(report)

        response_data = {
            'detail': "Signalement enregistré. Merci pour votre vigilance.",
            'report_id': report.pk,
        }
        if auto_suspended:
            response_data['listing_suspended'] = True
            response_data['detail'] += " L'annonce a été automatiquement suspendue."

        return Response(response_data, status=status.HTTP_201_CREATED)


class ClientReportListView(generics.ListAPIView):
    """GET /api/client/reports/ → Mes signalements."""
    permission_classes = [IsAuthenticated, IsClient]
    serializer_class = ListingReportSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return ListingReport.objects.none()
        return (
            ListingReport.objects
            .filter(user=self.request.user)
            .select_related('listing')
        )
