"""
Tâches Celery — MonaJent
────────────────────────
Wrappent les services existants pour exécution asynchrone et planifiée.
"""

import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)

PLATFORM_EMAIL = getattr(settings, 'PLATFORM_NOTIFY_EMAIL', 'info@monajent.com')
FROM_EMAIL = getattr(settings, 'DEFAULT_FROM_EMAIL', 'MonaJent <info@monajent.com>')


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


# ══════════════════════════════════════════════════════════════════
# Notifications email — Inscription & KYC
# ══════════════════════════════════════════════════════════════════

@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def send_agent_welcome_email(self, user_id: int):
    """
    Email de bienvenue envoyé à l'agent nouvellement inscrit
    + notification à la plateforme info@monajent.com.
    """
    try:
        from apps.users.models import User
        user = User.objects.select_related('agent_profile').get(pk=user_id)
        profile = getattr(user, 'agent_profile', None)
        agency = profile.agency_name if profile else ''
        display_name = user.username or user.phone
        frontend_url = getattr(settings, 'FRONTEND_URL', 'https://monajent.com')

        # ── 1. Email à l'agent (si email renseigné) ──────────
        if user.email:
            send_mail(
                subject='Bienvenue sur MonaJent !',
                message=(
                    f'Bonjour {display_name},\n\n'
                    f'Votre compte agent a été créé avec succès sur MonaJent.\n\n'
                    f'Prochaine étape : complétez votre vérification d\'identité (KYC) '
                    f'pour pouvoir publier vos annonces.\n\n'
                    f'Rendez-vous sur votre espace agent :\n'
                    f'{frontend_url}/agent/settings#kyc\n\n'
                    f'Cordialement,\n'
                    f'L\'équipe MonaJent'
                ),
                from_email=FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            logger.info('Email de bienvenue envoyé à %s', user.email)

        # ── 2. Notification à la plateforme ───────────────────
        send_mail(
            subject=f'[MonaJent] Nouvel agent inscrit : {display_name}',
            message=(
                f'Un nouvel agent vient de s\'inscrire sur MonaJent.\n\n'
                f'Téléphone : {user.phone}\n'
                f'Nom d\'utilisateur : {user.username or "—"}\n'
                f'Email : {user.email or "—"}\n'
                f'Agence : {agency or "—"}\n'
                f'Date : {user.created_at:%d/%m/%Y %H:%M}\n\n'
                f'— MonaJent Platform'
            ),
            from_email=FROM_EMAIL,
            recipient_list=[PLATFORM_EMAIL],
            fail_silently=False,
        )
        logger.info('Notification inscription agent envoyée à %s', PLATFORM_EMAIL)

    except Exception as exc:
        logger.exception('send_agent_welcome_email failed for user #%d', user_id)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def send_kyc_submitted_email(self, profile_id: int):
    """
    Notification envoyée quand un agent soumet son KYC :
    - À la plateforme info@monajent.com (pour review)
    - À l'agent (confirmation de réception)
    """
    try:
        from apps.users.models import AgentProfile
        profile = AgentProfile.objects.select_related('user').get(pk=profile_id)
        user = profile.user
        display_name = user.username or user.phone
        frontend_url = getattr(settings, 'FRONTEND_URL', 'https://monajent.com')

        # ── 1. Notification à la plateforme ───────────────────
        doc_count = profile.documents.count()
        send_mail(
            subject=f'[MonaJent KYC] Soumission de {display_name}',
            message=(
                f'L\'agent {display_name} a soumis ses documents KYC.\n\n'
                f'Téléphone : {user.phone}\n'
                f'Email : {user.email or "—"}\n'
                f'Agence : {profile.agency_name or "—"}\n'
                f'Documents soumis : {doc_count}\n\n'
                f'Vérifiez et traitez la demande dans l\'admin.\n\n'
                f'— MonaJent Platform'
            ),
            from_email=FROM_EMAIL,
            recipient_list=[PLATFORM_EMAIL],
            fail_silently=False,
        )
        logger.info('Notification KYC soumis envoyée à %s', PLATFORM_EMAIL)

        # ── 2. Confirmation à l'agent (si email) ─────────────
        if user.email:
            send_mail(
                subject='MonaJent — Documents KYC reçus',
                message=(
                    f'Bonjour {display_name},\n\n'
                    f'Nous avons bien reçu vos documents de vérification d\'identité.\n\n'
                    f'Notre équipe les examine dans les plus brefs délais. '
                    f'Vous recevrez une notification dès que la vérification sera terminée.\n\n'
                    f'Suivez l\'état de votre vérification :\n'
                    f'{frontend_url}/agent/settings#kyc\n\n'
                    f'Cordialement,\n'
                    f'L\'équipe MonaJent'
                ),
                from_email=FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            logger.info('Confirmation KYC soumis envoyée à %s', user.email)

    except Exception as exc:
        logger.exception('send_kyc_submitted_email failed for profile #%d', profile_id)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def send_kyc_approved_email(self, profile_id: int):
    """Email envoyé à l'agent quand son KYC est approuvé."""
    try:
        from apps.users.models import AgentProfile
        profile = AgentProfile.objects.select_related('user').get(pk=profile_id)
        user = profile.user
        display_name = user.username or user.phone
        frontend_url = getattr(settings, 'FRONTEND_URL', 'https://monajent.com')

        if not user.email:
            logger.info('Pas d\'email pour %s, notification KYC approuvé ignorée', user.phone)
            return

        send_mail(
            subject='MonaJent — Identité vérifiée ✓',
            message=(
                f'Bonjour {display_name},\n\n'
                f'Bonne nouvelle ! Votre identité a été vérifiée avec succès.\n\n'
                f'Vous pouvez maintenant publier vos annonces et '
                f'commencer à recevoir des clients sur MonaJent.\n\n'
                f'Publiez votre première annonce :\n'
                f'{frontend_url}/agent/listings\n\n'
                f'Cordialement,\n'
                f'L\'équipe MonaJent'
            ),
            from_email=FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        logger.info('Email KYC approuvé envoyé à %s', user.email)

    except Exception as exc:
        logger.exception('send_kyc_approved_email failed for profile #%d', profile_id)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def send_kyc_rejected_email(self, profile_id: int):
    """Email envoyé à l'agent quand son KYC est rejeté."""
    try:
        from apps.users.models import AgentProfile
        profile = AgentProfile.objects.select_related('user').get(pk=profile_id)
        user = profile.user
        display_name = user.username or user.phone
        reason = profile.kyc_rejection_reason or 'Document non conforme.'
        frontend_url = getattr(settings, 'FRONTEND_URL', 'https://monajent.com')

        if not user.email:
            logger.info('Pas d\'email pour %s, notification KYC rejeté ignorée', user.phone)
            return

        send_mail(
            subject='MonaJent — Vérification d\'identité à compléter',
            message=(
                f'Bonjour {display_name},\n\n'
                f'Votre vérification d\'identité n\'a pas pu être validée.\n\n'
                f'Motif : {reason}\n\n'
                f'Vous pouvez soumettre de nouveaux documents depuis votre espace agent :\n'
                f'{frontend_url}/agent/settings#kyc\n\n'
                f'Si vous avez des questions, n\'hésitez pas à ouvrir un ticket de support.\n\n'
                f'Cordialement,\n'
                f'L\'équipe MonaJent'
            ),
            from_email=FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        logger.info('Email KYC rejeté envoyé à %s', user.email)

    except Exception as exc:
        logger.exception('send_kyc_rejected_email failed for profile #%d', profile_id)
        raise self.retry(exc=exc)


# ══════════════════════════════════════════════════════════════════
# Notifications email — Visites
# ══════════════════════════════════════════════════════════════════

@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def send_visit_request_email(self, visit_id: int):
    """
    Notification email envoyée quand un client programme une visite :
    - À la plateforme (info@monajent.com)
    - À l'agent concerné (si email renseigné)
    Contient les infos du client, du bien et de l'agent.
    """
    try:
        from apps.visits.models import VisitRequest
        from apps.users.models import AgentProfile

        visit = (
            VisitRequest.objects
            .select_related('user', 'listing', 'listing__agent', 'slot')
            .get(pk=visit_id)
        )
        client = visit.user
        listing = visit.listing
        agent = listing.agent
        profile = getattr(agent, 'agent_profile', None)
        agency = profile.agency_name if profile else '—'
        frontend_url = getattr(settings, 'FRONTEND_URL', 'https://monajent.com')

        slot_info = '—'
        if visit.slot:
            days_fr = {
                'MONDAY': 'Lundi', 'TUESDAY': 'Mardi', 'WEDNESDAY': 'Mercredi',
                'THURSDAY': 'Jeudi', 'FRIDAY': 'Vendredi', 'SATURDAY': 'Samedi',
                'SUNDAY': 'Dimanche',
            }
            day = days_fr.get(visit.slot.day_of_week, visit.slot.day_of_week)
            slot_info = f'{day} {visit.slot.start_time:%Hh%M} — {visit.slot.end_time:%Hh%M}'

        scheduled_info = ''
        if visit.scheduled_at:
            scheduled_info = f'Date prévue : {visit.scheduled_at:%d/%m/%Y à %Hh%M}\n'

        note_info = ''
        if visit.client_note:
            note_info = f'Note du client : {visit.client_note}\n'

        body = (
            f'Nouvelle demande de visite sur MonaJent !\n'
            f'{"=" * 45}\n\n'
            f'BIEN IMMOBILIER\n'
            f'  Titre : {listing.title}\n'
            f'  Ville : {listing.city}'
            f'{" — " + listing.neighborhood if listing.neighborhood else ""}\n'
            f'  Prix : {listing.price:,.0f} F CFA\n'
            f'  Type : {listing.get_listing_type_display()}\n'
            f'  Lien : {frontend_url}/{listing.slug}\n\n'
            f'CLIENT DEMANDEUR\n'
            f'  Téléphone : {client.phone}\n'
            f'  Nom : {client.username or "—"}\n'
            f'  Email : {client.email or "—"}\n\n'
            f'AGENT CONCERNÉ\n'
            f'  Téléphone : {agent.phone}\n'
            f'  Nom : {agent.username or "—"}\n'
            f'  Email : {agent.email or "—"}\n'
            f'  Agence : {agency}\n\n'
            f'CRÉNEAU\n'
            f'  {slot_info}\n'
            f'{scheduled_info}'
            f'{note_info}\n'
            f'Statut : {visit.get_status_display()}\n'
            f'Code de vérification : {visit.verification_code}\n\n'
            f'— MonaJent Platform'
        )

        # ── 1. Notification à la plateforme ───────────────────
        send_mail(
            subject=f'[MonaJent] Nouvelle visite — {listing.title}',
            message=body,
            from_email=FROM_EMAIL,
            recipient_list=[PLATFORM_EMAIL],
            fail_silently=False,
        )
        logger.info('Email visite envoyé à plateforme (%s) pour visit #%d', PLATFORM_EMAIL, visit_id)

        # ── 2. Notification à l'agent (si email renseigné) ────
        if agent.email:
            agent_body = (
                f'Bonjour {agent.username or agent.phone},\n\n'
                f'Un client souhaite visiter votre bien « {listing.title} ».\n\n'
                f'CLIENT\n'
                f'  Téléphone : {client.phone}\n'
                f'  Nom : {client.username or "—"}\n\n'
                f'CRÉNEAU DEMANDÉ\n'
                f'  {slot_info}\n'
                f'{scheduled_info}'
                f'{note_info}\n'
                f'Connectez-vous pour confirmer ou gérer cette demande :\n'
                f'{frontend_url}/agent/visits\n\n'
                f'Cordialement,\n'
                f'L\'équipe MonaJent'
            )
            send_mail(
                subject=f'MonaJent — Nouvelle demande de visite pour « {listing.title} »',
                message=agent_body,
                from_email=FROM_EMAIL,
                recipient_list=[agent.email],
                fail_silently=False,
            )
            logger.info('Email visite envoyé à agent %s pour visit #%d', agent.email, visit_id)

    except Exception as exc:
        logger.exception('send_visit_request_email failed for visit #%d', visit_id)
        raise self.retry(exc=exc)
