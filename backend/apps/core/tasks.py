"""
Tâches Celery — MonaJent
────────────────────────
Wrappent les services existants pour exécution asynchrone et planifiée.
"""

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def expire_listings_task(self):
    """Expire les annonces actives dont la date d'expiration est dépassée."""
    try:
        from apps.core.services.listing_lifecycle import expire_listings
        count = expire_listings()
        logger.info('expire_listings_task: %d annonce(s) expirée(s)', count)
        return count
    except Exception as exc:
        logger.exception('expire_listings_task failed')
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def auto_cancel_visits_task(self):
    """Expire les visites sans réponse agent et restaure les clés physiques."""
    try:
        from apps.core.services.visits import expire_unresponded_visits
        count = expire_unresponded_visits()
        logger.info('auto_cancel_visits_task: %d visite(s) expirée(s)', count)
        return count
    except Exception as exc:
        logger.exception('auto_cancel_visits_task failed')
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=1, default_retry_delay=300)
def cleanup_media_task(self):
    """Nettoie les médias des annonces expirées depuis 30+ jours."""
    try:
        from apps.core.services.listing_lifecycle import cleanup_expired_media
        stats = cleanup_expired_media(days_after_expiry=30, dry_run=False)
        logger.info(
            'cleanup_media_task: %d annonces, %d images, %d vidéos supprimées',
            stats['listings_count'], stats['images_deleted'], stats['videos_deleted'],
        )
        return stats
    except Exception as exc:
        logger.exception('cleanup_media_task failed')
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def generate_video_thumbnail_task(self, video_id: int):
    """Génère le thumbnail d'une vidéo en arrière-plan (post-upload)."""
    try:
        from apps.listings.models import Video
        from apps.core.services.video_thumbnail import generate_thumbnail

        video = Video.objects.get(pk=video_id)
        if video.thumbnail:
            return

        if not video.file:
            logger.warning('Video %d has no file — skipping thumbnail', video_id)
            return

        thumb = generate_thumbnail(video.file)
        if thumb:
            video.thumbnail.save(thumb.name, thumb, save=True)
            logger.info('Thumbnail généré pour video %d', video_id)
        else:
            logger.warning('Thumbnail generation returned None for video %d', video_id)
    except Exception as exc:
        logger.exception('generate_video_thumbnail_task failed for video %d', video_id)
        raise self.retry(exc=exc)
