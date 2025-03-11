from decimal import Decimal
from typing import cast
from urllib.parse import urljoin

from responses import RequestsMock
import responses

from santander_sdk.api_client.client import TOKEN_ENDPOINT
from santander_sdk.api_client.workspaces import WORKSPACES_ENDPOINT
from santander_sdk.pix import PIX_ENDPOINT
from santander_sdk.types import SantanderBeneficiary, OrderStatus

SANTANDER_URL = "https://trust-sandbox.api.santander.com.br"
BASE_URL_RECEIPTS = "https://trust-sandbox.api.santander.com.br/consult_payment_receipts/v1/payment_receipts"
TEST_WORKSPACE_ID = "8e33d56c-204f-461e-aebe-08baaab6479e"
PIX_ENDPOINT_WITH_WORKSPACE = urljoin(
    SANTANDER_URL, PIX_ENDPOINT.replace(":workspaceid", TEST_WORKSPACE_ID)
)


def get_dict_payment_pix_response(
    id: str,
    value: Decimal,
    status: str,
    key: str | SantanderBeneficiary = "12345678909",
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
        "nominalValue": str(value),
        "deductedValue": "0.00",
        "addedValue": "0.00",
        "totalValue": str(value),
        "payer": {
            "name": "John Doe SA",
            "documentType": "CPNJ",
            "documentNumber": "20157935000193",
        },
        "transaction": {
            "value": str(value),
            "code": "13a654q",
            "date": "2025-01-08T13:44:36Z",
            "endToEnd": "a213e5q564as456f4as56f",
        },
        "paymentValue": str(value),
    }

    if isinstance(key, str):
        payment.update({"dictCode": key, "dictCodeType": key_type})
        return payment

    payment.update({"beneficiary": beneficiary_as_dict_json(key)})
    return payment


def beneficiary_as_dict_json(beneficiary: SantanderBeneficiary) -> dict:
    beneciary_dict = cast(dict, beneficiary.copy())
    bank_code = beneciary_dict.get("bankCode", "")
    ispb = beneciary_dict.get("ispb", "")
    if bank_code and ispb:
        del beneciary_dict["ispb"]
    elif not bank_code and not ispb:
        raise ValueError("Deve ser informado 'bankCode' ou 'ispb'")

    return beneciary_dict


def get_dict_payment_pix_request(
    id: str,
    value: Decimal,
    key: str | SantanderBeneficiary,
    key_type: str = "",
) -> dict:
    payment = {
        "paymentValue": value,
        "remittanceInformation": "informação da transferência",
        "tags": ["RH", "123456"],
    }

    if isinstance(key, str):
        payment.update({"dictCode": key, "dictCodeType": key_type})
        return payment

    payment.update({"beneficiary": beneficiary_as_dict_json(key)})
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


dict_token_response = {
    "obs": "token mockado",
    "access_token": "eyJraWQiOiI1MDZhY2QwYS0zN2M2LTQ2NjktYWYwZS0yODR..",
    "expires_in": 900,
    "token_type": "bearer",
    "not-before-policy": 1614173461,
    "session_state": "2ddeacf0-1e7d-4351-ba78-abb286373bd1",
    "scope": "",
}


def mock_create_pix_endpoint(
    responses: RequestsMock,
    pix_id: str,
    value: Decimal,
    status: str,
    pix_info: str | SantanderBeneficiary,
    key_type: str = "CPF",
):
    post_response = get_dict_payment_pix_response(
        pix_id, value, status, pix_info, key_type
    )
    return responses.post(PIX_ENDPOINT_WITH_WORKSPACE, json=post_response)


def mock_confirm_pix_endpoint(
    responses: RequestsMock,
    pix_id: str,
    value: Decimal,
    status: str,
    pix_info: str | SantanderBeneficiary,
    key_type: str = "CPF",
):
    patch_response = get_dict_payment_pix_response(
        pix_id, value, status, pix_info, key_type
    )
    return responses.patch(
        f"{PIX_ENDPOINT_WITH_WORKSPACE}/{pix_id}", json=patch_response
    )


def mock_pix_status_endpoint(
    responses: RequestsMock,
    pix_id: str,
    value: Decimal,
    status: str,
    pix_info: str | SantanderBeneficiary,
    key_type: str = "CPF",
):
    get_response = get_dict_payment_pix_response(
        pix_id, value, status, pix_info, key_type
    )
    return responses.get(f"{PIX_ENDPOINT_WITH_WORKSPACE}/{pix_id}", json=get_response)


beneciary_john_dict_json = {
    "name": "John Doe",
    "documentType": "CPF",
    "documentNumber": "12345678909",
    "bankCode": "404",
    "branch": "2424",
    "number": "123456789",
    "type": "CONTA_CORRENTE",
}


santander_beneciary_john = SantanderBeneficiary(
    bankCode="404",
    branch="2424",
    number="123456789",
    type="CONTA_CORRENTE",
    documentType="CPF",
    documentNumber="12345678909",
    ispb="789123",
    name="John Doe",
)

payment_response_by_beneficiary = get_dict_payment_pix_response(
    "12345678", Decimal("299.99"), OrderStatus.READY_TO_PAY, santander_beneciary_john
)
payment_response_by_beneficiary = get_dict_payment_pix_request(
    "12345678", Decimal("299.99"), santander_beneciary_john
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


def receipt_history_response_dict(
    receipt_request_id,
    receipt_stauts="REQUESTED",
):
    return {
        "paymentReceiptsFileRequests": [
            {
                "request": {
                    "requestId": receipt_request_id,
                    "creationDateTime": "2025-03-07T12:32:38-03:00",
                },
                "file": {
                    "fileRepository": {"location": None},
                    "mimeType": "application/pdf",
                    "expirationDate": None,
                    "statusInfo": {"statusCode": receipt_stauts},
                    "audit": {"creationDateTime": None},
                },
            }
        ],
        "links": {
            "_first": {"href": f"{BASE_URL_RECEIPTS}?_offset=0&_limit=10"},
            "_prev": None,
            "_next": None,
        },
    }


def receipt_response_dict(
    receipt_request_id,
    receipt_status="REQUESTED",
    receipt_location: str | None = None,
):
    return {
        "request": {
            "requestId": receipt_request_id,
            "creationDateTime": "2025-03-07T12:32:38-03:00",
        },
        "file": {
            "fileRepository": {"location": receipt_location},
            "mimeType": "application/pdf",
            "expirationDate": "2025-04-07T12:32:38-03:00" if receipt_location else None,
            "statusInfo": {"statusCode": receipt_status},
            "audit": {
                "creationDateTime": "2025-03-07T12:32:38-03:00"
                if receipt_location
                else None
            },
        },
    }


def mock_workspaces_endpoint():
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add(
            responses.GET,
            urljoin(SANTANDER_URL, WORKSPACES_ENDPOINT),
            json=workspace_response_mock,
        )
        return rsps


def mock_auth_endpoint(responses: RequestsMock):
    return responses.add(
        responses.POST, urljoin(SANTANDER_URL, TOKEN_ENDPOINT), json=dict_token_response
    )
