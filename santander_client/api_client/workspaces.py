from typing import Literal

from .abstract_client import SantanderAbstractApiClient
from .exceptions import SantanderClientException

"""
    Para ter acesso ao sistema cliente e consumir as APIs, se faz necessário ter o cadastro de
    uma ou mais Workspaces, sendo a Workspace a “porta de entrada” para ter o acesso ao Hub de
    Pagamentos transacional. Rotas de pagamentos, geração de pix, etc, vão precisar do id do workspace.
    
    Existem os seguintes tipos de workspaces
    - PAYMENTS para o cliente que deseja fazer pagamentos próprios;
    - DIGITAL_CORBAN para o cliente que deseja fazer pagamentos de terceiros de maneira digital;
    - PHYSICAL_CORBAN para o cliente que deseja fazer pagamentos e ser correspondente bancário
    de maneira subestabelecida ou direta.
    
    ### No nosso caso, o uso será para o tipo PAYMENTS.
"""
WorkspaceType = Literal["PHYSICAL_CORBAN", "PAYMENTS", "DIGITAL_CORBAN"]


WORKSPACES_ENDPOINT = "/management_payments_partners/v1/workspaces"


def get_workspaces(client: SantanderAbstractApiClient):
    _check_client_instance(client)
    response = client.get(WORKSPACES_ENDPOINT)
    return response.get("_content", None)


def get_first_workspace_id_of_type(
    client: SantanderAbstractApiClient, workspace_type: WorkspaceType
) -> str | None:
    _check_client_instance(client)
    workspaces = get_workspaces(client)
    if len(workspaces) == 0:
        return None

    workspace_id = next(
        (
            w["id"]
            for w in workspaces
            if w.get("type") == workspace_type and w.get("status") == "ACTIVE"
        ),
        None,
    )
    return workspace_id


def _check_client_instance(client):
    if not client:
        raise SantanderClientException("O client é obrigatório")

    if not issubclass(client.__class__, SantanderAbstractApiClient):
        raise SantanderClientException(
            "O client deve ser uma instância de Herança de BaseSantanderApiClient"
        )
