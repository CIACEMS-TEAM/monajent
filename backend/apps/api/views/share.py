"""
Open Graph share page — Monajent
─────────────────────────────────
GET /api/share/<slug>/

Sert une page HTML minimale avec les meta OG spécifiques à l'annonce.
- Bots (WhatsApp, Facebook, Twitter) → lisent les meta tags → aperçu riche
- Humains → redirect instantané vers la SPA
"""

import re

from django.conf import settings
from django.http import HttpResponse, Http404
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from apps.listings.models import Listing

FRONTEND_URL = getattr(settings, 'FRONTEND_URL', 'https://monajent.com').rstrip('/')

BOT_PATTERN = re.compile(
    r'facebookexternalhit|Facebot|Twitterbot|WhatsApp|LinkedInBot|'
    r'Slackbot|TelegramBot|Pinterest|Googlebot|Google-Read-Aloud|'
    r'Discordbot|Viber|Snapchat|redditbot',
    re.IGNORECASE,
)


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

        spa_url = f"{FRONTEND_URL}/home/annonce/{listing.slug}"
        share_url = f"{FRONTEND_URL}/share/{listing.slug}/"

        is_bot = BOT_PATTERN.search(request.META.get('HTTP_USER_AGENT', ''))
        if not is_bot:
            return HttpResponse(status=302, headers={'Location': spa_url})

        og_title = listing.title
        price_fmt = f"{int(listing.price):,}".replace(',', ' ')
        listing_type = 'Location' if listing.listing_type == 'LOCATION' else 'Vente'
        og_description = f"{listing_type} — {price_fmt} F CFA · {listing.city}"
        if listing.neighborhood:
            og_description += f", {listing.neighborhood}"
        if listing.rooms:
            og_description += f" · {listing.rooms} pièces"
        if listing.surface_m2:
            og_description += f" · {int(listing.surface_m2)} m²"
        og_description += " · Visite Gratuite !"

        og_image = ''
        first_image = listing.images.first()
        if first_image and first_image.image:
            img_url = first_image.image.url
            if img_url.startswith('http'):
                og_image = img_url
            else:
                og_image = request.build_absolute_uri(img_url)
        elif listing.videos.first() and listing.videos.first().thumbnail:
            thumb_url = listing.videos.first().thumbnail.url
            if thumb_url.startswith('http'):
                og_image = thumb_url
            else:
                og_image = request.build_absolute_uri(thumb_url)

        html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>{_esc(og_title)} — MonaJent</title>
<meta name="description" content="{_esc(og_description)}">

<meta property="og:type" content="article">
<meta property="og:site_name" content="MonaJent">
<meta property="og:title" content="{_esc(og_title)}">
<meta property="og:description" content="{_esc(og_description)}">
<meta property="og:url" content="{_esc(share_url)}">
<meta property="og:image" content="{_esc(og_image)}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="fr_CI">

<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{_esc(og_title)}">
<meta name="twitter:description" content="{_esc(og_description)}">
<meta name="twitter:image" content="{_esc(og_image)}">

</head>
<body>
<p><a href="{_esc(spa_url)}">Voir l'annonce sur MonaJent</a></p>
</body>
</html>"""
        return HttpResponse(html, content_type='text/html; charset=utf-8')


def _esc(text: str) -> str:
    """Échappe les caractères HTML dans les attributs."""
    return (
        str(text)
        .replace('&', '&amp;')
        .replace('"', '&quot;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
    )
