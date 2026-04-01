"""
Sitemap XML dynamique — Monajent
─────────────────────────────────
GET /api/sitemap.xml → Sitemap contenant toutes les annonces actives
                        et les pages statiques du frontend.
"""

from django.conf import settings
from django.http import HttpResponse
from django.utils.xmlutils import SimplerXMLGenerator
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from apps.listings.models import Listing

FRONTEND_URL = getattr(settings, 'FRONTEND_URL', 'https://monajent.com').rstrip('/')

STATIC_PAGES = [
    {'path': '/home',                      'changefreq': 'daily',   'priority': '1.0'},
    {'path': '/auth/login',                'changefreq': 'monthly', 'priority': '0.5'},
    {'path': '/auth/join',                 'changefreq': 'monthly', 'priority': '0.5'},
    {'path': '/legal/cgu',                 'changefreq': 'yearly',  'priority': '0.3'},
    {'path': '/legal/confidentialite',     'changefreq': 'yearly',  'priority': '0.3'},
    {'path': '/legal/conditions-agents',   'changefreq': 'yearly',  'priority': '0.3'},
]


class SitemapXMLView(APIView):
    """Génère un sitemap XML complet (pages statiques + annonces actives)."""

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = []

    def get(self, request):
        response = HttpResponse(content_type='application/xml; charset=utf-8')
        handler = SimplerXMLGenerator(response, 'utf-8')
        handler.startDocument()
        handler.startElement('urlset', {'xmlns': 'http://www.sitemaps.org/schemas/sitemap/0.9'})

        for page in STATIC_PAGES:
            self._add_url(handler, f"{FRONTEND_URL}{page['path']}", page['changefreq'], page['priority'])

        listings = (
            Listing.objects
            .filter(status=Listing.Status.ACTIF)
            .only('id', 'slug', 'updated_at')
            .order_by('-updated_at')
        )
        for listing in listings.iterator(chunk_size=500):
            lastmod = listing.updated_at.strftime('%Y-%m-%d') if listing.updated_at else None
            self._add_url(
                handler,
                f"{FRONTEND_URL}/home/annonce/{listing.slug}",
                changefreq='weekly',
                priority='0.8',
                lastmod=lastmod,
            )

        handler.endElement('urlset')
        handler.endDocument()
        return response

    @staticmethod
    def _add_url(handler, loc, changefreq, priority, lastmod=None):
        handler.startElement('url', {})
        handler.addQuickElement('loc', loc)
        if lastmod:
            handler.addQuickElement('lastmod', lastmod)
        handler.addQuickElement('changefreq', changefreq)
        handler.addQuickElement('priority', priority)
        handler.endElement('url')
