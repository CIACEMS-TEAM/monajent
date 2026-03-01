"""
Management command : auto_cancel_visits
───────────────────────────────────────
Expire les visites REQUESTED dont le délai de réponse agent est dépassé.
Restaure la clé physique au client.

Usage :
    python manage.py auto_cancel_visits

En production, sera appelé via Celery beat (toutes les heures par exemple).
"""

from django.core.management.base import BaseCommand

from apps.core.services.visits import expire_unresponded_visits


class Command(BaseCommand):
    help = "Expire les visites dont l'agent n'a pas répondu dans le délai imparti."

    def handle(self, *args, **options):
        count = expire_unresponded_visits()
        self.stdout.write(
            self.style.SUCCESS(f"{count} visite(s) expirée(s), clés physiques restaurées.")
        )
