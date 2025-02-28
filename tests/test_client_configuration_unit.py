import unittest
from santander_sdk.api_client.client_configuration import (
    SantanderClientConfiguration,
)
from mock.santander_mocker import client_santander_client_config_mock


class UnitTestSantanderClientConfiguration(unittest.TestCase):
    def setUp(self):
        self.config = SantanderClientConfiguration(
            **client_santander_client_config_mock
        )

    def test_set_workspace_id(self):
        new_workspace_id = "new_workspace_id"
        self.config.set_workspace_id(new_workspace_id)
        self.assertEqual(self.config.workspace_id, new_workspace_id)
