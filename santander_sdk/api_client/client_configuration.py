from typing import Literal
import logging


class SantanderClientConfiguration:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        cert: str,
        base_url: str,
        workspace_id: str = "",
        log_request_response_level: Literal["ERROR", "ALL", "NONE"] = "ERROR",
        logger: logging.Logger | None = None,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.workspace_id = workspace_id
        self.cert = cert
        self.base_url = base_url
        self.log_request_response_level = log_request_response_level
        self.logger = logger or logging.getLogger(__name__)

    def set_workspace_id(self, workspace_id: str):
        self.workspace_id = workspace_id

    def __repr__(self):
        return (
            f"SantanderClientConfiguration<client_id={self.client_id} cert={self.cert}>"
        )
