from datetime import datetime, timedelta
from requests.auth import AuthBase

from santander_sdk.api_client.base import BaseURLSession
from santander_sdk.api_client.client_configuration import SantanderClientConfiguration


class SantanderAuth(AuthBase):
    TOKEN_ENDPOINT = "/auth/oauth/v2/token"

    def __init__(self, base_url, client_id, client_secret, cert_path):
        self.base_url = base_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.cert_path = cert_path

        self._token = None
        self._token_expires_at = None

    @classmethod
    def from_config(cls, config: SantanderClientConfiguration):
        return cls(
            base_url=config.base_url,
            client_id=config.client_id,
            client_secret=config.client_secret,
            cert_path=config.cert,
        )

    def __call__(self, r):
        r.headers["Authorization"] = f"Bearer {self.token}"
        r.headers["X-Application-Key"] = self.client_id
        return r

    @property
    def token(self):
        if self.is_expired:
            self.renew()

        return self._token

    @token.setter
    def token(self, values):
        self._token, self._token_expires_at = values

    def renew(self):
        session = BaseURLSession(base_url=self.base_url)
        session.cert = self.cert_path

        response = session.post(
            self.TOKEN_ENDPOINT,
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=60,
        )
        response.raise_for_status()

        token_data = response.json()
        self.token = (
            token_data["access_token"],
            datetime.now() + timedelta(seconds=token_data["expires_in"]),
        )

    @property
    def is_expired(self):
        if self._token_expires_at is None:
            return True

        return datetime.now() > self._token_expires_at
