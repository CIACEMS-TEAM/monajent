from django.core.management.base import BaseCommand, CommandParser

from apps.core.services.orange_sms import OrangeSmsClient


class Command(BaseCommand):
    help = "Diagnostics Orange SMS: contrats, achats, statistiques, envoi test."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument('--country', default='CIV', help='Code pays ISO-3 (ex: CIV) pour stats/achats')
        parser.add_argument('--test-to', default=None, help='Numéro MSISDN destinataire pour un envoi test')
        parser.add_argument('--test-message', default='Test Monajent', help='Message test à envoyer')
        parser.add_argument('--skip-contracts', action='store_true')
        parser.add_argument('--skip-purchases', action='store_true')
        parser.add_argument('--skip-stats', action='store_true')

    def handle(self, *args, **options):
        client = OrangeSmsClient()

        if not options['skip_contracts']:
            self.stdout.write(self.style.MIGRATE_HEADING('== Contrats =='))
            try:
                data = client.get_contracts(country=options['country'])
                self.stdout.write(str(data))
            except Exception as exc:
                self.stderr.write(self.style.ERROR(f'Contracts error: {exc}'))

        if not options['skip_purchases']:
            self.stdout.write(self.style.MIGRATE_HEADING('== Achats =='))
            try:
                data = client.get_purchase_orders(country=options['country'])
                self.stdout.write(str(data))
            except Exception as exc:
                self.stderr.write(self.style.ERROR(f'Purchase error: {exc}'))

        if not options['skip_stats']:
            self.stdout.write(self.style.MIGRATE_HEADING('== Statistiques =='))
            try:
                data = client.get_statistics(country=options['country'])
                self.stdout.write(str(data))
            except Exception as exc:
                self.stderr.write(self.style.ERROR(f'Stats error: {exc}'))

        to = options['test_to']
        if to:
            self.stdout.write(self.style.MIGRATE_HEADING('== Envoi test =='))
            try:
                data = client.send_sms(to, options['test_message'])
                self.stdout.write(str(data))
            except Exception as exc:
                self.stderr.write(self.style.ERROR(f'Send error: {exc}'))



