"""
Vues Dashboard & Analytics — Monajent (Agent)
──────────────────────────────────────────────
    GET /api/agent/dashboard/   → Vue consolidée (solde, visites en attente, derniers mouvements, stats rapides)
    GET /api/agent/analytics/   → Statistiques détaillées (vues par jour, top listings, tendances)
"""

from datetime import timedelta
from collections import defaultdict

from django.db.models import Sum, Count, Q
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsAgent
from apps.wallet.models import Wallet, WalletEntry
from apps.visits.models import VisitRequest
from apps.listings.models import Listing
from apps.packs.models import VirtualKeyUsage


class AgentDashboardView(APIView):
    """
    GET /api/agent/dashboard/
    Résumé consolidé pour la page d'accueil du dashboard agent.
    """
    permission_classes = [IsAuthenticated, IsAgent]

    def get(self, request):
        user = request.user

        wallet, _ = Wallet.objects.get_or_create(agent=user)

        listings = Listing.objects.filter(agent=user).exclude(status=Listing.Status.DELETED)
        listings_count = listings.count()
        published_count = listings.filter(status=Listing.Status.ACTIF).count()
        total_views = listings.aggregate(total=Sum('views_count'))['total'] or 0
        total_favorites = listings.aggregate(total=Sum('favorites_count'))['total'] or 0

        pending_visits = VisitRequest.objects.filter(
            listing__agent=user,
            status=VisitRequest.Status.REQUESTED,
        ).count()

        recent_entries = WalletEntry.objects.filter(wallet=wallet).order_by('-created_at')[:5]
        entries_data = [
            {
                'id': e.id,
                'entry_type': e.entry_type,
                'source_label': e.get_source_display(),
                'amount': str(e.amount),
                'label': e.label,
                'created_at': e.created_at.isoformat(),
            }
            for e in recent_entries
        ]

        def _listing_cover(listing_obj):
            """Retourne l'URL de couverture (image ou thumbnail vidéo)."""
            img = listing_obj.images.first()
            if img and img.image:
                return request.build_absolute_uri(img.image.url)
            vid = listing_obj.videos.first()
            if vid and vid.thumbnail:
                return request.build_absolute_uri(vid.thumbnail.url)
            return None

        latest_obj = listings.prefetch_related('images', 'videos').order_by('-created_at').first()
        latest_listing = None
        if latest_obj:
            latest_listing = {
                'id': latest_obj.id,
                'title': latest_obj.title,
                'views_count': latest_obj.views_count,
                'favorites_count': latest_obj.favorites_count,
                'price': str(latest_obj.price),
                'created_at': latest_obj.created_at.isoformat(),
                'cover_image': _listing_cover(latest_obj),
            }

        top_qs = (
            listings
            .filter(status=Listing.Status.ACTIF)
            .prefetch_related('images', 'videos')
            .order_by('-views_count')[:3]
        )
        top_listings = [
            {
                'id': l.id,
                'title': l.title,
                'views_count': l.views_count,
                'favorites_count': l.favorites_count,
                'cover_image': _listing_cover(l),
            }
            for l in top_qs
        ]

        now = timezone.now()
        views_28d = VirtualKeyUsage.objects.filter(
            agent=user,
            created_at__gte=now - timedelta(days=28),
        ).count()

        return Response({
            'wallet': {
                'balance': str(wallet.balance),
                'total_earned': str(wallet.total_earned),
                'total_withdrawn': str(wallet.total_withdrawn),
                'has_pin': wallet.has_pin,
            },
            'listings': {
                'total': listings_count,
                'published': published_count,
                'total_views': total_views,
                'total_favorites': total_favorites,
            },
            'pending_visits': pending_visits,
            'recent_entries': entries_data,
            'latest_listing': latest_listing,
            'top_listings': top_listings,
            'views_28d': views_28d,
        })


