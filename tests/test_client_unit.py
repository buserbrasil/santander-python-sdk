import re
import pytest
from decimal import Decimal as D
from unittest.mock import patch

import responses

from mock.santander_mocker import (
    SANTANDER_URL,
    get_dict_payment_pix_request,
    get_dict_payment_pix_response,
)

from santander_sdk.api_client.client import SantanderApiClient
from santander_sdk.api_client.client_configuration import (
    SantanderClientConfiguration,
)
from santander_sdk.api_client.exceptions import (
    SantanderClientError,
    SantanderRequestError,
)


@responses.activate
@pytest.fixture
def client():
    config = SantanderClientConfiguration(
        client_id="test_client_id",
        client_secret="test_client_secret",
        cert="test_cert",
        workspace_id="test_workspace_id",
        base_url=SANTANDER_URL,
    )
    responses.add(
        responses.POST,
        re.compile(r".*v2/token$"),
        json={"access_token": "test_access_token", "expires_in": 3600},
        status=200,
    )
    client_instance = SantanderApiClient(config)

    with patch("logging.getLogger") as mock_get_logger:
        mock_logger = mock_get_logger.return_value
        client_instance.logger = mock_logger
        yield client_instance


@patch("santander_sdk.api_client.client.requests.Session.request")
def test_request(mock_request, client):
    response_dict = get_dict_payment_pix_response(
        "12345678", D(299.99), "READY_TO_PAY", "12345678909", "CPF"
    )
    request_dict = get_dict_payment_pix_request(
        "12345678", D(299.99), "12345678909", "CPF"
    )
    mock_request.return_value.json.return_value = response_dict
    response_data = client._request("GET", "/test_endpoint")
    assert response_data == response_dict
    mock_request.assert_called_once_with(
        "GET", "/test_endpoint", json=None, params=None, timeout=60
    )

    mock_request.reset_mock()
    response_data = client._request("POST", "/test_endpoint", data=request_dict)
    assert response_data == response_dict
    mock_request.assert_called_once_with(
        "POST",
        "/test_endpoint",
        json=request_dict,
        params=None,
        timeout=60,
    )


def test_prepare_url(client):
    client.config.workspace_id = "d6c7b8a9e"
    assert client._prepare_url("test_endpoint/qr") == "test_endpoint/qr"
    assert client._prepare_url("test/:WORKSPACEID") == "test/d6c7b8a9e"
    assert client._prepare_url(":workspaceid/pix") == "d6c7b8a9e/pix"
    client.config.workspace_id = ""
    with pytest.raises(SantanderClientError):
        client._prepare_url("test_endpoint/:workspaceid")
    client.config.workspace_id = "d6c7b8a9e"


@patch("santander_sdk.api_client.client.SantanderApiClient._request")
def test_get_method(mock_request, client):
    client.get("test_endpoint")
    mock_request.assert_called_once_with("GET", "test_endpoint", params=None)


@patch("santander_sdk.api_client.client.SantanderApiClient._request")
def test_post_method(mock_request, client):
    client.post("test_endpoint", data={"post_data_key": "post_data_value"})
    mock_request.assert_called_once_with(
        "POST", "test_endpoint", data={"post_data_key": "post_data_value"}
    )


@patch("santander_sdk.api_client.client.SantanderApiClient._request")
def test_put_method(mock_request, client):
    client.put("test_endpoint", data={"put_data_key": "put_data_value"})
    mock_request.assert_called_once_with(
        "PUT", "test_endpoint", data={"put_data_key": "put_data_value"}
    )


@patch("santander_sdk.api_client.client.SantanderApiClient._request")
def test_delete_method(mock_request, client):
    client.delete("test_endpoint")
    mock_request.assert_called_once_with("DELETE", "test_endpoint")


@patch("santander_sdk.api_client.client.SantanderApiClient._request")
def test_patch_method(mock_request, client):
    client.patch("test_endpoint", data={"patch_data_key": "patch_data_value"})
    mock_request.assert_called_once_with(
        "PATCH", "test_endpoint", data={"patch_data_key": "patch_data_value"}
    )


@responses.activate
def test_request_log_success_all(client):
    client.config.log_request_response_level = "ALL"
    responses.add(
        responses.POST,
        re.compile(r".*/test_endpoint$"),
        json={"id": "123456789", "status": "success"},
        status=200,
    )

    with patch.object(client, "logger") as mock_logger:
        result = client._request(
            "POST", "/test_endpoint", data={"pix_key": "123456789", "amount": "100.00"}
        )

    extra = mock_logger.info.call_args[1]["extra"]
    assert result == {"id": "123456789", "status": "success"}
    assert mock_logger.info.call_args[0][0] == "API request successful"
    mock_logger.info.assert_called_once()
    expected_extra = {
        "method": "POST",
        "url": "/test_endpoint",
        "status_code": 200,
        "request_body": {"pix_key": "123456789", "amount": "100.00"},
        "response_body": {"id": "123456789", "status": "success"},
        "status": "success",
    }

    for key, value in expected_extra.items():
        assert extra[key] == value


@responses.activate
def test_request_log_error(client):
    client.config.log_request_response_level = "ERROR"
    request_data = {"pix_key": "123456789", "amount": "100.00"}
    error_response = {"error": "Bad Request"}

    responses.add(
        responses.POST,
        f"{SANTANDER_URL}/test_endpoint",
        json=error_response,
        status=400,
    )

    with patch.object(client, "logger") as mock_logger:
        with pytest.raises(SantanderRequestError):
            client._request("POST", "/test_endpoint", data=request_data)

    mock_logger.error.assert_called_once()
    assert mock_logger.error.call_args[0][0] == "API request failed"

    extra = mock_logger.error.call_args[1]["extra"]
    expected_fields = {
        "method": "POST",
        "url": "/test_endpoint",
        "status_code": 400,
        "request_body": request_data,
        "response_body": error_response,
        "status": "error",
        "error": {
            "message": "400 Client Error: Bad Request for url: https://trust-sandbox.api.santander.com.br/test_endpoint",
            "type": "HTTPError",
        },
    }

    for key, value in expected_fields.items():
        assert extra[key] == value
