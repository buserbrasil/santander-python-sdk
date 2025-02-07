from decimal import Decimal
from urllib.parse import urljoin

from requests_mock import Mocker

from santander_client.api_client.client import TOKEN_ENDPOINT
from santander_client.api_client.workspaces import WORKSPACES_ENDPOINT
from santander_client.pix import PIX_ENDPOINT
from santander_client.types import BeneficiaryDataDict

SANTANDER_URL = "https://trust-sandbox.api.santander.com.br"
TEST_WORKSPACE_ID = "8e33d56c-204f-461e-aebe-08baaab6479e"
PIX_ENDPOINT_WITH_WORKSPACE = urljoin(
    SANTANDER_URL, PIX_ENDPOINT.replace(":workspaceid", TEST_WORKSPACE_ID)
)


def get_dict_payment_pix_response(
    id: str,
    value: Decimal,
    status: str,
    key: str | BeneficiaryDataDict = "12345678909",
    key_type: str = "CPF",
) -> dict:
    payment = {
        "obs": "payment mockado",
        "id": id,
        "workspaceId": "3870ba5d-d58e-4182-992f-454e5d0e08e2",
        "debitAccount": {
            "branch": "0001",
            "number": "123456789",
        },
        "status": status,
        "tags": [],
        "remittanceInformation": "informação da transferência",
        "nominalValue": value,
        "deductedValue": "0.00",
        "addedValue": "0.00",
        "totalValue": value,
        "payer": {
            "name": "John Doe SA",
            "documentType": "CPNJ",
            "documentNumber": "20157935000193",
        },
        "transaction": {
            "value": value,
            "code": "13a654q",
            "date": "2025-01-08T13:44:36Z",
            "endToEnd": "a213e5q564as456f4as56f",
        },
        "paymentValue": value,
    }

    if isinstance(key, str):
        payment.update({"dictCode": key, "dictCodeType": key_type})
        return payment

    beneficiary = {
        "branch": key["bank_account"]["agencia"],
        "number": f"{key['bank_account']['conta']}{key['bank_account']['conta_dv']}",
        "type": key["bank_account"]["tipo_conta"],
        "documentType": "CPNJ"
        if len(key["bank_account"]["document_number"]) > 11
        else "CPF",
        "documentNumber": key["bank_account"]["document_number"],
        "name": key["recebedor"]["name"],
    }
    if key["bank_account"].get("bank_code_compe"):
        beneficiary["bankCode"] = key["bank_account"]["bank_code_compe"]
    else:
        beneficiary["ispb"] = key["bank_account"]["bank_code_ispb"]
    payment.update({"beneficiary": beneficiary})

    return payment


def get_dict_payment_pix_request(
    id: str, value: str, key: str | BeneficiaryDataDict, key_type: str = ""
) -> dict:
    payment = {
        "paymentValue": value,
        "remittanceInformation": "informação da transferência",
        "tags": ["RH", "123456"],
    }

    if isinstance(key, str):
        payment.update({"dictCode": key, "dictCodeType": key_type})
        return payment

    beneficiary = {
        "branch": key["bank_account"]["agencia"],
        "number": f"{key['bank_account']['conta']}{key['bank_account']['conta_dv']}",
        "type": key["bank_account"]["tipo_conta"],
        "documentType": "CPNJ"
        if len(key["bank_account"]["document_number"]) > 11
        else "CPF",
        "documentNumber": key["bank_account"]["document_number"],
        "name": key["recebedor"]["name"],
    }
    if key.get("bank_code"):
        beneficiary["bankCode"] = key["bank_account"]["bank_code_compe"]
    else:
        beneficiary["ispb"] = key["bank_account"]["bank_code_ispb"]
    payment.update({"beneficiary": beneficiary})

    return payment


def get_dict_workspace_response(
    id: str, type: str, status: str, creation_date: str
) -> dict:
    return {
        "obs": "workspace mockado",
        "id": id,
        "type": type,
        "status": status,
        "creationDate": creation_date,
        "mainDebitAccount": {"branch": "0001", "number": "130392838"},
        "additionalDebitAccounts": [
            {"branch": "0001", "number": "130476959"},
            {"branch": "0001", "number": "130380064"},
        ],
        "tags": ["client:123", "18/04/2023"],
        "description": "CreateTest",
        "webhookURL": None,
        "pixPaymentsActive": True,
        "barCodePaymentsActive": True,
        "bankSlipPaymentsActive": True,
        "bankSlipAvailableActive": True,
        "taxesByFieldPaymentsActive": True,
        "vehicleTaxesPaymentsActive": True,
        "bankSlipAvailableWebhookActive": True,
    }


def get_dict_token_response() -> dict:
    return {
        "obs": "token mockado",
        "access_token": "eyJraWQiOiI1MDZhY2QwYS0zN2M2LTQ2NjktYWYwZS0yODR..",
        "expires_in": 900,
        "token_type": "bearer",
        "not-before-policy": 1614173461,
        "session_state": "2ddeacf0-1e7d-4351-ba78-abb286373bd1",
        "scope": "",
    }


