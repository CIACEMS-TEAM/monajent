from django.db.models.signals import pre_save
from django.dispatch import receiver

from .models import AgentProfile, Notification


@receiver(pre_save, sender=AgentProfile)
def sync_kyc_status_and_notify(sender, instance, **kwargs):
    """Synchronise kyc_status avec verified et envoie une notification."""
    if instance.pk is None:
        return

    try:
        old = AgentProfile.objects.get(pk=instance.pk)
    except AgentProfile.DoesNotExist:
        return

    if old.verified == instance.verified:
        return

    if instance.verified:
        instance.kyc_status = AgentProfile.KycStatus.APPROVED
        instance.kyc_rejection_reason = ''
        Notification.objects.create(
            user=instance.user,
            category=Notification.Category.KYC,
            title='KYC approuvé',
            message=(
                'Félicitations ! Votre profil a été vérifié avec succès. '
                'Vous pouvez maintenant publier des annonces sur MonaJent.'
            ),
            link='/agent/settings#kyc',
        )
    else:
        instance.kyc_status = AgentProfile.KycStatus.REJECTED
        Notification.objects.create(
            user=instance.user,
            category=Notification.Category.KYC,
            title='KYC rejeté',
            message=(
                'Votre demande de vérification a été rejetée. '
                'Veuillez soumettre de nouveaux documents depuis vos paramètres.'
            ),
            link='/agent/settings#kyc',
        )
