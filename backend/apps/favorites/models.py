"""
Modèles FavoriteListing & SavedSearch
──────────────────────────────────────
Confort client : favoris et recherches sauvegardées.
"""

from django.conf import settings
from django.db import models


class FavoriteListing(models.Model):
    """Annonce mise en favori par un client."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favorites',
        limit_choices_to={'role': 'CLIENT'},
    )
    listing = models.ForeignKey(
        'listings.Listing',
        on_delete=models.CASCADE,
        related_name='favorited_by',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'listing'],
                name='unique_user_listing_favorite',
            ),
        ]
        ordering = ['-created_at']
        indexes = [
            # "Combien de favoris pour cette annonce ?" + tri chrono
            models.Index(fields=['listing', '-created_at'], name='idx_fav_listing_date'),
        ]

    def __str__(self) -> str:
        return f"Fav<{self.user.phone} → {self.listing.title}>"


class SavedSearch(models.Model):
    """Recherche sauvegardée par un client (filtres en JSON)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='saved_searches',
        limit_choices_to={'role': 'CLIENT'},
    )
    label = models.CharField('Libellé', max_length=255)
    filters = models.JSONField(
        'Filtres', default=dict,
        help_text='Ex: {"city": "Abidjan", "listing_type": "LOCATION", "budget_max": 150000}',
    )
    notify = models.BooleanField(
        'Notifications', default=False,
        help_text='Recevoir une alerte quand une nouvelle annonce correspond.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"SavedSearch<{self.user.phone}: {self.label}>"
