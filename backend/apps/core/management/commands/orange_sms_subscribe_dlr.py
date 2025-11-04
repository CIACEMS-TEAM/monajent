from django.conf import settings
from django.core.management.base import BaseCommand

from apps.core.services.orange_sms import OrangeSmsClient


class Command(BaseCommand):
    help = "Souscrire aux notifications Orange DLR (Delivery Receipts) sur l'URL fournie."

    def add_arguments(self, parser):
        parser.add_argument('--notify-url', default=None, help='URL publique pour recevoir les DLR')

    def handle(self, *args, **options):
        notify_url = options['notify_url'] or getattr(settings, 'ORANGE_DLR_NOTIFY_URL', '')
        if not notify_url:
            self.stderr.write(self.style.ERROR('notify_url manquant. Utilise --notify-url ou ORANGE_DLR_NOTIFY_URL dans settings/.env'))
            return

        client = OrangeSmsClient()
        try:
            data = client.subscribe_dlr(notify_url)
            self.stdout.write(self.style.SUCCESS(str(data)))
        except Exception as exc:
            self.stderr.write(self.style.ERROR(str(exc)))



