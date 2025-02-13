import logging
from datetime import datetime, timedelta

import requests

from santander_sdk.api_client.auth import SantanderAuth
from santander_sdk.api_client.base import BaseURLSession
from santander_sdk.api_client.workspaces import get_first_workspace_id_of_type

from .abstract_client import SantanderAbstractApiClient
from .client_configuration import SantanderClientConfiguration
from .exceptions import (
    SantanderClientException,
    SantanderRequestException,
    SantanderWorkspaceException,
)
from .helpers import get_status_code_description, try_parse_response_to_json

BEFORE_EXPIRE_TOKEN_SECONDS = timedelta(seconds=60)
TOKEN_ENDPOINT = "/auth/oauth/v2/token"

logger = logging.getLogger(__name__)


class SantanderApiClient(SantanderAbstractApiClient):
    """
    Cliente base para requisições à API do Santander.
    Lida de forma auto gerenciada com requisitos, autenticação, token e manutenção de sessão com a API do Santander.

    #### Inicialização:
    - É necessário informar a URL base da API e a configuração de autenticação (SantanderClientConfiguration).

    #### Endpoints dos métodos HTTPS (get, post, put, delete, patch):
     - Deve ser informado o endpoint relativo, sem a URL base.
     - Poderá ser informado o slug :workspaceid no endpoint, que será substituído pelo ID da workspace configurada.
     - Caso o slug :workspaceid seja informado e não haja ID de workspace configurado, será lançada uma exceção.


    #### Exceções:
    - SantanderClientException: O fluxo não seguiu conforme o esperado ou houve na troca de informações com a API
    - SantanderRequestException: Lançado em caso de códigos de retorno HTTP diferentes de 2xx.
    - SantanderConfigurationException: Há um erro a nível de configuração do cliente Santander.
    - SantanderWorkspaceException: Erro na obtenção ou configuração da workspace.

    """

    def __init__(self, config: SantanderClientConfiguration):
        self.config = config
        self._set_default_workspace_id()

        self.session = BaseURLSession(base_url=config.base_url)
        self.session.auth = SantanderAuth.from_config(config)

    def _set_default_workspace_id(self):
        if not self.config.workspace_id:
            workspace_id = get_first_workspace_id_of_type(self, "PAYMENTS")
            if not workspace_id:
                raise SantanderWorkspaceException(
                    "Conta sem configuração de workspace na configuração e na conta."
                )

            logger.info(f"Workspace obtido e configurado com sucesso: {workspace_id}")
            self.config.set_workspace_id(workspace_id)

    def get(self, endpoint: str, params: dict | None = None) -> dict:
        return self._request("GET", endpoint, params=params)

    def post(self, endpoint: str, data: dict) -> dict:
        return self._request("POST", endpoint, data=data)

    def put(self, endpoint: str, data: dict) -> dict:
        return self._request("PUT", endpoint, data=data)

    def delete(self, endpoint: str) -> dict:
        return self._request("DELETE", endpoint)

    def patch(self, endpoint: str, data: dict) -> dict:
        return self._request("PATCH", endpoint, data=data)

    def _prepare_url(self, endpoint: str) -> str:
        endpoint = endpoint.lower()
        if ":workspaceid" in endpoint:
            if not self.config.workspace_id:
                raise SantanderClientException("ID da workspace não configurado")
            endpoint = endpoint.replace(":workspaceid", self.config.workspace_id)

        return endpoint

    def _request(
        self,
        method: str,
        endpoint: str,
        data: dict | None = None,
        params: dict | None = None,
    ) -> dict:
        url = self._prepare_url(endpoint)
        try:
            response = self.session.request(
                method, url, json=data, params=params, timeout=60
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            status_code = getattr(e.response, "status_code", 0)
            error_content = try_parse_response_to_json(e.response)
            status_description = get_status_code_description(status_code)

            raise SantanderRequestException(
                status_description, status_code, error_content
            )
        except Exception as e:
            raise SantanderRequestException(f"Erro na requisição: {e}", 0, None) from e
