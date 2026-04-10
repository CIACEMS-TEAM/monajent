"""
Vues IA — extraction d'annonce (agents) et intention de recherche (public).
Délègue au package apps.core.services.ai (multi-providers, auto-discovery).
"""

from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsAgent
from apps.core.services.ai import (
    AIProviderError as GeminiAPIError,
    AIConfigurationError as GeminiConfigurationError,
    AIParseError as GeminiParseError,
    extract_listing_from_text,
    parse_search_intent,
)
from apps.core.services.ai._registry import get_providers

from ..serializers.ai import GeminiTextSerializer


def _ai_disabled_response():
    return Response(
        {'detail': "Mona n'est pas disponible pour le moment. Veuillez réessayer ultérieurement."},
        status=status.HTTP_503_SERVICE_UNAVAILABLE,
    )


def _any_provider_available() -> bool:
    return any(p.is_available() for p in get_providers())


class ExtractListingAIView(APIView):
    """
    POST /api/ai/extract-listing/
    Transforme une description libre en champs JSON pour pré-remplir le formulaire annonce.
    """

    permission_classes = [permissions.IsAuthenticated, IsAgent]
    throttle_scope = 'ai_extract_listing'

    @extend_schema(
        tags=['ai'],
        summary='Extraire les champs annonce depuis un texte',
        request=GeminiTextSerializer,
        responses={200: {'type': 'object', 'properties': {'data': {'type': 'object'}}}},
        examples=[
            OpenApiExample(
                'Exemple',
                value={'text': '3 pièces à Faya 250k/mois, 2+2+1, bitumé'},
                request_only=True,
            ),
        ],
    )
    def post(self, request):
        if not _any_provider_available():
            return _ai_disabled_response()
        ser = GeminiTextSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        text = ser.validated_data['text']
        try:
            data = extract_listing_from_text(text)
        except GeminiConfigurationError:
            return _ai_disabled_response()
        except GeminiParseError:
            return Response(
                {'detail': 'Mona n\'a pas pu interpréter votre description. Essayez de reformuler.'},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        except GeminiAPIError as e:
            return Response({'detail': str(e)}, status=status.HTTP_502_BAD_GATEWAY)
        return Response({'data': data}, status=status.HTTP_200_OK)


class SearchIntentAIView(APIView):
    """
    POST /api/ai/search-intent/
    Transforme une phrase (ex. transcription vocale) en paramètres pour GET /api/listings/.
    """

    permission_classes = [permissions.AllowAny]
    throttle_scope = 'ai_search_intent'

    @extend_schema(
        tags=['ai'],
        summary='Interpréter une recherche en filtres liste publique',
        request=GeminiTextSerializer,
        responses={200: {'type': 'object', 'properties': {'data': {'type': 'object'}}}},
    )
    def post(self, request):
        if not _any_provider_available():
            return _ai_disabled_response()
        ser = GeminiTextSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        text = ser.validated_data['text']
        try:
            data = parse_search_intent(text)
        except GeminiConfigurationError:
            return _ai_disabled_response()
        except GeminiParseError:
            return Response(
                {'detail': 'Mona n\'a pas compris votre recherche. Essayez de reformuler.'},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        except GeminiAPIError as e:
            return Response({'detail': str(e)}, status=status.HTTP_502_BAD_GATEWAY)
        return Response({'data': data}, status=status.HTTP_200_OK)
