"""
Vues Agent — Monajent
──────────────────────
Profil & KYC :
    GET    /api/agent/profile/              → Profil agent complet
    PATCH  /api/agent/profile/              → Modifier le profil (multipart)

Documents KYC :
    GET    /api/agent/profile/documents/    → Liste des documents
    POST   /api/agent/profile/documents/    → Uploader un document (crée ou remplace)
    DELETE /api/agent/profile/documents/{id}/ → Interdit si vérifié
"""

from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import AgentProfile, AgentDocument
from apps.core.permissions import IsAgent
from apps.api.serializers.agent import (
    AgentProfileReadSerializer,
    AgentProfileUpdateSerializer,
    AgentDocumentSerializer,
    AgentDocumentUploadSerializer,
)


# ═══════════════════════════════════════════════════════════════
# Profil agent
# ═══════════════════════════════════════════════════════════════


class AgentProfileView(APIView):
    permission_classes = [IsAuthenticated, IsAgent]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        profile, _ = AgentProfile.objects.prefetch_related('documents').get_or_create(
            user=request.user,
        )
        serializer = AgentProfileReadSerializer(profile, context={'request': request})
        return Response(serializer.data)

    def patch(self, request):
        ser = AgentProfileUpdateSerializer(
            data=request.data,
            context={'request': request, 'user': request.user},
        )
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        user = request.user
        profile, _ = AgentProfile.objects.get_or_create(user=user)

        user_fields = []
        if 'username' in data:
            user.username = data['username']
            user_fields.append('username')
        if 'email' in data:
            user.email = data['email'] or None
            user_fields.append('email')
        if user_fields:
            user_fields.append('updated_at')
            user.save(update_fields=user_fields)

        profile_fields = []
        text_attrs = ['agency_name', 'bio', 'contact_phone', 'contact_email', 'national_id_number']
        for attr in text_attrs:
            if attr in data:
                setattr(profile, attr, data[attr])
                profile_fields.append(attr)

        file_attrs = ['national_id_document', 'profile_photo']
        for attr in file_attrs:
            if attr in data:
                old_file = getattr(profile, attr, None)
                new_file = data[attr]
                if new_file is None and old_file:
                    old_file.delete(save=False)
                setattr(profile, attr, new_file)
                profile_fields.append(attr)

        if profile_fields:
            profile_fields.append('updated_at')
            profile.save(update_fields=profile_fields)

        profile.refresh_from_db()
        return Response(
            AgentProfileReadSerializer(profile, context={'request': request}).data,
        )


# ═══════════════════════════════════════════════════════════════
# Documents KYC
# ═══════════════════════════════════════════════════════════════


