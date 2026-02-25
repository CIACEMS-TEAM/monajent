"""
Management command : expire_listings
────────────────────────────────────
Passe en EXPIRED les annonces ACTIVES dont la date d'expiration est dépassée.

Usage :
    python manage.py expire_listings

En production, sera appelé via Celery beat (toutes les heures par exemple).
"""

from django.core.management.base import BaseCommand

from apps.core.services.listing_lifecycle import expire_listings


class Command(BaseCommand):
    help = "Expire les annonces actives dont la date d'expiration est dépassée."

    def handle(self, *args, **options):
        count = expire_listings()
        self.stdout.write(
            self.style.SUCCESS(f"{count} annonce(s) expirée(s).")
        )
