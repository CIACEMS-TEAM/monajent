"""
Service cycle de vie des annonces — Monajent
─────────────────────────────────────────────
Gère l'expiration, le renouvellement, la suspension automatique
suite aux signalements, et le nettoyage des médias périmés.

Fonctions appelables depuis :
  • Management commands (immédiat)
  • Celery beat (périodique, en production)
"""

import logging
from datetime import timedelta

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.listings.models import Listing, ListingReport, LISTING_AUTO_SUSPEND_REPORTS

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# Expiration automatique
# ═══════════════════════════════════════════════════════════════


def expire_listings() -> int:
    """
    Passe en EXPIRED toutes les annonces ACTIVES dont expires_at est dépassé.
    Exécuté périodiquement (cron / Celery beat).

    Returns:
        Nombre d'annonces expirées.
    """
    now = timezone.now()
    expired_qs = Listing.objects.filter(
        status=Listing.Status.ACTIF,
        expires_at__lt=now,
    )
    count = expired_qs.update(status=Listing.Status.EXPIRED, updated_at=now)
    if count:
        logger.info("expire_listings: %d annonce(s) passée(s) en EXPIRED.", count)
    return count


# ═══════════════════════════════════════════════════════════════
# Suspension automatique (signalements)
# ═══════════════════════════════════════════════════════════════


def process_report(report: ListingReport) -> bool:
    """
    Traite un signalement : incrémente le compteur et suspend
    automatiquement si le seuil est atteint.

    Returns:
        True si l'annonce a été suspendue automatiquement.
    """
    listing = report.listing

    with transaction.atomic():
        # Incrémenter le compteur dénormalisé
        Listing.objects.filter(pk=listing.pk).update(
            reports_count=F('reports_count') + 1,
        )
        listing.refresh_from_db(fields=['reports_count'])

        # Vérifier le seuil
        if listing.reports_count >= LISTING_AUTO_SUSPEND_REPORTS:
            if listing.status == Listing.Status.ACTIF:
                Listing.objects.filter(pk=listing.pk).update(
                    status=Listing.Status.SUSPENDED,
                    updated_at=timezone.now(),
                )
                logger.warning(
                    "Annonce #%d « %s » auto-suspendue après %d signalements.",
                    listing.pk, listing.title, listing.reports_count,
                )
                return True

    return False


# ═══════════════════════════════════════════════════════════════
# Nettoyage des médias périmés
# ═══════════════════════════════════════════════════════════════


def find_expired_listings_for_cleanup(days_after_expiry: int = 30):
    """
    Trouve les annonces expirées depuis plus de N jours.
    Ces annonces et leurs médias (images + vidéos) peuvent être supprimées.

    Returns:
        QuerySet des Listing à nettoyer.
    """
    cutoff = timezone.now() - timedelta(days=days_after_expiry)
    return Listing.objects.filter(
        status=Listing.Status.EXPIRED,
        expires_at__lt=cutoff,
    ).select_related('agent')


def cleanup_expired_media(days_after_expiry: int = 30, dry_run: bool = True) -> dict:
    """
    Supprime les fichiers médias des annonces expirées depuis N jours.

    Args:
        days_after_expiry: Nombre de jours après expiration avant suppression.
        dry_run: Si True, ne supprime pas réellement (comptage uniquement).

    Returns:
        dict avec clés: listings_count, images_deleted, videos_deleted.
    """
    listings_qs = find_expired_listings_for_cleanup(days_after_expiry)

    stats = {
        'listings_count': listings_qs.count(),
        'images_deleted': 0,
        'videos_deleted': 0,
    }

    for listing in listings_qs.iterator():
        # Supprimer les fichiers images
        for img in listing.images.all():
            stats['images_deleted'] += 1
            if not dry_run:
                if img.image:
                    img.image.delete(save=False)
                img.delete()

        # Supprimer les fichiers vidéos
        for vid in listing.videos.all():
            stats['videos_deleted'] += 1
            if not dry_run:
                if vid.file:
                    vid.file.delete(save=False)
                if vid.thumbnail:
                    vid.thumbnail.delete(save=False)
                vid.delete()

        # Supprimer l'annonce elle-même
        if not dry_run:
            listing.delete()

    action = "DRY RUN" if dry_run else "SUPPRIMÉ"
    logger.info(
        "cleanup_expired_media [%s]: %d annonces, %d images, %d vidéos.",
        action, stats['listings_count'], stats['images_deleted'], stats['videos_deleted'],
    )
    return stats
