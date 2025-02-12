from requests import Request

from santander_sdk.api_client.base import BaseURLSession


def test_base_url_session_prepare_request():
    session = BaseURLSession("https://api.santander.com.br")

    req = Request("GET", "/orders")
    req = session.prepare_request(req)

    assert req.url == "https://api.santander.com.br/orders"
