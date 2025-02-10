import pytest

from santander_client.api_client.client import SantanderApiClient
from santander_client.api_client.client_configuration import (
    SantanderClientConfiguration,
)


@pytest.fixture
def api_client():
    return SantanderApiClient(
        SantanderClientConfiguration(
            client_id="test_client_id",
            client_secret="test_client_secret",
            cert="certificate_path",
            base_url="https://trust-sandbox.api.santander.com.br",
            workspace_id="8e33d56c-204f-461e-aebe-08baaab6479e",
        )
    )
