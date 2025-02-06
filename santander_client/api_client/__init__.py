import logging
from typing import TypedDict
from .exceptions import SantanderConfigurationException, SantanderWorkspaceException
from .workspaces import get_first_workspace_id_of_type
from .client import SantanderApiClient
from .client_configuration import SantanderClientConfiguration
  
logger = logging.getLogger("santanderLogger")
      
santander_client_configuration = None
      
def set_configuration(configuration: SantanderClientConfiguration) -> None:
    if not isinstance(configuration, SantanderClientConfiguration):
        raise SantanderConfigurationException("Configuração inválida fornecida.")
    
    global santander_client_configuration
    santander_client_configuration = configuration
      
def get_client() -> SantanderApiClient:
    """
    Creates and returns an instance of SantanderApiClient based on the provided configuration.
    """
    if not santander_client_configuration:
        raise SantanderConfigurationException("Configuração do client (SantanderClientConfiguration) não foi denida.")

    santander_client_instance = SantanderApiClient(santander_client_configuration)

    if not santander_client_configuration.workspace_id:
        workspace_id = get_first_workspace_id_of_type(santander_client_instance, "PAYMENTS")
        if not workspace_id:
            raise SantanderWorkspaceException("Conta sem configuração de workspace na configuração e na conta.")

        logger.info(f"Workspace obtido e configurado com sucesso: {workspace_id}")
        santander_client_configuration.set_workspace_id(workspace_id)

    return santander_client_instance
