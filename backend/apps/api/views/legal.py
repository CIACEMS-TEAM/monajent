from django.conf import settings
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import LegalConsent
from ..serializers.legal import LegalConsentAcceptSerializer, LegalConsentReadSerializer


def _client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


class LegalConsentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        consents = LegalConsent.objects.filter(user=request.user)
        serializer = LegalConsentReadSerializer(consents, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = LegalConsentAcceptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        doc_type = serializer.validated_data['document_type']

        already = LegalConsent.objects.filter(
            user=request.user,
            document_type=doc_type,
        ).exists()
        if already:
            return Response(
                {'detail': 'Consentement déjà enregistré.'},
                status=status.HTTP_200_OK,
            )

        consent = LegalConsent.objects.create(
            user=request.user,
            document_type=doc_type,
            document_version=settings.LEGAL_DOCUMENT_VERSIONS.get(doc_type, 'unknown'),
            ip_address=_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:512],
        )
        return Response(
            LegalConsentReadSerializer(consent).data,
            status=status.HTTP_201_CREATED,
        )
