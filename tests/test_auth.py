from re import compile as regex
from datetime import datetime

import pytest
from freezegun import freeze_time
from requests import PreparedRequest

from santander_sdk.api_client.auth import SantanderAuth


@pytest.fixture
def auth():
    return SantanderAuth(
        "https://api.santander.com.br",
        client_id="123",
        client_secret="secert",
        cert_path="/var/certs/cert.pem",
    )


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
