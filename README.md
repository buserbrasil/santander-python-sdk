# Santander Python SDK

An **unofficial** Python SDK for Santander's API that simplifies integration with Santander banking services.

[![test](https://github.com/buserbrasil/santander-python-sdk/actions/workflows/test.yml/badge.svg)](https://github.com/buserbrasil/santander-python-sdk/actions/workflows/test.yml)

## Features

- ✨ **Authentication**: Automatic token management
- 💰 **Account Information**: Retrieve account and workspace details
- 💸 **PIX Transfers**: Easy PIX payment processing
- 📊 **Transaction History**: Query and track transactions
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
from santander_sdk.pix import transfer_pix

transfer = transfer_pix(
    client,
    pix_key="recipient@email.com",
    value=Decimal("50.00"),
    description="Lunch payment"
)

# Check transfer status
from santander_sdk.pix import get_transfer

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

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Security

For security concerns, please email <foss@buser.com.br>.

## Acknowledgments

- Thanks to all contributors who have helped shape this SDK
- Built with support from the Python community

---

⭐ If you find this SDK helpful, please star the repository!
