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
from santander_client import SantanderApiClient, SantanderClientConfiguration

client = SantanderApiClient(SantanderClientConfiguration(
  client_id="client_id",
  client_secret="client_pk",
  cert="certificate_path",
  base_url="api_url"
))

# Realizar um PIX para uma chave
transfer = transfer_pix_payment(
    client,
    pix_info="alice@example.com", # PIX key
    value=Decimal(0.99),
    description="My first pix payment"
)

pix_info = get_transfer(transfer["id"])
# ...
```

## Em desenvolvimento
 - Será atualizado o README

## Funcionalidades

- **Autenticação**: Gerenciamento de tokens de acesso.
- **Informações da Conta**: Recuperação de detalhes da conta como workspace.
- **Transações**: Consulta de transações realizadas.
- **Pagamentos**: Realização de pagamentos e transferências pix com abstração do fluxo.


## Licença

Este projeto está licenciado sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## Aviso Legal

Este projeto não é afiliado, endossado ou patrocinado pelo Santander.
