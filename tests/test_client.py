import unittest
from decimal import Decimal as D
from unittest.mock import patch

from mock.santander_mocker import (
    SANTANDER_URL,
    get_dict_payment_pix_request,
    get_dict_payment_pix_response,
    get_dict_token_response,
)

from santander_sdk.api_client.client import SantanderApiClient
from santander_sdk.api_client.client_configuration import (
    SantanderClientConfiguration,
)
from santander_sdk.api_client.exceptions import SantanderClientException
from santander_sdk.types import OrderStatus


class UnitTestSantanderApiClient(unittest.TestCase):
    def setUp(self):
        self.config = SantanderClientConfiguration(
            client_id="test_client_id",
            client_secret="test_client_secret",
            cert="test_cert",
            workspace_id="test_workspace_id",
            base_url=SANTANDER_URL,
        )
        self.token_response_mock = get_dict_token_response()
        self.client = SantanderApiClient(self.config)

    @patch("santander_sdk.api_client.client.requests.Session.request")
    def test_request(self, mock_request):
        response_dict = get_dict_payment_pix_response(
            "12345678", D(299.99), OrderStatus.READY_TO_PAY, "12345678909", "CPF"
        )
        request_dict = get_dict_payment_pix_request(
            "12345678", D(299.99), "12345678909", "CPF"
        )
        mock_request.return_value.json.return_value = response_dict

        # GET (Não precisa de data)
        response_data = self.client._request("GET", "/test_endpoint")
        assert response_data == response_dict, (
            "Deveria ter retornado o dict de resposta"
        )
        mock_request.assert_called_once_with(
            "GET", "/test_endpoint", json=None, params=None, timeout=60
        )

        # Post (Precisa de data)
        mock_request.reset_mock()
        response_data = self.client._request(
            "POST", "/test_endpoint", data=request_dict
        )
        assert response_data == response_dict, (
            "Deveria ter retornado o dict de resposta"
        )
        mock_request.assert_called_once_with(
            "POST",
            "/test_endpoint",
            json=request_dict,
            params=None,
            timeout=60,
        )

    def test_prepare_url(self):
        self.client.config.workspace_id = "d6c7b8a9e"
        assert self.client._prepare_url("test_endpoint/qr") == "test_endpoint/qr"
        assert self.client._prepare_url("test/:WORKSPACEID") == "test/d6c7b8a9e"
        assert self.client._prepare_url(":workspaceid/pix") == "d6c7b8a9e/pix"
        self.client.config.workspace_id = ""
        with self.assertRaises(SantanderClientException):
            self.client._prepare_url("test_endpoint/:workspaceid")
        self.client.config.workspace_id = "d6c7b8a9e"

    @patch("santander_sdk.api_client.client.SantanderApiClient._request")
    def test_get_method(self, mock_request):
        self.client.get("test_endpoint")
        mock_request.assert_called_once_with("GET", "test_endpoint", params=None)

    @patch("santander_sdk.api_client.client.SantanderApiClient._request")
    def test_post_method(self, mock_request):
        self.client.post("test_endpoint", data={"post_data_key": "post_data_value"})
        mock_request.assert_called_once_with(
            "POST", "test_endpoint", data={"post_data_key": "post_data_value"}
        )

    @patch("santander_sdk.api_client.client.SantanderApiClient._request")
    def test_put_method(self, mock_request):
        self.client.put("test_endpoint", data={"put_data_key": "put_data_value"})
        mock_request.assert_called_once_with(
            "PUT", "test_endpoint", data={"put_data_key": "put_data_value"}
        )

    @patch("santander_sdk.api_client.client.SantanderApiClient._request")
    def test_delete_method(self, mock_request):
        self.client.delete("test_endpoint")
        mock_request.assert_called_once_with("DELETE", "test_endpoint")

    @patch("santander_sdk.api_client.client.SantanderApiClient._request")
    def test_patch_method(self, mock_request):
        self.client.patch("test_endpoint", data={"patch_data_key": "patch_data_value"})
        mock_request.assert_called_once_with(
            "PATCH", "test_endpoint", data={"patch_data_key": "patch_data_value"}
        )