class AgentAnalyticsView(APIView):
    """
    GET /api/agent/analytics/
    Statistiques détaillées : vues par jour sur 28j, top listings, tendances.
    """
    permission_classes = [IsAuthenticated, IsAgent]

    def get(self, request):
        user = request.user
        now = timezone.now()

        from datetime import date as _date
        raw_start = request.query_params.get('start_date')
        raw_end = request.query_params.get('end_date')
        try:
            end_date = _date.fromisoformat(raw_end) if raw_end else now.date()
            start_date = _date.fromisoformat(raw_start) if raw_start else end_date - timedelta(days=27)
        except (ValueError, TypeError):
            end_date = now.date()
            start_date = end_date - timedelta(days=27)

        start_dt = timezone.make_aware(timezone.datetime.combine(start_date, timezone.datetime.min.time()))
        end_dt = timezone.make_aware(timezone.datetime.combine(end_date, timezone.datetime.max.time()))
        num_days = (end_date - start_date).days + 1

        usages_qs = VirtualKeyUsage.objects.filter(
            agent=user,
            created_at__gte=start_dt,
            created_at__lte=end_dt,
        )

        daily_views = defaultdict(int)
        for u in usages_qs.values_list('created_at', flat=True):
            daily_views[u.date().isoformat()] += 1

        daily_stats = []
        for i in range(num_days):
            d = (start_date + timedelta(days=i))
            key = d.isoformat()
            daily_stats.append({'date': key, 'views': daily_views.get(key, 0)})

        total_views_period = sum(d['views'] for d in daily_stats)

        prev_start_dt = start_dt - timedelta(days=num_days)
        prev_views = VirtualKeyUsage.objects.filter(
            agent=user,
            created_at__gte=prev_start_dt,
            created_at__lt=start_dt,
        ).count()

        if prev_views > 0:
            trend_pct = round(((total_views_period - prev_views) / prev_views) * 100, 1)
        else:
            trend_pct = 100.0 if total_views_period > 0 else 0.0

        listings = Listing.objects.filter(agent=user).exclude(status=Listing.Status.DELETED)
        total_views_all = listings.aggregate(total=Sum('views_count'))['total'] or 0
        total_favorites_all = listings.aggregate(total=Sum('favorites_count'))['total'] or 0
        published_count = listings.filter(status=Listing.Status.ACTIF).count()
        listings_count = listings.count()

        top_listings = list(
            listings
            .filter(status=Listing.Status.ACTIF)
            .order_by('-views_count')
            .values('id', 'title', 'views_count', 'favorites_count')
        )

        avg_views = round(total_views_all / max(listings_count, 1), 1)

        visits_done = VisitRequest.objects.filter(
            listing__agent=user,
            status=VisitRequest.Status.DONE,
        ).count()

        visits_total = VisitRequest.objects.filter(
            listing__agent=user,
        ).count()

        visit_conversion = round((visits_done / max(visits_total, 1)) * 100, 1)

        from apps.listings.models import ListingReport
        total_reports = ListingReport.objects.filter(listing__agent=user).count()
        reports_by_reason = list(
            ListingReport.objects.filter(listing__agent=user)
            .values('reason')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        reason_labels = dict(ListingReport.Reason.choices)
        for item in reports_by_reason:
            item['reason_label'] = reason_labels.get(item['reason'], item['reason'])

        return Response({
            'daily_stats': daily_stats,
            'total_views_28d': total_views_period,
            'period_days': num_days,
            'trend_pct': trend_pct,
            'summary': {
                'total_views': total_views_all,
                'total_favorites': total_favorites_all,
                'total_reports': total_reports,
                'published_count': published_count,
                'total_listings': listings_count,
                'avg_views_per_listing': avg_views,
            },
            'top_listings': top_listings,
            'reports_by_reason': reports_by_reason,
            'visits': {
                'done': visits_done,
                'total': visits_total,
                'conversion_pct': visit_conversion,
            },
        })
