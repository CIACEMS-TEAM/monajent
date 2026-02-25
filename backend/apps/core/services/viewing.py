"""
Service de visionnage — Monajent
────────────────────────────────
Transaction atomique : le client consomme 1 clé virtuelle pour voir une vidéo.

Opérations dans une seule transaction DB :
1. Verrouiller le pack (select_for_update) pour éviter les races
2. Créer VirtualKeyUsage (anti-double via UNIQUE constraint)
3. Incrémenter pack.virtual_used
4. Créditer le wallet de l'agent (+10 XOF)
5. Enregistrer PlatformRevenue (+5 XOF)
6. Incrémenter les compteurs dénormalisés (video.views_count, listing.views_count)
"""

from django.db import transaction
from django.db.models import F

from apps.packs.models import (
    PackPurchase, VirtualKeyUsage,
    AGENT_REVENUE_PER_VIEW, PLATFORM_REVENUE_PER_VIEW,
)
from apps.wallet.models import Wallet, WalletEntry, PlatformRevenue
from apps.listings.models import Video


class ViewingError(Exception):
    """Erreur métier lors du visionnage."""
    pass


class NoActivePackError(ViewingError):
    """Le client n'a aucun pack actif avec des clés restantes."""
    pass


class AlreadyWatchedError(ViewingError):
    """Le client a déjà vu cette vidéo (retour gratuit de l'URL)."""
    def __init__(self, usage: VirtualKeyUsage):
        self.usage = usage
        super().__init__("Vidéo déjà visionnée avec ce pack.")


def _find_active_pack(user) -> PackPurchase:
    """
    Trouve le pack actif du client : non verrouillé, avec des clés restantes.
    Utilise select_for_update pour verrouiller la ligne (anti-race condition).
    Prend le pack le plus ancien avec des clés restantes (FIFO).
    """
    pack = (
        PackPurchase.objects
        .select_for_update()
        .filter(
            user=user,
            is_locked_by_visit=False,
        )
        .extra(where=["virtual_total - virtual_used > 0"])
        .order_by('created_at')
        .first()
    )
    if pack is None:
        raise NoActivePackError("Aucun pack actif avec des clés restantes.")
    return pack


def consume_virtual_key(user, video: Video) -> dict:
    """
    Consomme 1 clé virtuelle pour visionner une vidéo.

    Returns:
        dict avec les clés : usage, pack, video_url, already_watched

    Raises:
        NoActivePackError: si aucun pack actif
        AlreadyWatchedError: si déjà vu (l'URL est quand même retournée)
    """
    # Vérifier si déjà vu (toutes packs confondus) → retour gratuit
    existing = (
        VirtualKeyUsage.objects
        .filter(user=user, video=video)
        .select_related('pack')
        .first()
    )
    if existing:
        raise AlreadyWatchedError(existing)

    with transaction.atomic():
        # 1. Trouver et verrouiller le pack actif
        pack = _find_active_pack(user)

        # 2. Créer le VirtualKeyUsage
        agent = video.listing.agent
        usage = VirtualKeyUsage.objects.create(
            pack=pack,
            video=video,
            user=user,
            agent=agent,
            amount_agent=AGENT_REVENUE_PER_VIEW,
            amount_platform=PLATFORM_REVENUE_PER_VIEW,
        )

        # 3. Incrémenter virtual_used sur le pack
        PackPurchase.objects.filter(pk=pack.pk).update(
            virtual_used=F('virtual_used') + 1,
        )

        # 4. Créditer le wallet de l'agent
        wallet, _ = Wallet.objects.get_or_create(agent=agent)
        Wallet.objects.filter(pk=wallet.pk).update(
            balance=F('balance') + AGENT_REVENUE_PER_VIEW,
            total_earned=F('total_earned') + AGENT_REVENUE_PER_VIEW,
        )
        WalletEntry.objects.create(
            wallet=wallet,
            entry_type=WalletEntry.EntryType.CREDIT,
            source=WalletEntry.Source.VIDEO_VIEW,
            amount=AGENT_REVENUE_PER_VIEW,
            label=f"Vue vidéo #{video.pk} — {video.listing.title}",
            ref_usage=usage,
        )

        # 5. Enregistrer le revenu plateforme
        PlatformRevenue.objects.create(
            source=PlatformRevenue.Source.VIDEO_VIEW,
            usage=usage,
            amount=PLATFORM_REVENUE_PER_VIEW,
        )

        # 6. Incrémenter les compteurs dénormalisés
        Video.objects.filter(pk=video.pk).update(
            views_count=F('views_count') + 1,
        )
        video.listing.__class__.objects.filter(pk=video.listing_id).update(
            views_count=F('views_count') + 1,
        )

        # Rafraîchir le pack pour retourner les valeurs à jour
        pack.refresh_from_db()

    return {
        'usage': usage,
        'pack': pack,
        'already_watched': False,
    }
