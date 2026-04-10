"""
Open Graph share page — MonaJent
─────────────────────────────────
GET /api/share/<slug>/          → HTML avec meta OG (bots) ou redirect 302 (humains)
GET /api/share/<slug>/image.jpg → Proxy image stable pour og:image

Corrections WhatsApp (avril 2026) :
- Image lue en mémoire → Content-Length exact (les bots WhatsApp en ont besoin)
- Fallback image servie directement en 200 (pas de 302 que WhatsApp ne suit pas)
- og:image sur le même domaine que og:url (via nginx ^~ /share/)
- og:image:type dynamique selon le fichier réel
"""

import io
import re

from django.conf import settings
from django.http import Http404, HttpResponse
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from apps.listings.models import Listing

FRONTEND_URL = getattr(settings, 'FRONTEND_URL', 'https://monajent.com').rstrip('/')

BOT_PATTERN = re.compile(
    r'facebookexternalhit|Facebot|Twitterbot|WhatsApp|LinkedInBot|'
    r'Slackbot|TelegramBot|Pinterest|Googlebot|Google-Read-Aloud|'
    r'Discordbot|Viber|Snapchat|redditbot|TikTok|Bytespider',
    re.IGNORECASE,
)

_IMAGE_CACHE = 'public, max-age=86400'

_fallback_image_cache: bytes | None = None
_FALLBACK_CT = 'image/png'


def _get_fallback_image() -> bytes:
    """1200x630 branded PNG served directly (no redirect)."""
    global _fallback_image_cache
    if _fallback_image_cache is not None:
        return _fallback_image_cache

    try:
        from PIL import Image, ImageDraw, ImageFont

        img = Image.new('RGB', (1200, 630), color=(29, 165, 63))
        draw = ImageDraw.Draw(img)
        for path in (
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
            '/usr/share/fonts/TTF/DejaVuSans-Bold.ttf',
        ):
            try:
                title_font = ImageFont.truetype(path, 80)
                sub_font = ImageFont.truetype(path.replace('-Bold', ''), 36)
                break
            except OSError:
                continue
        else:
            title_font = ImageFont.load_default(size=80)
            sub_font = ImageFont.load_default(size=36)

        title = 'MonaJent'
        tb = draw.textbbox((0, 0), title, font=title_font)
        tw = tb[2] - tb[0]
        draw.text(((1200 - tw) / 2, 230), title, fill='white', font=title_font)

        sub = "Immobilier Côte d'Ivoire"
        sb = draw.textbbox((0, 0), sub, font=sub_font)
        sw = sb[2] - sb[0]
        draw.text(((1200 - sw) / 2, 340), sub, fill=(255, 255, 255, 200), font=sub_font)

        buf = io.BytesIO()
        img.save(buf, format='PNG', optimize=True)
        _fallback_image_cache = buf.getvalue()
    except Exception:
        import struct
        import zlib

        def _chunk(ctype, data):
            raw = ctype + data
            return (struct.pack('>I', len(data)) + raw
                    + struct.pack('>I', zlib.crc32(raw) & 0xFFFFFFFF))

        _fallback_image_cache = (
            b'\x89PNG\r\n\x1a\n'
            + _chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0))
            + _chunk(b'IDAT', zlib.compress(b'\x00\x1d\xa5\x3f'))
            + _chunk(b'IEND', b'')
        )

    return _fallback_image_cache


def _get_listing_image_field(listing):
    """Retourne le FileField de la meilleure image disponible, ou None."""
    first_image = listing.images.first()
    if first_image and first_image.image:
        return first_image.image
    first_video = listing.videos.first()
    if first_video and first_video.thumbnail:
        return first_video.thumbnail
    return None


def _ct_from_name(name: str) -> str:
    """Content-type from file extension."""
    name = (name or '').lower()
    if name.endswith('.png'):
        return 'image/png'
    if name.endswith('.webp'):
        return 'image/webp'
    return 'image/jpeg'


def _og_image_url(listing) -> str:
    """og:image URL on the same domain as the share page (routed by nginx ^~ /share/)."""
    return f'{FRONTEND_URL}/share/{listing.slug}/image.jpg'


def _og_image_type(listing) -> str:
    """og:image:type matching the actual file."""
    field = _get_listing_image_field(listing)
    return _ct_from_name(field.name) if field else _FALLBACK_CT


def _serve_image(data: bytes, content_type: str) -> HttpResponse:
    """HttpResponse with Content-Length and cache headers (WhatsApp needs Content-Length)."""
    resp = HttpResponse(data, content_type=content_type)
    resp['Content-Length'] = len(data)
    resp['Cache-Control'] = _IMAGE_CACHE
    return resp


