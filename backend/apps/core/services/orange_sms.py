import base64
import json
from typing import Optional
from urllib.parse import quote

import requests
from django.conf import settings
from django.core.cache import cache


class OrangeSmsClient:
    """Client minimal pour Orange SMS A2P (Côte d'Ivoire).

    - OAuth2 client_credentials → access token mis en cache
    - Envoi SMS via /smsmessaging/v1/outbound/{senderAddress}/requests
    """

    def __init__(self) -> None:
        self.base_url = settings.ORANGE_API_BASE_URL.rstrip('/')
        self.client_id = settings.ORANGE_CLIENT_ID
        self.client_secret = settings.ORANGE_CLIENT_SECRET
        self.sender_address = self._clean_sender(settings.ORANGE_SENDER_ADDRESS)  # ex: 'tel:+2250700000000'
        self.sender_name = getattr(settings, 'ORANGE_SENDER_NAME', '')
        self.default_cc = getattr(settings, 'ORANGE_DEFAULT_COUNTRY_CODE', '+225')

    def _get_access_token(self) -> str:
        cache_key = 'orange_sms_access_token'
        token = cache.get(cache_key)
        if token:
            return token

        token_url = f"{self.base_url}/oauth/v3/token"
        basic = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        headers = {
            'Authorization': f'Basic {basic}',
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        data = {'grant_type': 'client_credentials'}
        resp = requests.post(token_url, headers=headers, data=data, timeout=15)
        if not resp.ok:
            print('[ORANGE_TOKEN_ERROR]', resp.status_code, resp.text)  # noqa: T201
            resp.raise_for_status()
        payload = resp.json()
        access_token = payload['access_token']
        expires_in = int(payload.get('expires_in', 3600))
        cache.set(cache_key, access_token, timeout=max(expires_in - 60, 300))
        return access_token

    def _normalize_msisdn(self, phone: str) -> str:
        phone = phone.strip()
        if phone.startswith('+'):
            return f"tel:{phone}"
        if phone.startswith('tel:+'):
            return phone
        # défaut pays
        digits = ''.join(ch for ch in phone if ch.isdigit())
        return f"tel:{self.default_cc}{digits}"

    def _clean_sender(self, value: str) -> str:
        """Nettoie le senderAddress provenant du .env.

        - supprime guillemets, espaces et commentaires inline après '#'
        - ajoute 'tel:' si manquant
        - valide le préfixe '+'.
        """
        s = str(value or '').strip().strip('"').strip("'")
        if '#' in s:
            s = s.split('#', 1)[0].strip()
        s = s.replace(' ', '')
        if s.startswith('tel:+'):
            return s
        if s.startswith('+'):
            return f'tel:{s}'
        # Si l'utilisateur a mis juste les chiffres, préfixer avec code pays
        digits = ''.join(ch for ch in s if ch.isdigit() or ch == '+')
        if digits.startswith('+'):
            return f'tel:{digits}'
        # fallback: utilise default_cc
        return f'tel:{self.default_cc}{digits}'

    def send_sms(self, to_phone: str, message: str) -> dict:
        token = self._get_access_token()
        address = self._normalize_msisdn(to_phone)
        sender_address = self.sender_address
        url = f"{self.base_url}/smsmessaging/v1/outbound/{quote(sender_address, safe=':+')}/requests"
        body = {
            'outboundSMSMessageRequest': {
                'address': address,
                'senderAddress': sender_address,
                'outboundSMSTextMessage': {'message': message[:160]},
            }
        }
        if self.sender_name:
            body['outboundSMSMessageRequest']['senderName'] = self.sender_name

        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        resp = requests.post(url, headers=headers, data=json.dumps(body), timeout=15)
        if not resp.ok:
            # Log complet pour diagnostic (statut + corps)
            print('[ORANGE_SMS_ERROR]', resp.status_code, resp.text)  # noqa: T201
            resp.raise_for_status()
        try:
            data = resp.json()
            print('[ORANGE_SMS_OK]', resp.status_code, data)  # noqa: T201
            return data
        except Exception:
            return {'raw': resp.text}

    # ---- Admin/diagnostic ----
    def _auth_headers_json(self) -> dict:
        return {
            'Authorization': f'Bearer {self._get_access_token()}',
            'Accept': 'application/json',
        }

    def get_contracts(self, country: Optional[str] = None, language: str = 'EN') -> dict:
        url = f"{self.base_url}/sms/admin/v1/contracts"
        params = {}
        if country:
            params['country'] = country
        if language:
            params['language'] = language
        resp = requests.get(url, headers=self._auth_headers_json(), params=params, timeout=15)
        print('[ORANGE_CONTRACTS]', resp.status_code, resp.text)  # noqa: T201
        resp.raise_for_status()
        return resp.json()

    def get_purchase_orders(self, country: Optional[str] = None) -> dict:
        url = f"{self.base_url}/sms/admin/v1/purchaseorders"
        params = {}
        if country:
            params['country'] = country
        resp = requests.get(url, headers=self._auth_headers_json(), params=params, timeout=15)
        print('[ORANGE_PURCHASES]', resp.status_code, resp.text)  # noqa: T201
        resp.raise_for_status()
        return resp.json()

    def get_statistics(self, country: Optional[str] = None) -> dict:
        url = f"{self.base_url}/sms/admin/v1/statistics"
        params = {}
        if country:
            params['country'] = country
        resp = requests.get(url, headers=self._auth_headers_json(), params=params, timeout=15)
        print('[ORANGE_STATS]', resp.status_code, resp.text)  # noqa: T201
        resp.raise_for_status()
        return resp.json()

    def subscribe_dlr(self, notify_url: str) -> dict:
        """Souscrit aux notifications de Delivery Receipt (DR)."""
        sender_address = self.sender_address
        url = f"{self.base_url}/smsmessaging/v1/outbound/{quote(sender_address, safe=':+')}/subscriptions"
        body = {
            'deliveryReceiptSubscription': {
                'callbackReference': {
                    'notifyURL': notify_url,
                }
            }
        }
        headers = {
            'Authorization': f'Bearer {self._get_access_token()}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        resp = requests.post(url, headers=headers, data=json.dumps(body), timeout=15)
        print('[ORANGE_SUBSCRIBE_DLR]', resp.status_code, resp.text)  # noqa: T201
        resp.raise_for_status()
        return resp.json()

    def send_otp(self, to_phone: str, code: str) -> dict:
        message = f"Votre code Monajent est {code}. Il expire dans 10 minutes. Ne le partagez pas."
        return self.send_sms(to_phone, message)


