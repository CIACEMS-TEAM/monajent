"""Serializers pour les endpoints IA (Gemini)."""

from rest_framework import serializers


class GeminiTextSerializer(serializers.Serializer):
    """Entrée texte pour extraction ou intention de recherche."""

    text = serializers.CharField(
        required=True,
        allow_blank=False,
        max_length=8000,
        trim_whitespace=True,
    )
