import pytest
from unittest.mock import MagicMock, patch
from santander_sdk.api_client.workspaces import (
    WORKSPACES_ENDPOINT,
    get_workspaces,
    get_first_workspace_id_of_type,
)
from santander_sdk.api_client.client import SantanderApiClient
from mock.santander_mocker import (
    no_payments_workspaces_mock,
    workspace_response_mock,
)


@pytest.fixture
def mock_client():
    return MagicMock(spec=SantanderApiClient)


def test_get_workspaces(mock_client):
    mock_response = workspace_response_mock
    mock_client.get.return_value = mock_response

    workspaces = get_workspaces(mock_client)
    mock_client.get.assert_called_once_with(WORKSPACES_ENDPOINT)
    assert workspaces == mock_response["_content"]


def test_get_workspaces_no_content(mock_client):
    mock_response = {}
    mock_client.get.return_value = mock_response

    workspaces = get_workspaces(mock_client)
    mock_client.get.assert_called_once_with(WORKSPACES_ENDPOINT)
    assert workspaces is None


def test_get_first_workspace_id_of_type(mock_client):
    workspace_payment_and_active = workspace_response_mock["_content"][2]
    with patch(
        "santander_sdk.api_client.workspaces.get_workspaces",
        return_value=workspace_response_mock["_content"],
    ):
        workspace_id = get_first_workspace_id_of_type(mock_client, "PAYMENTS")
        assert workspace_id == workspace_payment_and_active["id"]


def test_get_first_workspace_id_of_type_no_match(mock_client):
    with patch(
        "santander_sdk.api_client.workspaces.get_workspaces",
        return_value=no_payments_workspaces_mock["_content"],
    ):
        workspace_id = get_first_workspace_id_of_type(mock_client, "PAYMENTS")
        assert workspace_id is None
