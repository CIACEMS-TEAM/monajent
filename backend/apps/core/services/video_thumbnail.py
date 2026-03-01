"""
Génération automatique de vignettes vidéo — Monajent
─────────────────────────────────────────────────────
Extrait une image à 1 seconde de la vidéo via FFmpeg.
"""

from __future__ import annotations

import logging
import os
import subprocess
import tempfile
import uuid

from django.core.files.base import ContentFile
from django.core.files.uploadedfile import UploadedFile

logger = logging.getLogger(__name__)


def generate_thumbnail(video_file: UploadedFile) -> ContentFile | None:
    """
    Génère un thumbnail JPEG à partir d'un fichier vidéo uploadé.
    Retourne un ContentFile prêt à être assigné à un ImageField, ou None si échec.
    """
    tmp_video = None
    tmp_thumb = None
    try:
        suffix = os.path.splitext(video_file.name or '')[-1] or '.mp4'
        tmp_video = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        video_file.seek(0)
        for chunk in video_file.chunks():
            tmp_video.write(chunk)
        tmp_video.flush()
        tmp_video.close()

        tmp_thumb = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        tmp_thumb.close()

        cmd = [
            'ffmpeg', '-y',
            '-i', tmp_video.name,
            '-ss', '1',
            '-vframes', '1',
            '-vf', 'scale=640:-2',
            '-q:v', '3',
            tmp_thumb.name,
        ]

        result = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            timeout=30,
        )

        if result.returncode != 0:
            logger.warning('FFmpeg thumbnail failed: %s', result.stderr.decode(errors='replace')[:500])
            return None

        with open(tmp_thumb.name, 'rb') as f:
            data = f.read()

        if len(data) < 100:
            return None

        filename = f'thumb_{uuid.uuid4().hex[:12]}.jpg'
        return ContentFile(data, name=filename)

    except FileNotFoundError:
        logger.warning('FFmpeg non trouvé — thumbnail non généré')
        return None
    except subprocess.TimeoutExpired:
        logger.warning('FFmpeg timeout — thumbnail non généré')
        return None
    except Exception as exc:
        logger.warning('Erreur génération thumbnail: %s', exc)
        return None
    finally:
        if tmp_video and os.path.exists(tmp_video.name):
            os.unlink(tmp_video.name)
        if tmp_thumb and os.path.exists(tmp_thumb.name):
            os.unlink(tmp_thumb.name)
        video_file.seek(0)


def get_video_duration(video_file: UploadedFile) -> int | None:
    """
    Retourne la durée en secondes d'un fichier vidéo, ou None si échec.
    """
    tmp_video = None
    try:
        suffix = os.path.splitext(video_file.name or '')[-1] or '.mp4'
        tmp_video = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        video_file.seek(0)
        for chunk in video_file.chunks():
            tmp_video.write(chunk)
        tmp_video.flush()
        tmp_video.close()

        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            tmp_video.name,
        ]

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=15,
        )

        if result.returncode != 0:
            return None

        duration = float(result.stdout.decode().strip())
        return max(1, int(duration))

    except (FileNotFoundError, ValueError, subprocess.TimeoutExpired):
        return None
    finally:
        if tmp_video and os.path.exists(tmp_video.name):
            os.unlink(tmp_video.name)
        video_file.seek(0)
