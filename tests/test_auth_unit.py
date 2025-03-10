from re import compile as regex
from datetime import datetime

import pytest
from freezegun import freeze_time
from requests import PreparedRequest

from santander_sdk.api_client.auth import SantanderAuth
from santander_sdk.api_client.client_configuration import SantanderClientConfiguration
from santander_sdk.api_client.exceptions import SantanderRequestError


@pytest.fixture
def auth():
    return SantanderAuth(
        "https://api.santander.com.br",
        client_id="123",
        client_secret="secret",
        cert_path="/var/certs/cert.pem",
    )


def test_from_config():
    config = SantanderClientConfiguration(
        client_id="buser",
        client_secret="secret",
        cert="/var/cets/cert.pem",
        base_url="https://api.santander.com.br",
        workspace_id="1",
    )

    auth = SantanderAuth.from_config(config)

    assert auth.base_url == "https://api.santander.com.br"
    assert auth.cert_path == "/var/cets/cert.pem"
    assert auth.client_id == "buser"
    assert auth.client_secret == "secret"


def test_renew_when_token_empty(auth, responses):
    responses.add(
        responses.POST,
        regex(".+/auth/oauth/v2/token"),
        json={"access_token": "VALID_TOKEN", "expires_in": 120},
    )

    req = PreparedRequest()
    req.prepare("GET", "https://api.santander.com.br/orders", auth=auth)

    assert req.headers["Authorization"] == "Bearer VALID_TOKEN"
    assert req.headers["X-Application-Key"] == auth.client_id


@freeze_time("2025-02-13 10:05")
def test_renew_token_when_expired(auth, responses):
    responses.add(
        responses.POST,
        regex(".+/auth/oauth/v2/token"),
        json={"access_token": "NEW_VALID_TOKEN", "expires_in": 120},
    )
    auth.token = "VALID_TOKEN", datetime(2025, 2, 13, 10)

    req = PreparedRequest()
    req.prepare("GET", "https://api.santander.com.br/orders", auth=auth)

    assert req.headers["Authorization"] == "Bearer NEW_VALID_TOKEN"
    assert auth.expires_at == datetime(2025, 2, 13, 10, 7)


@freeze_time("2025-02-13 10:00")
@pytest.mark.parametrize(
    "expires_at,expected",
    [
        (None, True),
        (datetime(2025, 2, 13, 10, 1), False),
        (datetime(2025, 2, 13, 10, 0, 59), True),
    ],
)
def test_is_expired(auth, expires_at, expected):
    auth.expires_at = expires_at
    assert auth.is_expired is expected


def test_invalid_credentials(auth, responses):
    responses.add(
        responses.POST,
        regex(".+/auth/oauth/v2/token"),
        json={
            "error": "unauthorized_client",
            "error_description": "Invalid client credentials",
        },
        status=401,
    )

    with pytest.raises(
        SantanderRequestError, match="Invalid client credentials"
    ) as exc:
        req = PreparedRequest()
        req.prepare("GET", "https://api.santander.com.br/orders", auth=auth)

    assert exc.value.status_code == 401
    assert exc.value.content == {
        "error": "unauthorized_client",
        "error_description": "Invalid client credentials",
    }


def test_server_error(auth, responses):
    responses.add(
        responses.POST,
        regex(".+/auth/oauth/v2/token"),
        status=500,
    )

    with pytest.raises(SantanderRequestError, match="500 Server Error"):
        req = PreparedRequest()
        req.prepare("GET", "https://api.santander.com.br/orders", auth=auth)
