import hashlib
from typing import Optional, Dict, Any

from django.http import HttpRequest

from .models import AuthEventLog


def _hash_phone(phone_e164: Optional[str]) -> str:
    if not phone_e164:
        return ''
    return hashlib.sha256(phone_e164.encode('utf-8')).hexdigest()


def _client_ip(request: HttpRequest) -> Optional[str]:
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        # X-Forwarded-For: client, proxy1, proxy2
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def write_auth_event(
    event: str,
    request: HttpRequest,
    *,
    user=None,
    phone_e164: Optional[str] = None,
    success: bool = True,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    try:
        AuthEventLog.objects.create(
            event=event,
            user=user,
            phone_hash=_hash_phone(phone_e164),
            ip_address=_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:512],
            success=success,
            metadata=(metadata or {}),
        )
    except Exception:
        # ne jamais faire échouer la requête pour l'audit
        pass