class AgentDocumentListCreateView(APIView):
    """
    GET  → Liste des documents KYC.
    POST → Upload d'un document. Si doc_type+side existe déjà, remplace le fichier.
           Interdit si le profil est déjà vérifié.
    """
    permission_classes = [IsAuthenticated, IsAgent]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        profile = AgentProfile.objects.filter(user=request.user).first()
        if not profile:
            return Response([], status=status.HTTP_200_OK)
        docs = AgentDocument.objects.filter(agent_profile=profile).order_by('doc_type', 'side')
        serializer = AgentDocumentSerializer(docs, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request):
        profile, _ = AgentProfile.objects.get_or_create(user=request.user)

        if profile.kyc_status in (AgentProfile.KycStatus.PENDING, AgentProfile.KycStatus.APPROVED):
            return Response(
                {'detail': 'Les documents ne peuvent pas être modifiés pendant ou après la vérification.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        ser = AgentDocumentUploadSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        vd = ser.validated_data

        existing = AgentDocument.objects.filter(
            agent_profile=profile,
            doc_type=vd['doc_type'],
            side=vd['side'],
        ).first()

        if existing:
            existing.file.delete(save=False)
            existing.file = vd['file']
            existing.label = vd.get('label', existing.label) or f"{vd['doc_type']} {vd['side']}"
            existing.save()
            doc = existing
        else:
            doc = AgentDocument.objects.create(
                agent_profile=profile,
                file=vd['file'],
                doc_type=vd['doc_type'],
                side=vd['side'],
                label=vd.get('label', '') or f"{vd['doc_type']} {vd['side']}",
            )

        return Response(
            AgentDocumentSerializer(doc, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class AgentDocumentDeleteView(APIView):
    """DELETE → Interdit si PENDING ou APPROVED."""
    permission_classes = [IsAuthenticated, IsAgent]

    def delete(self, request, pk):
        profile = AgentProfile.objects.filter(user=request.user).first()
        if not profile:
            return Response({'detail': 'Profil introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        if profile.kyc_status in (AgentProfile.KycStatus.PENDING, AgentProfile.KycStatus.APPROVED):
            return Response(
                {'detail': 'Suppression interdite pendant ou après vérification.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            doc = AgentDocument.objects.get(pk=pk, agent_profile=profile)
        except AgentDocument.DoesNotExist:
            return Response({'detail': 'Document introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        doc.file.delete(save=False)
        doc.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AgentKycSubmitView(APIView):
    """
    POST /api/agent/profile/kyc/submit/
    Soumet les documents KYC pour vérification.
    Vérifie que les documents requis sont présents.
    """
    permission_classes = [IsAuthenticated, IsAgent]

    def post(self, request):
        profile = AgentProfile.objects.filter(user=request.user).first()
        if not profile:
            return Response({'detail': 'Profil introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        if profile.kyc_status == AgentProfile.KycStatus.APPROVED:
            return Response({'detail': 'Votre identité est déjà vérifiée.'}, status=status.HTTP_400_BAD_REQUEST)

        if profile.kyc_status == AgentProfile.KycStatus.PENDING:
            return Response({'detail': 'Vos documents sont déjà en cours de vérification.'}, status=status.HTTP_400_BAD_REQUEST)

        docs = AgentDocument.objects.filter(agent_profile=profile)
        if not docs.exists():
            return Response({'detail': 'Aucun document chargé.'}, status=status.HTTP_400_BAD_REQUEST)

        doc_types = set(docs.values_list('doc_type', flat=True))
        for dt in doc_types:
            if dt == AgentDocument.DocType.CNI:
                sides = set(docs.filter(doc_type=dt).values_list('side', flat=True))
                if 'RECTO' not in sides or 'VERSO' not in sides:
                    return Response(
                        {'detail': 'Pour une CNI, le recto et le verso sont requis.'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            else:
                if not docs.filter(doc_type=dt, side='SINGLE').exists():
                    return Response(
                        {'detail': f'Document manquant pour {dt}.'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

        profile.kyc_status = AgentProfile.KycStatus.PENDING
        profile.kyc_rejection_reason = ''
        profile.save(update_fields=['kyc_status', 'kyc_rejection_reason', 'updated_at'])

        return Response({'detail': 'Documents soumis pour vérification.', 'kyc_status': 'PENDING'})


class AdminKycReviewView(APIView):
    """
    POST /api/admin/kyc/{profile_id}/review/
    Body: { "action": "approve" | "reject", "reason": "..." }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, profile_id):
        if not (request.user.is_staff or request.user.role == 'ADMIN'):
            return Response({'detail': 'Accès refusé.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            profile = AgentProfile.objects.get(pk=profile_id)
        except AgentProfile.DoesNotExist:
            return Response({'detail': 'Profil introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        action = request.data.get('action')
        if action not in ('approve', 'reject'):
            return Response({'detail': 'Action invalide.'}, status=status.HTTP_400_BAD_REQUEST)

        if action == 'approve':
            profile.kyc_status = AgentProfile.KycStatus.APPROVED
            profile.verified = True
            profile.kyc_rejection_reason = ''
            profile.save(update_fields=['kyc_status', 'verified', 'kyc_rejection_reason', 'updated_at'])

            from apps.users.models import Notification
            Notification.objects.create(
                user=profile.user,
                category='KYC',
                title='Identité vérifiée',
                message='Votre identité a été vérifiée avec succès. Vous pouvez maintenant publier vos annonces.',
                link='/agent/settings#kyc',
            )
            return Response({'detail': 'KYC approuvé.', 'kyc_status': 'APPROVED'})

        else:
            reason = request.data.get('reason', 'Document non conforme.')
            profile.kyc_status = AgentProfile.KycStatus.REJECTED
            profile.verified = False
            profile.kyc_rejection_reason = reason
            profile.save(update_fields=['kyc_status', 'verified', 'kyc_rejection_reason', 'updated_at'])

            from apps.users.models import Notification
            Notification.objects.create(
                user=profile.user,
                category='KYC',
                title='Vérification rejetée',
                message=f'Votre vérification d\'identité a été rejetée. Motif : {reason}',
                link='/agent/settings#kyc',
            )
            return Response({'detail': 'KYC rejeté.', 'kyc_status': 'REJECTED'})
