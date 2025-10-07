import abc
from datetime import datetime, timedelta

from requests import HTTPError, JSONDecodeError
from requests.auth import AuthBase

from santander_sdk.api_client.base import BaseURLSession
from santander_sdk.api_client.client_configuration import SantanderClientConfiguration
from santander_sdk.api_client.exceptions import SantanderRequestError


class TokenStore(abc.ABC):
    @abc.abstractmethod
    def get(self) -> str | None: ...

    @abc.abstractmethod
    def set(self, token: str, expires_in: timedelta) -> None: ...


class InMemoryTokenStore(TokenStore):
    def __init__(self, offset=timedelta(seconds=60)):
        self._token = None
        self._expires_at = None
        self._offset = offset

    def get(self):
        if self._is_expired():
            return None

        return self._token

    def _is_expired(self):
        if self._expires_at is None:
            return True

        return self._expires_at - self._offset < datetime.now()

    def set(self, token: str, expires_in: timedelta):
        self._token = token
        self._expires_at = datetime.now() + expires_in


class SantanderAuth(AuthBase):
    TOKEN_ENDPOINT = "/auth/oauth/v2/token"
    TIMEOUT_SECS = 60
    BEFORE_EXPIRE_TOKEN = timedelta(seconds=60)

    def __init__(
        self,
        base_url,
        client_id,
        client_secret,
        cert_path,
        token_store=InMemoryTokenStore(),
    ):
        self.base_url = base_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.cert_path = cert_path
        self.token_store = token_store

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
        token = self.token_store.get()
        if not token:
            token, expires_in = self.renew()
            self.token_store.set(token, expires_in)

        return token

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
        return data["access_token"], timedelta(seconds=data["expires_in"])
