"""
Throttles métier — Monajent
───────────────────────────
Limitations de débit pour les endpoints métier.
Les scopes sont définis ici et les taux dans settings.DEFAULT_THROTTLE_RATES.

Scopes listings agent (dashboard) :
  - agent_listing_read   : GET liste / détail — quota large (actualisations)
  - agent_listing_mutate : PATCH, DELETE, bulk, renew — modifs groupées
  - listing_create       : POST nouvelle annonce uniquement

Usage dans une vue :
    throttle_classes = [ListingCreateThrottle]
  ou
    throttle_scope = 'listing_create'  (avec ScopedRateThrottle par défaut)
"""

from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


# ── Listings ──────────────────────────────────────────────────


class ListingCreateThrottle(UserRateThrottle):
    """Limite la création d'annonces par agent."""
    scope = 'listing_create'


class ListingSearchThrottle(AnonRateThrottle):
    """Limite les recherches d'annonces (anon + auth)."""
    scope = 'listing_search'


# ── Vidéos / Visionnage ──────────────────────────────────────


class VideoViewThrottle(UserRateThrottle):
    """Limite la consommation de clés virtuelles (visionnage)."""
    scope = 'video_view'


class VideoUploadThrottle(UserRateThrottle):
    """Limite l'upload de vidéos par agent."""
    scope = 'video_upload'


# ── Packs ─────────────────────────────────────────────────────


class PackPurchaseThrottle(UserRateThrottle):
    """Limite l'achat de packs."""
    scope = 'pack_purchase'


# ── Visites ───────────────────────────────────────────────────


class VisitRequestThrottle(UserRateThrottle):
    """Limite les demandes de visite."""
    scope = 'visit_request'


# ── Wallet / Retraits ────────────────────────────────────────


class WalletWithdrawThrottle(UserRateThrottle):
    """Limite les demandes de retrait."""
    scope = 'wallet_withdraw'


# ── Favoris ───────────────────────────────────────────────────


class FavoriteToggleThrottle(UserRateThrottle):
    """Limite l'ajout/suppression de favoris."""
    scope = 'favorite_toggle'
