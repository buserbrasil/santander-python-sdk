import unittest
from unittest.mock import patch, MagicMock
from santander_client.api_client import (
    get_client,
    SantanderWorkspaceException,
    set_configuration,
)
from santander_client.api_client.client_configuration import (
    SantanderClientConfiguration,
)


class UnitTestGetClient(unittest.TestCase):
    @patch(
        "santander_client.api_client.get_first_workspace_id_of_type", return_value=None
    )
    @patch("santander_client.api_client.SantanderApiClient")
    def test_get_client(self, mock_santander_client, mock_get_first_workspace_id):
        mock_client_instance = MagicMock()
        mock_santander_client.return_value = mock_client_instance
        with self.assertRaises(SantanderWorkspaceException):
            set_configuration(
                SantanderClientConfiguration(
                    client_id="client_id",
                    client_secret="client_pk",
                    cert="certificate_path",
                    base_url="api_url",
                )
            )
            get_client()

        mock_get_first_workspace_id.assert_called_once_with(
            mock_client_instance, "PAYMENTS"
        )
