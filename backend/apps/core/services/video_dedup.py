"""
Service anti-fraude vidéo — Monajent
────────────────────────────────────
Double couche de détection de vidéos dupliquées :

  1. SHA-256 (exact)   — bloque les fichiers bit-à-bit identiques.
                         Très rapide, pré-vérifiable côté client.
  2. VideoHash (percep.)— bloque les copies recompressées, recadrées
                         ou filtrées. Basé sur la similarité visuelle
                         (distance de Hamming sur un hash 64-bit).

Règles :
  • Deux agents différents PEUVENT avoir la même vidéo (mandat partagé)
  • Un même agent NE PEUT PAS réutiliser la même vidéo sur deux annonces
    différentes, quel que soit le statut
"""

from __future__ import annotations

import hashlib
import logging
import os
import tempfile

from PIL import Image
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS

from django.core.files.uploadedfile import UploadedFile

from apps.listings.models import Video

logger = logging.getLogger(__name__)

PERCEPTUAL_HAMMING_THRESHOLD = 10


# ═══════════════════════════════════════════════════════════════
# Exceptions
# ═══════════════════════════════════════════════════════════════


class DuplicateVideoError(Exception):
    """Vidéo identique (exacte ou visuellement similaire) déjà chez cet agent."""

    def __init__(self, existing_video: Video, method: str = 'exact'):
        self.existing_video = existing_video
        self.method = method
        label = 'identique' if method == 'exact' else 'visuellement similaire'
        super().__init__(
            f"Vidéo {label} déjà utilisée sur l'annonce "
            f"« {existing_video.listing.title} » (ID #{existing_video.listing_id})."
        )


# ═══════════════════════════════════════════════════════════════
# Couche 1 — SHA-256 (doublons exacts)
# ═══════════════════════════════════════════════════════════════


def compute_file_hash(file: UploadedFile) -> str:
    """SHA-256 par blocs de 8 Ko. Rembobine après lecture."""
    sha256 = hashlib.sha256()
    file.seek(0)
    for chunk in file.chunks(chunk_size=8192):
        sha256.update(chunk)
    file.seek(0)
    return sha256.hexdigest()


def check_exact_duplicate(
    agent_user,
    file_hash: str,
    exclude_listing_id: int | None = None,
) -> Video | None:
    qs = (
        Video.objects
        .filter(listing__agent=agent_user, file_hash=file_hash)
        .select_related('listing')
    )
    if exclude_listing_id:
        qs = qs.exclude(listing_id=exclude_listing_id)
    return qs.first()


def check_hash_exists(agent_user, file_hash: str) -> Video | None:
    """Vérification rapide par SHA-256 seul (utilisé par l'endpoint pré-check)."""
    return (
        Video.objects
        .filter(listing__agent=agent_user, file_hash=file_hash)
        .select_related('listing')
        .first()
    )


# ═══════════════════════════════════════════════════════════════
# Couche 2 — Hash perceptuel (copies modifiées)
# ═══════════════════════════════════════════════════════════════


def _hamming_distance(h1: str, h2: str) -> int:
    """Distance de Hamming entre deux hash hex de même longueur."""
    n1, n2 = int(h1, 16), int(h2, 16)
    xor = n1 ^ n2
    return bin(xor).count('1')


def compute_perceptual_hash(file: UploadedFile) -> str:
    """
    Calcule le hash perceptuel via VideoHash.
    Écrit le fichier dans un temp car VideoHash a besoin d'un chemin.
    Retourne le hash hex (16 chars = 64 bits) ou '' si échec.
    """
    try:
        from videohash import VideoHash
    except ImportError:
        logger.warning("videohash non installé — hash perceptuel ignoré")
        return ''

    suffix = os.path.splitext(file.name)[1] or '.mp4'
    tmp = None
    try:
        file.seek(0)
        tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        for chunk in file.chunks(chunk_size=65536):
            tmp.write(chunk)
        tmp.close()
        file.seek(0)

        vh = VideoHash(path=tmp.name)
        return vh.hash_hex.removeprefix('0x')
    except Exception as exc:
        logger.warning("Erreur calcul hash perceptuel : %s", exc)
        return ''
    finally:
        if tmp and os.path.exists(tmp.name):
            os.unlink(tmp.name)


def check_perceptual_duplicate(
    agent_user,
    phash: str,
    exclude_listing_id: int | None = None,
    threshold: int = PERCEPTUAL_HAMMING_THRESHOLD,
) -> Video | None:
    """
    Compare le hash perceptuel avec ceux des vidéos existantes de l'agent.
    Retourne la première vidéo visuellement similaire ou None.
    """
    if not phash:
        return None

    qs = (
        Video.objects
        .filter(listing__agent=agent_user)
        .exclude(perceptual_hash='')
        .values_list('id', 'perceptual_hash', 'listing_id', named=True)
    )
    if exclude_listing_id:
        qs = qs.exclude(listing_id=exclude_listing_id)

    for row in qs:
        try:
            dist = _hamming_distance(phash, row.perceptual_hash)
        except (ValueError, TypeError):
            continue
        if dist <= threshold:
            return (
                Video.objects
                .select_related('listing')
                .get(pk=row.id)
            )
    return None


# ═══════════════════════════════════════════════════════════════
# Point d'entrée principal
# ═══════════════════════════════════════════════════════════════


def validate_and_hash_video(
    agent_user,
    file: UploadedFile,
    exclude_listing_id: int | None = None,
) -> tuple[str, str]:
    """
    Pipeline anti-fraude complet :
      1. SHA-256 → rejet immédiat si doublon exact
      2. Hash perceptuel → rejet si copie visuellement similaire

    Returns:
        (file_hash, perceptual_hash)

    Raises:
        DuplicateVideoError
    """
    file_hash = compute_file_hash(file)
    existing = check_exact_duplicate(agent_user, file_hash, exclude_listing_id)
    if existing:
        raise DuplicateVideoError(existing, method='exact')

    phash = compute_perceptual_hash(file)
    if phash:
        similar = check_perceptual_duplicate(
            agent_user, phash, exclude_listing_id,
        )
        if similar:
            raise DuplicateVideoError(similar, method='perceptual')

    return file_hash, phash
