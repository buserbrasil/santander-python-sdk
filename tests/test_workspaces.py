import unittest
from unittest.mock import MagicMock, patch
from santander_client.api_client.exceptions import SantanderClientException
from santander_client.api_client.workspaces import (
    WORKSPACES_ENDPOINT,
    get_workspaces,
    get_first_workspace_id_of_type,
    _check_client_instance,
)
from santander_client.api_client.client import SantanderApiClient
from tests.mock.santander_mocker import (
    no_payments_workspaces_mock,
    workspace_response_mock,
)


class UnitTestWorkspaces(unittest.TestCase):
    def setUp(self):
        self.mock_client = MagicMock(spec=SantanderApiClient)

    def test_get_workspaces(self):
        mock_response = workspace_response_mock
        self.mock_client.get.return_value = mock_response

        workspaces = get_workspaces(self.mock_client)
        self.mock_client.get.assert_called_once_with(WORKSPACES_ENDPOINT)
        self.assertEqual(workspaces, mock_response["_content"])

    def test_get_workspaces_no_content(self):
        mock_response = {}
        self.mock_client.get.return_value = mock_response

        workspaces = get_workspaces(self.mock_client)
        self.mock_client.get.assert_called_once_with(WORKSPACES_ENDPOINT)
        self.assertIsNone(workspaces)

    def test_get_first_workspace_id_of_type(self):
        workspace_payment_and_active = workspace_response_mock["_content"][2]
        with patch(
            "santander_client.api_client.workspaces.get_workspaces",
            return_value=workspace_response_mock["_content"],
        ):
            workspace_id = get_first_workspace_id_of_type(self.mock_client, "PAYMENTS")
            self.assertEqual(workspace_id, workspace_payment_and_active["id"])

    def test_get_first_workspace_id_of_type_no_match(self):
        with patch(
            "santander_client.api_client.workspaces.get_workspaces",
            return_value=no_payments_workspaces_mock["_content"],  # Corrigir erro de digitação
        ):
            workspace_id = get_first_workspace_id_of_type(self.mock_client, "PAYMENTS")
            self.assertIsNone(workspace_id)

    def test_check_client_instance(self):
        _check_client_instance(self.mock_client)

        with self.assertRaises(SantanderClientException):
            _check_client_instance(object())
