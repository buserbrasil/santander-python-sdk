from datetime import datetime, timedelta
import unittest
from unittest.mock import patch
from urllib.parse import urljoin

from santander_sdk.api_client.client import TOKEN_ENDPOINT, SantanderApiClient
from santander_sdk.api_client.client_configuration import (
    SantanderClientConfiguration,
)
from santander_sdk.api_client.exceptions import SantanderClientException
from decimal import Decimal as D
from mock.santander_mocker import (
    SANTANDER_URL,
    get_dict_token_response,
    get_dict_token_request,
    get_dict_payment_pix_request,
    get_dict_payment_pix_response,
)
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
        self.token_request_mock = get_dict_token_request()
        self.token_response_mock = get_dict_token_response()
        self.client = SantanderApiClient(self.config)

    def test_is_authenticated(self):
        self.client.token = "test_token"
        now = datetime.now()
        self.client.token_expires_at = now + timedelta(seconds=900)
        assert self.client.is_authenticated is True, "Deveria estar autenticado"

        # Token expirado (considerado expirado se restarem menos de BEFORE_EXPIRE_TOKEN_SECONDS, que são 60 segundos)
        self.client.token_expires_at = now + timedelta(seconds=50)
        assert self.client.is_authenticated is False, "Deveria ter expirado"

        # Token não existe
        self.client.token = None
        assert self.client.is_authenticated is False, (
            "Não tem token, deveria retornar False"
        )

    @patch("santander_sdk.api_client.client.datetime")
    @patch.object(
        SantanderApiClient, "_request_token", return_value=get_dict_token_response()
    )
    def test_authenticate(self, mock_request_token, mock_datetime):
        expire_in = mock_request_token.return_value.get("expires_in")
        access_token = mock_request_token.return_value.get("access_token")
        self.config.cert = "test_configure_session_cert_path"
        mock_datetime.now.return_value = datetime.fromtimestamp(1000)

        self.client._authenticate()

        mock_request_token.assert_called_once()
        assert self.client.token == access_token, "Token incorreto"
        expected_expires_at = datetime.fromtimestamp(1000) + timedelta(
            seconds=expire_in
        )
        assert self.client.token_expires_at == expected_expires_at, "Expiração não bate"
        assert (
            self.client.session.headers["Authorization"] == f"Bearer {access_token}"
        ), "O token deve bater"
        assert self.client.session.headers["X-Application-Key"] == "test_client_id", (
            "O client_id deve bater"
        )
        assert self.client.session.verify is True, (
            "Deve estar configurado para verificar certificado"
        )
        assert self.client.session.cert == "test_configure_session_cert_path", (
            "O path deve bater"
        )

    @patch.object(SantanderApiClient, "_authenticate")
    def test_ensure_requirements_happy_path(self, mock_authenticate):
        self.client.token = "test_token"
        self.client.token_expires_at = datetime.now() + timedelta(seconds=100)
        self.client._ensure_requirements()
        mock_authenticate.assert_not_called()

    @patch("santander_sdk.api_client.client.requests.Session.post")
    def test_request_token(self, mock_post):
        mock_post.return_value.json.return_value = self.token_response_mock
        self.client.config.cert = "test_request_token_cert_path.pem"

        token_data = self.client._request_token()
        mock_post.assert_called_once_with(
            TOKEN_ENDPOINT,
            data=self.token_request_mock,
            verify=True,
            timeout=60,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            cert="test_request_token_cert_path.pem",
        )
        self.assertEqual(
            token_data.get("access_token"), self.token_response_mock.get("access_token")
        )
        self.assertEqual(
            token_data.get("expires_in"), self.token_response_mock.get("expires_in")
        )

    @patch("santander_sdk.api_client.client.requests.Session.request")
    @patch.object(SantanderApiClient, "_ensure_requirements")
    def test_request(self, mock_ensure_requirements, mock_request):
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
        response_data = self.client._request("POST", "/test_endpoint", data=request_dict)
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
        assert (
            self.client._prepare_url("test_endpoint/qr")
            == "test_endpoint/qr"
        )
        assert (
            self.client._prepare_url("test/:WORKSPACEID")
            == "test/d6c7b8a9e"
        )
        assert (
            self.client._prepare_url(":workspaceid/pix")
            == "d6c7b8a9e/pix"
        )
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
