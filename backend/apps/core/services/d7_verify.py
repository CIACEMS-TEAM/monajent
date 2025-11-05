import json
from typing import Optional

import requests
from django.conf import settings


class D7VerifyClient:
    def __init__(self) -> None:
        self.base_url = getattr(settings, 'D7_API_BASE_URL', 'https://api.d7networks.com').rstrip('/')
        self.api_token = settings.D7_API_TOKEN
        self.originator = getattr(settings, 'D7_ORIGINATOR', 'SignOTP')

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
        resp = requests.post(url, headers=self._headers(), data=json.dumps(body), timeout=20)
        if not resp.ok:
            print('[D7_SEND_ERROR]', resp.status_code, resp.text)  # noqa: T201
            resp.raise_for_status()
        data = resp.json()
        print('[D7_SEND_OK]', data)  # noqa: T201
        return data

    def resend_otp(self, otp_id: str) -> dict:
        url = f"{self.base_url}/verify/v1/otp/resend-otp"
        body = {'otp_id': otp_id}
        resp = requests.post(url, headers=self._headers(), data=json.dumps(body), timeout=20)
        if not resp.ok:
            print('[D7_RESEND_ERROR]', resp.status_code, resp.text)  # noqa: T201
            resp.raise_for_status()
        data = resp.json()
        print('[D7_RESEND_OK]', data)  # noqa: T201
        return data

    def verify_otp(self, otp_id: str, otp_code: str) -> dict:
        url = f"{self.base_url}/verify/v1/otp/verify-otp"
        body = {'otp_id': otp_id, 'otp_code': otp_code}
        resp = requests.post(url, headers=self._headers(), data=json.dumps(body), timeout=20)
        if not resp.ok:
            print('[D7_VERIFY_ERROR]', resp.status_code, resp.text)  # noqa: T201
            resp.raise_for_status()
        data = resp.json()
        print('[D7_VERIFY_OK]', data)  # noqa: T201
        return data

    def get_status(self, otp_id: str) -> dict:
        url = f"{self.base_url}/verify/v1/report/{otp_id}"
        resp = requests.get(url, headers=self._headers(), timeout=20)
        if not resp.ok:
            print('[D7_STATUS_ERROR]', resp.status_code, resp.text)  # noqa: T201
            resp.raise_for_status()
        data = resp.json()
        print('[D7_STATUS_OK]', data)  # noqa: T201
        return data


