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
from santander_sdk import (
  SantanderApiClient,
  SantanderClientConfiguration
  SantanderBeneficiary,
)
from santander_sdk.pix import transfer_pix, get_transfer

# Setup do client
client = SantanderApiClient(SantanderClientConfiguration(
  client_id="client_id",
  client_secret="client_pk",
  cert="certificate_path",
  base_url="api_url",
  workspace_id="optional"
))

# Exemplo 1 - PIX para uma chave (Telefone, email, chave aleatória, cpf ou cpnj)
transfer = transfer_pix(
    client,
    pix_key="alice@example.com",
    value=Decimal(0.99),
    description="My first pix payment"
)

# Exemplo 2 - Transferência pix via beneficiário:
benefiary = SantanderBeneficiary(
    name="John Doe",
    bankCode="404",
    branch="2424",
    number="123456789", # Número da conta com dígito verificador
    type="CONTA_CORRENTE",
    documentType="CPF",
    documentNumber="12345678909",
)

transfer = transfer_pix(
    client,
    benefiary,
    value=Decimal(0.99),
    description="My second pix payment by beneficiary"
)


# Exemplo 3 - Consulta de um pix realizado 
transfer = get_transfer(transfer["id"])
assert transfer["status"] == "PAYED"


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
