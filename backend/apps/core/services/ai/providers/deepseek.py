"""
Provider DeepSeek — API compatible OpenAI (DeepSeek-V3.2).
Priorité 50 (entre Groq et Gemini) : pas de rate limit, ~0.28$/M tokens.
"""

from django.conf import settings

from .._registry import register_provider

_SYSTEM_MSG = (
    "Tu es un assistant expert immobilier en Côte d'Ivoire. "
    "Réponds UNIQUEMENT en JSON valide, sans markdown, sans texte avant ou après."
)


def _is_available() -> bool:
    return bool((getattr(settings, 'DEEPSEEK_API_KEY', None) or '').strip())


def _generate(prompt: str) -> str:
    from openai import OpenAI

    client = OpenAI(
        api_key=settings.DEEPSEEK_API_KEY.strip(),
        base_url=(
            getattr(settings, 'DEEPSEEK_API_URL', None) or 'https://api.deepseek.com'
        ).strip(),
    )
    model = (getattr(settings, 'DEEPSEEK_MODEL', None) or 'deepseek-chat').strip()

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
        raise ValueError('Réponse DeepSeek vide.')
    return text.strip()


register_provider(
    name='deepseek',
    priority=50,
    is_available=_is_available,
    generate=_generate,
)
