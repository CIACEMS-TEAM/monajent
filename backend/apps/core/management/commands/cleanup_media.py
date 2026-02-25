"""
Management command : cleanup_media
──────────────────────────────────
Supprime les fichiers médias des annonces expirées depuis N jours.

Usage :
    python manage.py cleanup_media                  # Dry run (comptage)
    python manage.py cleanup_media --execute        # Suppression réelle
    python manage.py cleanup_media --days 60        # Seuil personnalisé

En production, sera appelé via Celery beat (1x / mois par exemple).
"""

from django.core.management.base import BaseCommand

from apps.core.services.listing_lifecycle import cleanup_expired_media


class Command(BaseCommand):
    help = "Supprime les médias des annonces expirées depuis N jours."

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Nombre de jours après expiration avant suppression (défaut: 30).',
        )
        parser.add_argument(
            '--execute',
            action='store_true',
            help='Exécuter la suppression (par défaut: dry run).',
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = not options['execute']

        if dry_run:
            self.stdout.write(self.style.WARNING(
                f"MODE DRY RUN — Aucune suppression réelle (ajoutez --execute pour supprimer)."
            ))

        stats = cleanup_expired_media(days_after_expiry=days, dry_run=dry_run)

        self.stdout.write(self.style.SUCCESS(
            f"Résultat: {stats['listings_count']} annonces, "
            f"{stats['images_deleted']} images, "
            f"{stats['videos_deleted']} vidéos."
        ))
