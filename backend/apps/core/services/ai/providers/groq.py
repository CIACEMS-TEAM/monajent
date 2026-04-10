"""
Provider Groq — Llama 3.3 70B via API OpenAI-compatible.
Priorité 10 (primaire) : 1000 RPD gratuit, ultra-rapide.
"""

from django.conf import settings

from .._registry import register_provider

_SYSTEM_MSG = (
    "Tu es un assistant expert immobilier en Côte d'Ivoire. "
    "Réponds UNIQUEMENT en JSON valide, sans markdown, sans texte avant ou après."
)


def _is_available() -> bool:
    return bool((getattr(settings, 'GROQ_API_KEY', None) or '').strip())


def _generate(prompt: str) -> str:
    from openai import OpenAI

    client = OpenAI(
        api_key=settings.GROQ_API_KEY.strip(),
        base_url=(
            getattr(settings, 'GROQ_API_URL', None) or 'https://api.groq.com/openai/v1'
        ).strip(),
    )
    model = (getattr(settings, 'GROQ_MODEL', None) or 'llama-3.3-70b-versatile').strip()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {'role': 'system', 'content': _SYSTEM_MSG},
            {'role': 'user', 'content': prompt},
        ],
        temperature=0.1,
        max_tokens=2048,
    )
    text = response.choices[0].message.content
    if not text or not text.strip():
        raise ValueError('Réponse Groq vide.')
    return text.strip()


register_provider(
    name='groq',
    priority=10,
    is_available=_is_available,
    generate=_generate,
)
