class SantanderClientConfiguration:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        cert: str,
        base_url: str,
        workspace_id: str = "",
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.workspace_id = workspace_id
        self.cert = cert
        self.base_url = base_url

    def set_workspace_id(self, workspace_id: str):
        self.workspace_id = workspace_id

    def __repr__(self):
        return (
            f"SantanderClientConfiguration<client_id={self.client_id} cert={self.cert}>"
        )