class ListingShareImageView(APIView):
    """
    GET /api/share/<slug>/image.jpg
    Sert l'image en mémoire avec Content-Length exact.
    Jamais de redirect 302 (WhatsApp ne les suit pas pour les images).
    """

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = []

    def get(self, request, slug):
        try:
            listing = (
                Listing.objects
                .filter(slug=slug, status=Listing.Status.ACTIF)
                .prefetch_related('images', 'videos')
                .get()
            )
        except Listing.DoesNotExist:
            raise Http404

        file_field = _get_listing_image_field(listing)
        if not file_field:
            return _serve_image(_get_fallback_image(), _FALLBACK_CT)

        try:
            with file_field.open('rb') as f:
                data = f.read()
            return _serve_image(data, _ct_from_name(file_field.name))
        except Exception:
            return _serve_image(_get_fallback_image(), _FALLBACK_CT)


class ListingShareOGView(APIView):
    """Page OG pour le partage social d'une annonce."""

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = []

    def get(self, request, slug):
        try:
            listing = (
                Listing.objects
                .filter(slug=slug, status=Listing.Status.ACTIF)
                .select_related('agent')
                .prefetch_related('images', 'videos')
                .get()
            )
        except Listing.DoesNotExist:
            raise Http404

        spa_url = f'{FRONTEND_URL}/home/annonce/{listing.slug}'
        share_url = f'{FRONTEND_URL}/share/{listing.slug}/'

        is_bot = BOT_PATTERN.search(request.META.get('HTTP_USER_AGENT', ''))
        if not is_bot:
            return HttpResponse(status=302, headers={'Location': spa_url})

        og_title = listing.title

        price_fmt = f'{int(listing.price):,}'.replace(',', ' ')
        lt = 'Location' if listing.listing_type == 'LOCATION' else 'Vente'
        parts = [f'{lt} — {price_fmt} F CFA']
        if listing.city:
            loc = listing.city
            if listing.neighborhood:
                loc += f', {listing.neighborhood}'
            parts.append(loc)
        if listing.rooms:
            parts.append(f'{listing.rooms} pièces')
        if listing.surface_m2:
            parts.append(f'{int(listing.surface_m2)} m²')
        if listing.furnishing == 'FURNISHED':
            parts.append('Meublé')
        parts.append('*Visite Gratuite*')
        og_description = ' · '.join(parts)

        og_image = _og_image_url(listing)
        og_image_type = _og_image_type(listing)

        agent_name = ''
        agent_profile = getattr(listing.agent, 'agent_profile', None)
        if agent_profile:
            agent_name = getattr(agent_profile, 'agency_name', '') or ''
        if not agent_name:
            agent_name = listing.agent.username or listing.agent.phone or 'Agent MonaJent'

        cond_parts = []
        if listing.deposit_months:
            cond_parts.append(f'{listing.deposit_months} mois caution')
        if listing.advance_months:
            cond_parts.append(f'{listing.advance_months} mois avance')
        if listing.agency_fee_months:
            cond_parts.append(f'{listing.agency_fee_months} mois agence')
        conditions = ' + '.join(cond_parts)

        html = f'''<!DOCTYPE html>
<html lang="fr" prefix="og: https://ogp.me/ns#">
<head>
<meta charset="utf-8">
<title>{_e(og_title)} — MonaJent</title>
<meta name="description" content="{_e(og_description)}">

<meta property="og:type" content="article">
<meta property="og:site_name" content="MonaJent — Immobilier Côte d&#x27;Ivoire">
<meta property="og:title" content="{_e(og_title)}">
<meta property="og:description" content="{_e(og_description)}">
<meta property="og:url" content="{_e(share_url)}">
<meta property="og:image" content="{_e(og_image)}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:type" content="{_e(og_image_type)}">
<meta property="og:locale" content="fr_CI">
<meta property="article:author" content="{_e(agent_name)}">
<meta property="article:section" content="Immobilier">

<meta property="product:price:amount" content="{int(listing.price)}">
<meta property="product:price:currency" content="XOF">

<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@monajent">
<meta name="twitter:title" content="{_e(og_title)}">
<meta name="twitter:description" content="{_e(og_description)}">
<meta name="twitter:image" content="{_e(og_image)}">
<meta name="twitter:image:alt" content="{_e(og_title)} — MonaJent">

<link rel="canonical" href="{_e(share_url)}">
</head>
<body>
<h1>{_e(og_title)}</h1>
<p>{_e(og_description)}</p>
{f'<p>Conditions : {_e(conditions)}</p>' if conditions else ''}
<p>Agent : {_e(agent_name)}</p>
<p><a href="{_e(spa_url)}">Voir l&#x27;annonce sur MonaJent</a></p>
</body>
</html>'''
        return HttpResponse(html, content_type='text/html; charset=utf-8')


def _e(text) -> str:
    """Échappe les caractères HTML dans les attributs."""
    return (
        str(text or '')
        .replace('&', '&amp;')
        .replace('"', '&quot;')
        .replace("'", '&#x27;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
    )
