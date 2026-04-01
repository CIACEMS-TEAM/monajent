"""
Tâches Celery — Support Monajent
─────────────────────────────────
Notifications email pour le système de tickets.
"""

import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)

TEAM_EMAIL = getattr(settings, 'DEFAULT_FROM_EMAIL', 'info@monajent.com')


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def send_ticket_created_email(self, ticket_id: int):
    """Notifie l'équipe MonaJent qu'un nouveau ticket a été créé."""
    try:
        from apps.support.models import SupportTicket
        ticket = SupportTicket.objects.select_related('user').get(pk=ticket_id)
        first_msg = ticket.messages.first()

        send_mail(
            subject=f'[Support MonaJent] Nouveau ticket #{ticket.pk}: {ticket.subject}',
            message=(
                f'Un nouveau ticket de support a été créé.\n\n'
                f'Utilisateur : {ticket.user.phone} ({ticket.user.username or "—"})\n'
                f'Catégorie : {ticket.get_category_display()}\n'
                f'Sujet : {ticket.subject}\n\n'
                f'Message :\n{first_msg.content if first_msg else "(vide)"}\n\n'
                f'— MonaJent Support'
            ),
            from_email=TEAM_EMAIL,
            recipient_list=[settings.SERVER_EMAIL],
            fail_silently=False,
        )
        logger.info('Email envoyé pour le ticket #%d', ticket_id)
    except Exception as exc:
        logger.exception('send_ticket_created_email failed for ticket #%d', ticket_id)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def send_ticket_reply_email(self, message_id: int):
    """Notifie l'utilisateur qu'un admin a répondu à son ticket."""
    try:
        from apps.support.models import SupportMessage
        msg = SupportMessage.objects.select_related(
            'ticket', 'ticket__user',
        ).get(pk=message_id)

        user = msg.ticket.user
        user_email = user.email
        if not user_email:
            logger.info(
                'Pas d\'email pour l\'utilisateur %s, notification ignorée', user.phone,
            )
            return

        send_mail(
            subject=f'[MonaJent] Réponse à votre ticket #{msg.ticket.pk}: {msg.ticket.subject}',
            message=(
                f'Bonjour {user.username or user.phone},\n\n'
                f'L\'équipe MonaJent a répondu à votre ticket :\n\n'
                f'"{msg.content[:500]}"\n\n'
                f'Connectez-vous à MonaJent pour voir la réponse complète '
                f'et continuer la conversation.\n\n'
                f'Cordialement,\n'
                f'L\'équipe MonaJent'
            ),
            from_email=TEAM_EMAIL,
            recipient_list=[user_email],
            fail_silently=False,
        )
        logger.info('Email réponse envoyé pour message #%d (ticket #%d)', message_id, msg.ticket_id)
    except Exception as exc:
        logger.exception('send_ticket_reply_email failed for message #%d', message_id)
        raise self.retry(exc=exc)
