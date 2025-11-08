import json
import logging
from typing import Optional

import requests
from django.conf import settings


logger = logging.getLogger(__name__)


class D7VerifyError(Exception):
    """Erreur d'appel au service D7 Verify."""


class D7VerifyClient:
    def __init__(self) -> None:
        self.base_url = getattr(settings, 'D7_API_BASE_URL', 'https://api.d7networks.com').rstrip('/')
        self.api_token = settings.D7_API_TOKEN
        self.originator = getattr(settings, 'D7_ORIGINATOR', 'SignOTP')
        self.timeout = 20

    def _headers(self) -> dict:
        return {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

    def send_otp(self, recipient_e164: str, *, content: Optional[str] = None, template_id: Optional[int] = None,
                 expiry: int = 600, otp_code_length: int = 6, otp_type: str = 'numeric') -> dict:
        url = f"{self.base_url}/verify/v1/otp/send-otp"
        body: dict = {
            'originator': self.originator,
            'recipient': recipient_e164,
            'expiry': expiry,
            'otp_code_length': otp_code_length,
            'otp_type': otp_type,
        }
        if template_id:
            body['template_id'] = template_id
        else:
            body['content'] = content or 'Votre code vérification est: {}'
        try:
            resp = requests.post(url, headers=self._headers(), data=json.dumps(body), timeout=self.timeout)
            if not resp.ok:
                logger.error('D7 send_otp failed: status=%s', resp.status_code)
                try:
                    payload = resp.json()
                except Exception:
                    payload = {}
                raise D7VerifyError(f"D7 send_otp error: {resp.status_code}")  # ne pas logguer PII
            data = resp.json()
            logger.debug('D7 send_otp ok')
            return data
        except requests.RequestException as exc:
            logger.exception('D7 send_otp request exception')
            raise D7VerifyError('D7 send_otp exception') from exc

    def resend_otp(self, otp_id: str) -> dict:
        url = f"{self.base_url}/verify/v1/otp/resend-otp"
        body = {'otp_id': otp_id}
        try:
            resp = requests.post(url, headers=self._headers(), data=json.dumps(body), timeout=self.timeout)
            if not resp.ok:
                logger.error('D7 resend_otp failed: status=%s', resp.status_code)
                raise D7VerifyError(f"D7 resend_otp error: {resp.status_code}")
            data = resp.json()
            logger.debug('D7 resend_otp ok')
            return data
        except requests.RequestException as exc:
            logger.exception('D7 resend_otp request exception')
            raise D7VerifyError('D7 resend_otp exception') from exc

    def verify_otp(self, otp_id: str, otp_code: str) -> dict:
        url = f"{self.base_url}/verify/v1/otp/verify-otp"
        body = {'otp_id': otp_id, 'otp_code': otp_code}
        try:
            resp = requests.post(url, headers=self._headers(), data=json.dumps(body), timeout=self.timeout)
            if not resp.ok:
                logger.error('D7 verify_otp failed: status=%s', resp.status_code)
                raise D7VerifyError(f"D7 verify_otp error: {resp.status_code}")
            data = resp.json()
            logger.debug('D7 verify_otp ok')
            return data
        except requests.RequestException as exc:
            logger.exception('D7 verify_otp request exception')
            raise D7VerifyError('D7 verify_otp exception') from exc

    def get_status(self, otp_id: str) -> dict:
        url = f"{self.base_url}/verify/v1/report/{otp_id}"
        try:
            resp = requests.get(url, headers=self._headers(), timeout=self.timeout)
            if not resp.ok:
                logger.error('D7 get_status failed: status=%s', resp.status_code)
                raise D7VerifyError(f"D7 get_status error: {resp.status_code}")
            data = resp.json()
            logger.debug('D7 get_status ok')
            return data
        except requests.RequestException as exc:
            logger.exception('D7 get_status request exception')
            raise D7VerifyError('D7 get_status exception') from exc


