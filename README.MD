# Santander Client API (Não Oficial)

Este é um cliente não oficial para a API do Santander, desenvolvido em Python. Ele permite a integração com os serviços do Santander de forma simples e abstraida.

## Instalação

Para instalar o pacote, utilize o pip:

```bash
pip install santander-python-sdk

## Uso
```
## Uso

```python
from decimal import Decimal
from santander_sdk import SantanderApiClient, SantanderClientConfiguration
from santander_sdk.pix import transfer_pix_payment, get_transfer

client = SantanderApiClient(SantanderClientConfiguration(
  client_id="client_id",
  client_secret="client_pk",
  cert="certificate_path",
  base_url="api_url",
  workspace_id="optional"
))

# Realizar um PIX para uma chave
transfer = transfer_pix_payment(
    client,
    pix_info="alice@example.com", # PIX key
    value=Decimal(0.99),
    description="My first pix payment"
)

# Obter informações de um pix realizado (SantanderTransferResponse | SantanderAPIErrorResponse)
transfer = get_transfer(transfer["id"])

status = transfer["status"] 

## Em desenvolvimento
 - Será atualizado o README
```

## Funcionalidades

- **Autenticação**: Gerenciamento de tokens de acesso.
- **Informações da Conta**: Recuperação de detalhes da conta como workspace.
- **Transações**: Consulta de transações realizadas.
- **Pagamentos**: Realização de pagamentos e transferências pix com abstração do fluxo.


## Licença

Este projeto está licenciado sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## Aviso Legal

Este projeto não é afiliado, endossado ou patrocinado pelo Santander.
