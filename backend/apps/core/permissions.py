"""
Permissions métier — Monajent
─────────────────────────────
Permissions réutilisables pour les vues DRF.
Combinables entre elles : permission_classes = [IsAuthenticated, IsAgent, IsListingOwner]

IMPORTANT — Performance :
Les permissions objet (has_object_permission) accèdent aux FK. Pour éviter
les requêtes N+1, les vues DOIVENT utiliser select_related() sur les FK
traversées par la permission. Exemples documentés ci-dessous.
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS


# ═══════════════════════════════════════════════════════════════
# Permissions basées sur le rôle (has_permission → niveau vue)
# ═══════════════════════════════════════════════════════════════


class IsAgent(BasePermission):
    """
    Accès réservé aux utilisateurs avec role=AGENT.
    Usage : Listing CRUD, Wallet, Stats, Video upload.
    """
    message = "Accès réservé aux agents immobiliers."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'AGENT'
        )


class IsClient(BasePermission):
    """
    Accès réservé aux utilisateurs avec role=CLIENT.
    Usage : Achat packs, Favoris, Visites, SavedSearch, Visionnage vidéo.
    """
    message = "Accès réservé aux clients."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'CLIENT'
        )


class IsAdmin(BasePermission):
    """
    Accès réservé aux administrateurs (role=ADMIN ou is_staff).
    Usage : Gestion plateforme, modération, stats globales.
    """
    message = "Accès réservé aux administrateurs."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (request.user.role == 'ADMIN' or request.user.is_staff)
        )


class IsVerifiedAgent(BasePermission):
    """
    Accès réservé aux agents dont le profil est vérifié (KYC validé).
    Usage : Publication d'annonces, upload vidéo.

    Perf : la vue devrait pré-charger le profil via
           select_related('agent_profile') ou un middleware.
    """
    message = "Votre profil agent doit être vérifié pour effectuer cette action."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated and request.user.role == 'AGENT'):
            return False
        profile = getattr(request.user, 'agent_profile', None)
        return profile is not None and profile.verified


# ═══════════════════════════════════════════════════════════════
# Permissions au niveau objet (has_object_permission)
# ═══════════════════════════════════════════════════════════════


class IsListingOwner(BasePermission):
    """
    L'agent ne peut modifier / supprimer que SES propres annonces.
    Fonctionne sur les objets Listing, ListingImage, Video.

    Perf : la vue doit utiliser select_related('listing') pour
           ListingImage et Video (évite 1 query par objet).
    """
    message = "Vous ne pouvez modifier que vos propres annonces."

    def has_object_permission(self, request, view, obj):
        # Remonter au Listing si l'objet est une Image ou une Video
        if hasattr(obj, 'listing_id') and hasattr(obj, 'listing'):
            # Video ou ListingImage → utiliser listing_id pour éviter le query
            # si listing n'est pas pré-chargé, accéder à l'ID FK directement
            return obj.listing.agent_id == request.user.id
        # L'objet EST un Listing
        return obj.agent_id == request.user.id


class IsObjectOwner(BasePermission):
    """
    Permission générique : l'objet appartient à l'utilisateur courant.
    Vérifie obj.user_id == request.user.id.

    Fonctionne pour : PackPurchase, Payment, FavoriteListing, SavedSearch.
    """
    message = "Vous ne pouvez accéder qu'à vos propres données."

    def has_object_permission(self, request, view, obj):
        return obj.user_id == request.user.id


class IsWalletOwner(BasePermission):
    """
    L'agent ne peut accéder qu'à SON propre wallet.
    Fonctionne sur Wallet et WalletEntry.

    Perf : la vue WalletEntry doit utiliser select_related('wallet')
           pour éviter 1 query par entrée.
    """
    message = "Vous ne pouvez accéder qu'à votre propre portefeuille."

    def has_object_permission(self, request, view, obj):
        # WalletEntry → remonter au Wallet
        wallet = getattr(obj, 'wallet', obj)
        return wallet.agent_id == request.user.id


class IsVisitParticipant(BasePermission):
    """
    Accès à une VisitRequest si l'utilisateur est :
    - le client demandeur, OU
    - l'agent propriétaire de l'annonce.

    Perf : la vue doit utiliser select_related('listing') pour
           éviter 1 query lors de la vérification agent.
    """
    message = "Vous n'êtes pas concerné par cette demande de visite."

    def has_object_permission(self, request, view, obj):
        user = request.user
        # Le client qui a demandé la visite
        if obj.user_id == user.id:
            return True
        # L'agent propriétaire de l'annonce
        if obj.listing.agent_id == user.id:
            return True
        return False


class IsVisitAgent(BasePermission):
    """
    Seul l'agent propriétaire de l'annonce peut modifier le statut
    de la visite (confirmer, marquer DONE, NO_SHOW).
    Le client ne peut que lire ou annuler.

    Perf : la vue doit utiliser select_related('listing').
    """
    message = "Seul l'agent de cette annonce peut effectuer cette action."

    def has_object_permission(self, request, view, obj):
        return obj.listing.agent_id == request.user.id


class IsViewUsageParticipant(BasePermission):
    """
    Accès à un VirtualKeyUsage si l'utilisateur est :
    - le client qui a visionné (obj.user_id), OU
    - l'agent bénéficiaire (obj.agent_id).

    Usage : historique de vues (client) ou stats détaillées (agent).
    """
    message = "Vous n'êtes pas concerné par ce visionnage."

    def has_object_permission(self, request, view, obj):
        return obj.user_id == request.user.id or obj.agent_id == request.user.id


# ═══════════════════════════════════════════════════════════════
# Permission lecture publique / écriture propriétaire
# ═══════════════════════════════════════════════════════════════


class IsOwnerOrReadOnly(BasePermission):
    """
    Lecture (GET, HEAD, OPTIONS) pour tous les authentifiés.
    Écriture (PUT, PATCH, DELETE) réservée au propriétaire.

    Le champ propriétaire est déterminé par `owner_field` sur la vue
    (défaut: 'agent' pour les Listings).

    Usage :
        class ListingDetailView(RetrieveUpdateDestroyAPIView):
            owner_field = 'agent'
            permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    """
    message = "Modification réservée au propriétaire."

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        owner_field = getattr(view, 'owner_field', 'agent')
        owner = getattr(obj, owner_field, None)
        if owner is None:
            return False
        # Supporter à la fois FK objet (owner.id) et FK ID brut (owner_field + '_id')
        owner_id = getattr(obj, f'{owner_field}_id', None) or getattr(owner, 'id', owner)
        return owner_id == request.user.id