def get_dict_token_request() -> dict:
    return {
        "client_id": "test_client_id",
        "client_secret": "test_client_secret",
        "grant_type": "client_credentials",
    }


def mock_create_pix_endpoint(
    mocker: Mocker,
    pix_id: str,
    value: Decimal,
    status: str,
    pix_info: str | BeneficiaryDataDict,
    key_type: str = "CPF",
) -> Mocker:
    post_response = get_dict_payment_pix_response(
        pix_id, value, status, pix_info, key_type
    )
    return mocker.post(PIX_ENDPOINT_WITH_WORKSPACE, json=post_response)


def mock_confirm_pix_endpoint(
    mocker: Mocker,
    pix_id: str,
    value: Decimal,
    status: str,
    pix_info: str | BeneficiaryDataDict,
    key_type: str = "CPF",
) -> Mocker:
    patch_response = get_dict_payment_pix_response(
        pix_id, value, status, pix_info, key_type
    )
    return mocker.patch(f"{PIX_ENDPOINT_WITH_WORKSPACE}/{pix_id}", json=patch_response)


def mock_pix_status_endpoint(
    mocker: Mocker,
    pix_id: str,
    value: Decimal,
    status: str,
    pix_info: str | BeneficiaryDataDict,
    key_type: str = "CPF",
) -> Mocker:
    get_response = get_dict_payment_pix_response(
        pix_id, value, status, pix_info, key_type
    )
    return mocker.get(f"{PIX_ENDPOINT_WITH_WORKSPACE}/{pix_id}", json=get_response)


def mock_get_workspaces_endpoint(mocker: Mocker) -> Mocker:
    return mocker.get(
        urljoin(SANTANDER_URL, WORKSPACES_ENDPOINT), json=workspace_response_mock
    )


def mock_token_endpoint(mocker: Mocker) -> Mocker:
    token_response = get_dict_token_response()
    return mocker.post(urljoin(SANTANDER_URL, TOKEN_ENDPOINT), json=token_response)


beneficiary_dict_john_cc = BeneficiaryDataDict(
    bank_account={
        "agencia": "123",
        "conta": "123456789",
        "conta_dv": "9",
        "tipo_conta": "checking",
        "document_number": "12345678909",
        "bank_code_compe": "123",
        "bank_code_ispb": "789123",
    },
    recebedor={
        "name": "John Doe",
    },
)

payment_response_by_beneficiary = get_dict_payment_pix_response(
    "12345678", 299.99, "READY_TO_PAY", beneficiary_dict_john_cc
)
payment_response_by_beneficiary = get_dict_payment_pix_request(
    "12345678", 299.99, beneficiary_dict_john_cc
)


workspace_digital_corban = get_dict_workspace_response(
    "3870ba5d-d58e-4182-992f-454e5d0e08e2",
    "DIGITAL_CORBAN",
    "ACTIVE",
    "2025-01-07T15:00:15Z",
)


workspace_physical_corban = get_dict_workspace_response(
    "3870baea", "PHYSICAL_CORBAN", "ACTIVE", "2025-01-07T15:00:15Z"
)
workspace_payments_active = get_dict_workspace_response(
    TEST_WORKSPACE_ID, "PAYMENTS", "ACTIVE", "2025-01-07T15:00:15Z"
)
workspace_payments_active2 = get_dict_workspace_response(
    "12345678", "PAYMENTS", "ACTIVE", "2025-02-01T12:00:00Z"
)
workspace_payments_disabled = get_dict_workspace_response(
    "3870ba5d", "PAYMENTS", "DISABLED", "2025-01-07T15:00:15Z"
)
workspace_response_mock = {
    "_content": [
        workspace_digital_corban,
        workspace_physical_corban,
        workspace_payments_active,
        workspace_payments_active2,
        workspace_payments_disabled,
    ]
}

no_payments_workspaces_mock = {
    "_content": [
        workspace_digital_corban,
        workspace_physical_corban,
        workspace_payments_disabled,
    ]
}

cert_mock_content = "a" * 512

invalid_config_cases = [
    {
        "description": "Teste de exeption, configuração certificado faltando",
        "cert_base64_content": "",
        "client_id": "test_client_id",
        "client_secret": "test_client_secret",
        "account_id": "test_account_id",
        "agency_number": "test_agency_number",
    },
    {
        "description": "Teste de exeption, configuração client_id faltando",
        "cert_base64_content": cert_mock_content,
        "client_id": "",
        "client_secret": "test_client_secret",
        "account_id": "test_account_id",
        "agency_number": "test_agency_number",
    },
    {
        "description": "Teste de exeption, configuração client_secret faltando",
        "cert_base64_content": cert_mock_content,
        "client_id": "test_client_id",
        "client_secret": "",
        "account_id": "test_account_id",
        "agency_number": "test_agency_number",
    },
]

client_santander_client_config_mock = {
    "client_id": "a1e23a135e4a4e35ae",
    "client_secret": "E56q6ASf3e8844",
    "cert": "temp_cert.pem",
    "workspace_id": TEST_WORKSPACE_ID,
    "base_url": SANTANDER_URL,
}
