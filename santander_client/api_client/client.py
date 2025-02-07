from datetime import datetime, timedelta
from urllib.parse import urljoin
import requests

from .helpers import get_status_code_description, try_parse_response_to_json

from .abstract_client import SantanderAbstractApiClient
from .client_configuration import SantanderClientConfiguration
from .exceptions import SantanderRequestException, SantanderClientException

BEFORE_EXPIRE_TOKEN_SECONDS = timedelta(seconds=60)
TOKEN_ENDPOINT = "/auth/oauth/v2/token"


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
        if not isinstance(config, SantanderClientConfiguration):
            raise SantanderClientConfiguration("Objeto de autenticação inválido")

        self.base_url = config.base_url.rstrip("/")
        self.config = config
        self.session = requests.Session()
        self.token = None
        self.token_expires_at = datetime.now()

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

    @property
    def is_authenticated(self) -> bool:
        return bool(
            self.token
            and (self.token_expires_at - BEFORE_EXPIRE_TOKEN_SECONDS) > datetime.now()
        )

    def _ensure_requirements(self) -> None:
        if not self.is_authenticated:
            self._authenticate()

    def _authenticate(self) -> None:
        token_data = self._request_token()
        self.token = token_data.get("access_token", "")
        if not self.token:
            raise SantanderClientException("Token de autenticação não encontrado")

        self.token_expires_at = datetime.now() + timedelta(
            seconds=token_data.get("expires_in", 120)
        )
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.token}",
                "X-Application-Key": self.config.client_id,
            }
        )
        self.session.verify = True
        self.session.cert = self.config.cert  # pyright: ignore

    def _request_token(self) -> dict:
        url = urljoin(self.base_url, TOKEN_ENDPOINT)
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "grant_type": "client_credentials",
        }
        try:
            response = self.session.post(
                url,
                data=data,
                headers=headers,
                verify=True,
                timeout=60,
                cert=self.config.cert,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            status_code = getattr(e.response, "status_code", 0)
            response = try_parse_response_to_json(e.response)
            raise SantanderRequestException(
                f"Erro na obtenção do Token: {e}", status_code, response
            )
        token_data = response.json()
        return token_data

    def _prepare_url(self, endpoint: str) -> str:
        url = urljoin(self.base_url, endpoint).lower()

        if ":workspaceid" in url:
            if not self.config.workspace_id:
                raise SantanderClientException("ID da workspace não configurado")
            url = url.replace(":workspaceid", self.config.workspace_id)
        return url

    def _request(
        self,
        method: str,
        endpoint: str,
        data: dict | None = None,
        params: dict | None = None,
    ) -> dict:
        self._ensure_requirements()
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
