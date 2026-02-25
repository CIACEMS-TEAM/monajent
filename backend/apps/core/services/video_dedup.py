"""
Service anti-fraude vidéo — Monajent
────────────────────────────────────
Calcule le SHA-256 d'un fichier vidéo uploadé et vérifie qu'aucune
vidéo identique n'est ACTUELLEMENT EN LIGNE pour le même agent.

Règles :
  • Deux agents différents PEUVENT avoir la même vidéo (même bien en mandat)
  • Un même agent NE PEUT PAS avoir la même vidéo en ligne sur 2 annonces
  • Si l'annonce précédente est EXPIRED / SUSPENDED / INACTIF, l'agent
    peut ré-uploader la vidéo (le bien est redevenu disponible)
"""

import hashlib

from django.core.files.uploadedfile import UploadedFile

from apps.listings.models import Listing, Video


class DuplicateVideoError(Exception):
    """Vidéo identique déjà en ligne chez cet agent."""
    def __init__(self, existing_video: Video):
        self.existing_video = existing_video
        super().__init__(
            f"Vidéo identique déjà en ligne sur l'annonce "
            f"« {existing_video.listing.title} » (ID #{existing_video.listing_id})."
        )


def compute_file_hash(file: UploadedFile) -> str:
    """
    Calcule le SHA-256 d'un fichier uploadé.
    Lit par blocs de 8 Ko pour ne pas saturer la mémoire.
    Rembobine le fichier après lecture.
    """
    sha256 = hashlib.sha256()
    file.seek(0)
    for chunk in file.chunks(chunk_size=8192):
        sha256.update(chunk)
    file.seek(0)
    return sha256.hexdigest()


def check_video_duplicate(agent_user, file_hash: str) -> Video | None:
    """
    Vérifie si l'agent possède déjà une vidéo avec le même hash
    sur une annonce ACTUELLEMENT ACTIVE.

    Ne bloque PAS si la vidéo existante est sur une annonce
    EXPIRED, SUSPENDED ou INACTIF (le bien peut être remis en ligne).

    Returns:
        La Video existante si doublon EN LIGNE trouvé, None sinon.
    """
    return (
        Video.objects
        .filter(
            listing__agent=agent_user,
            listing__status=Listing.Status.ACTIF,
            file_hash=file_hash,
        )
        .select_related('listing')
        .first()
    )


def validate_and_hash_video(agent_user, file: UploadedFile) -> str:
    """
    Calcule le hash et vérifie l'unicité parmi les annonces en ligne.

    Returns:
        Le hash SHA-256 du fichier.

    Raises:
        DuplicateVideoError si une vidéo identique est déjà EN LIGNE.
    """
    file_hash = compute_file_hash(file)
    existing = check_video_duplicate(agent_user, file_hash)
    if existing:
        raise DuplicateVideoError(existing)
    return file_hash
