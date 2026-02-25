from django.db.models.signals import pre_save
from django.dispatch import receiver

from .models import AgentProfile, Notification


@receiver(pre_save, sender=AgentProfile)
def notify_agent_kyc_change(sender, instance, **kwargs):
    """Create a notification when admin changes an agent's verified status."""
    if instance.pk is None:
        return

    try:
        old = AgentProfile.objects.get(pk=instance.pk)
    except AgentProfile.DoesNotExist:
        return

    if old.verified == instance.verified:
        return

    if instance.verified:
        Notification.objects.create(
            user=instance.user,
            category=Notification.Category.KYC,
            title='KYC approuvé',
            message=(
                'Félicitations ! Votre profil a été vérifié avec succès. '
                'Vous pouvez maintenant publier des annonces sur MonaJent.'
            ),
        )
    else:
        Notification.objects.create(
            user=instance.user,
            category=Notification.Category.KYC,
            title='KYC rejeté',
            message=(
                'Votre demande de vérification a été rejetée. '
                'Veuillez soumettre de nouveaux documents depuis vos paramètres.'
            ),
        )
