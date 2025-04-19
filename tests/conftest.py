import pytest
from santander_sdk.api_client.client import SantanderApiClient
from santander_sdk.api_client.client_configuration import SantanderClientConfiguration
from tests.mock.santander_mocker import SANTANDER_URL, TEST_WORKSPACE_ID, mock_auth_endpoint


@pytest.fixture
def client_instance():
    return SantanderApiClient(
        SantanderClientConfiguration(
            client_id="buser",
            client_secret="secret",
            cert="/var/cets/cert.pem",
            base_url=SANTANDER_URL,
            workspace_id=TEST_WORKSPACE_ID,
        )
    )

@pytest.fixture
def mock_auth(responses):
    mock_auth_endpoint(responses)