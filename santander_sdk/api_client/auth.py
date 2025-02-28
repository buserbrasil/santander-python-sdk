from datetime import datetime, timedelta

from requests import HTTPError, JSONDecodeError
from requests.auth import AuthBase

from santander_sdk.api_client.base import BaseURLSession
from santander_sdk.api_client.client_configuration import SantanderClientConfiguration
from santander_sdk.api_client.exceptions import SantanderRequestError


class SantanderAuth(AuthBase):
    TOKEN_ENDPOINT = "/auth/oauth/v2/token"
    TIMEOUT_SECS = 60
    BEFORE_EXPIRE_TOKEN = timedelta(seconds=60)

    def __init__(self, base_url, client_id, client_secret, cert_path):
        self.base_url = base_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.cert_path = cert_path

        self._token = None
        self.expires_at = None

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
        self._token, self.expires_at = values

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
            timeout=self.TIMEOUT_SECS,
        )
        try:
            response.raise_for_status()
        except HTTPError as e:
            try:
                error_data = response.json()
            except JSONDecodeError:
                error_data = {}

            raise SantanderRequestError(
                error_data.get("error_description", str(e)),
                status_code=e.response.status_code,
                content=error_data,
            ) from e

        data = response.json()
        self.token = (
            data["access_token"],
            datetime.now() + timedelta(seconds=data["expires_in"]),
        )

    @property
    def is_expired(self):
        if not self.expires_at:
            return True

        return datetime.now() > self.expires_at - self.BEFORE_EXPIRE_TOKEN
