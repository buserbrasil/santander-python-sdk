# Santander Python SDK

An **unofficial** Python SDK for Santander's API that simplifies integration with Santander banking services.

[![test](https://github.com/buserbrasil/santander-python-sdk/actions/workflows/test.yml/badge.svg)](https://github.com/buserbrasil/santander-python-sdk/actions/workflows/test.yml)

## Features

- ✨ **Authentication**: Automatic token management
- 💰 **Account Information**: Retrieve account and workspace details
- 💸 **PIX Transfers**: Easy PIX payment processing
- 📑 **Receipts**: Query and retrieve receipts of any transaction
- 📊 **Transaction History**: Query and track transactions history
- 🔒 **Secure**: Built-in security best practices

## Installation

```bash
pip install santander-python-sdk
```

## Quick Start

```python
from decimal import Decimal
from santander_sdk import SantanderApiClient, SantanderClientConfiguration

# Initialize the client
client = SantanderApiClient(
    SantanderClientConfiguration(
        client_id="your_client_id",
        client_secret="your_client_secret",
        cert="path_to_certificate",
        base_url="api_url",
        workspace_id="optional_workspace_id"
    )
)

# Make a simple PIX transfer
from santander_sdk import transfer_pix

transfer = transfer_pix(
    client,
    pix_key="recipient@email.com",
    value=Decimal("50.00"),
    description="Lunch payment"
)

# Check transfer status
from santander_sdk import get_transfer

status = get_transfer(transfer["id"])
print(f"Transfer status: {status['status']}")
```

## Advanced Usage

### PIX Transfer to Bank Account

```python
from santander_sdk import SantanderBeneficiary

# Create beneficiary
beneficiary = SantanderBeneficiary(
    name="John Doe",
    bankCode="404",  # Santander bank code
    branch="2424",
    number="123456789",  # Account number with check digit
    type="CONTA_CORRENTE",
    documentType="CPF",
    documentNumber="12345678909"
)

# Make transfer
transfer = transfer_pix(
    client,
    beneficiary,
    value=Decimal("100.00"),
    description="Rent payment"
)
```

### List Payments to get useful information
You can get the list of payments made, filtering by payment type, recipient, etc. See `ListPaymentParams` for all possible filters. One use case, for example, is when you want to generate a receipt but don't have the payment ID.

```python
from santander_sdk import payment_list, ListPaymentParams

payments = payment_list(client, ListPaymentParams(
    start_date="2025-01-01",
    end_date="2025-01-02",
))
payment_id = payments[0]["payment"]["paymentId"]
```

### Create a Receipt Request

Create a receipt request using the payment ID.
```python
from santander_sdk import create_receipt

create_response = create_receipt(client, "MY-PAYMENT-ID")
```
The receipt creation is asynchronous on Santander. You will likely receive a response indicating that your receipt has been requested. Since the process is asynchronous, you should check back later to retrieve it.


### Get the Receipt Information/URL

To obtain the receipt information, you need the payment id and the `receipt_request_id` (which is generated when you made the request on `create_receipt`).

```python
from santander_sdk import get_receipt

receipt_info = get_receipt(client, payment_id, receipt_request_id)

print('Receipt Status:', receipt_info["status"])
print('Receipt URL Location:', receipt_info["location"])
print('Full Information:', receipt_info["data"])
```

## Advanced usage of Receipts 

### Iterate Over Payments List

If the payments list is too large and you want to iterate over them, use `payment_list_iter_by_pages`.

```python
from santander_sdk import payment_list_iter_by_pages, ListPaymentParams

# Filtering by one month with a return of 2 payments per page, the max per page is 1000
payments_pages = payment_list_iter_by_pages(client, ListPaymentParams(
    start_date="2025-02-01", 
    end_date="2025-02-28", 
    _limit="2")
)

for page in payments_pages:
    print('Page:', page)
```

### Obtain Receipt Creation History

To obtain the history of receipt creation:

```python
from santander_sdk.payment_receipts import receipt_creation_history

history = receipt_creation_history(client, payment_id)
print('Receipt Creation History:', history)
```
This function is used internally to handle cases where a receipt request has expired or encountered an error. However, you can use it to view all receipt creation requests that have been made.


## Contributing

We welcome contributions! Here's how you can help:

### Setting up Development Environment

1. Clone the repository

```bash
git clone https://github.com/yourusername/santander-python-sdk
cd santander-python-sdk
```

2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install development dependencies

```bash
pip install -e ".[dev]"
```

### Development Guidelines

- Write tests for new features using pytest
- Follow PEP 8 style guide
- Add docstrings to new functions and classes
- Update documentation when adding features

### Running Tests

```bash
pytest tests/
```

### Submitting Changes

1. Fork the repository
2. Create a new branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Support

- 📫 Open an issue for bugs or feature requests
- 💬 Join our [Discord community](link-to-discord) for discussions
- 📖 Check our [FAQ](link-to-faq) for common questions

## Santander oficial documentation

 - [User guide introduction](https://developer.santander.com.br/api/user-guide/user-guide-introduction)
 - [Pix, Boleto, transfer flow](https://developer.santander.com.br/api/documentacao/transferencias-pix-visao-geral#/)
 - [Receipts](https://developer.santander.com.br/api/documentacao/comprovantes-visao-geral#/)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Security

For security concerns, please email <foss@buser.com.br>.

## Acknowledgments

- Thanks to all contributors who have helped shape this SDK
- Built with support from the Python community

---

⭐ If you find this SDK helpful, please star the repository!
