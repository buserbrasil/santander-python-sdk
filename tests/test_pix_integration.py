import pytest
import requests_mock
from decimal import Decimal
from santander_sdk.api_client.client import SantanderApiClient
from santander_sdk.pix import (
    MAX_UPDATE_STATUS_ATTEMPTS,
    MAX_UPDATE_STATUS_ATTEMPTS_TO_CONFIRM,
    transfer_pix,
)
from mock.santander_mocker import (
    PIX_ENDPOINT_WITH_WORKSPACE,
    santander_beneciary_john,
    beneciary_john_dict_json,
    get_dict_payment_pix_response,
    mock_confirm_pix_endpoint,
    mock_create_pix_endpoint,
    mock_get_workspaces_endpoint,
    mock_pix_status_endpoint,
    mock_token_endpoint,
)
from santander_sdk.types import OrderStatus


@pytest.fixture
def mock_api(mocker):
    mocker.patch("santander_sdk.pix.sleep", return_value=None)
    with requests_mock.Mocker() as m:
        mock_get_workspaces_endpoint(m)
        mock_token_endpoint(m)
        yield m


def test_transfer_pix_payment_success(mock_api, api_client):
    pix_id = "12345"
    value = Decimal("100.00")
    description = "Pagamento Teste"
    pix_key = "12345678909"
    mock_create = mock_create_pix_endpoint(
        mock_api, pix_id, value, OrderStatus.READY_TO_PAY, pix_key, "CPF"
    )
    mock_confirm = mock_confirm_pix_endpoint(
        mock_api, pix_id, value, OrderStatus.PENDING_CONFIRMATION, pix_key, "CPF"
    )
    mock_status = mock_pix_status_endpoint(
        mock_api, pix_id, value, OrderStatus.PAYED, pix_key, "CPF"
    )
    transfer_result = transfer_pix(
        api_client, pix_key, value, description, tags=["teste"]
    )
    assert transfer_result == {
        "data": {
            "addedValue": "0.00",
            "debitAccount": {
                "branch": "0001",
                "number": "123456789",
            },
            "deductedValue": "0.00",
            "dictCode": "12345678909",
            "dictCodeType": "CPF",
            "id": "12345",
            "nominalValue": "100.00",
            "obs": "payment mockado",
            "payer": {
                "documentNumber": "20157935000193",
                "documentType": "CPNJ",
                "name": "John Doe SA",
            },
            "paymentValue": "100.00",
            "remittanceInformation": "informação da transferência",
            "status": OrderStatus.PAYED,
            "tags": [],
            "totalValue": "100.00",
            "transaction": {
                "code": "13a654q",
                "date": "2025-01-08T13:44:36Z",
                "endToEnd": "a213e5q564as456f4as56f",
                "value": "100.00",
            },
            "workspaceId": "3870ba5d-d58e-4182-992f-454e5d0e08e2",
        },
        "success": True,
        "error": "",
    }

    assert mock_create.call_count == 1
    assert mock_confirm.call_count == 1
    assert mock_status.call_count == 1
    assert mock_create.request_history[0].json() == {
        "tags": ["teste"],
        "paymentValue": "100.00",
        "remittanceInformation": description,
        "dictCode": pix_key,
        "dictCodeType": "CPF",
    }


def test_transfer_pix_payment_timeout_create(api_client: SantanderApiClient, mock_api):
    pix_id = "12345"
    value = Decimal("100.00")
    description = "Pagamento Teste"
    pix_key = "12345678909"

    mock_create = mock_create_pix_endpoint(
        mock_api, pix_id, value, OrderStatus.PENDING_VALIDATION, pix_key, "CPF"
    )
    mock_status = mock_pix_status_endpoint(
        mock_api, pix_id, value, OrderStatus.PENDING_VALIDATION, pix_key, "CPF"
    )
    transfer_result = transfer_pix(api_client, pix_key, value, description)

    assert transfer_result == {
        "success": False,
        "error": "Timeout na atualização do status após várias tentativas: Santander - Limite de tentativas de atualização do status do pagamento PIX atingido",
        "data": None,
    }
    assert mock_create.call_count == 1
    assert mock_status.call_count == MAX_UPDATE_STATUS_ATTEMPTS


def test_transfer_pix_payment_timeout_before_authorize(
    api_client: SantanderApiClient, mock_api
):
    pix_id = "QAS47FASF5646"
    value = Decimal("123.44")
    description = "Pagamento Teste"
    pix_key = "12345678909"

    mock_create = mock_create_pix_endpoint(
        mock_api, pix_id, value, OrderStatus.READY_TO_PAY, pix_key, "CPF"
    )
    mock_confirm = mock_confirm_pix_endpoint(
        mock_api, pix_id, value, OrderStatus.PENDING_CONFIRMATION, pix_key, "CPF"
    )
    mock_status = mock_pix_status_endpoint(
        mock_api, pix_id, value, OrderStatus.PENDING_CONFIRMATION, pix_key, "CPF"
    )

    transfer_result = transfer_pix(api_client, pix_key, value, description)
    assert transfer_result == {
        "success": True,
        "data": {
            "addedValue": "0.00",
            "debitAccount": {
                "branch": "0001",
                "number": "123456789",
            },
            "deductedValue": "0.00",
            "dictCode": "12345678909",
            "dictCodeType": "CPF",
            "id": pix_id,
            "nominalValue": "123.44",
            "obs": "payment mockado",
            "payer": {
                "documentNumber": "20157935000193",
                "documentType": "CPNJ",
                "name": "John Doe SA",
            },
            "paymentValue": "123.44",
            "remittanceInformation": "informação da transferência",
            "status": OrderStatus.PENDING_CONFIRMATION,
            "tags": [],
            "totalValue": "123.44",
            "transaction": {
                "code": "13a654q",
                "date": "2025-01-08T13:44:36Z",
                "endToEnd": "a213e5q564as456f4as56f",
                "value": "123.44",
            },
            "workspaceId": "3870ba5d-d58e-4182-992f-454e5d0e08e2",
        },
        "error": "",
    }
    assert mock_create.call_count == 1
    assert mock_confirm.call_count == 1
    assert mock_status.call_count == MAX_UPDATE_STATUS_ATTEMPTS_TO_CONFIRM


def test_transfer_pix_payment_rejected_on_create(
    api_client: SantanderApiClient, mock_api
):
    pix_id = "QASF4568E48Q"
    value = Decimal("100.00")
    description = "Pagamento Teste"
    pix_key = "12345678909"

    mock_create = mock_create_pix_endpoint(
        mock_api, pix_id, value, OrderStatus.REJECTED, pix_key, "CPF"
    )

    transfer_result = transfer_pix(api_client, pix_key, value, description)
    assert transfer_result == {
        "success": False,
        "error": "Rejeição de pagamento: Santander - Pagamento rejeitado pelo banco na etapa Criação do pagamento PIX - Motivo não retornado pelo Santander",
        "data": None,
    }
    assert mock_create.call_count == 1


def test_transfer_pix_payment_rejected_on_confirm(
    api_client: SantanderApiClient, mock_api
):
    pix_id = "5A4SD6Q5W6Q68A"
    value = Decimal("157.00")
    description = "Pagamento Teste"
    pix_key = "12345678909"

    mock_create = mock_create_pix_endpoint(
        mock_api, pix_id, value, OrderStatus.READY_TO_PAY, pix_key, "CPF"
    )
    mock_confirm = mock_confirm_pix_endpoint(
        mock_api, pix_id, value, OrderStatus.REJECTED, pix_key, "CPF"
    )
    mock_status = mock_pix_status_endpoint(
        mock_api, pix_id, value, OrderStatus.REJECTED, pix_key, "CPF"
    )

    transfer_result = transfer_pix(api_client, pix_key, value, description)
    assert transfer_result == {
        "success": False,
        "error": "Rejeição de pagamento: Santander - Pagamento rejeitado pelo banco na etapa Confirmação do pagamento PIX - Motivo não retornado pelo Santander",
        "data": None,
    }
    assert mock_create.call_count == 1
    assert mock_confirm.call_count == 1
    assert mock_status.call_count == 0


def test_transfer_pix_payment_with_beneficiary(
    api_client: SantanderApiClient, mock_api
):
    pix_id = "ASF5Q7Q879WQ"
    value = Decimal("59.99")
    description = "Pagamento Teste"

    mock_create = mock_create_pix_endpoint(
        mock_api,
        pix_id,
        value,
        OrderStatus.PENDING_VALIDATION,
        santander_beneciary_john,
    )
    mock_status = mock_pix_status_endpoint(
        mock_api, pix_id, value, OrderStatus.READY_TO_PAY, santander_beneciary_john
    )
    mock_confirm = mock_confirm_pix_endpoint(
        mock_api, pix_id, value, OrderStatus.PAYED, santander_beneciary_john
    )

    transfer_result = transfer_pix(
        api_client, santander_beneciary_john, value, description
    )
    assert transfer_result == {
        "success": True,
        "data": {
            "addedValue": "0.00",
            "beneficiary": beneciary_john_dict_json,
            "debitAccount": {
                "branch": "0001",
                "number": "123456789",
            },
            "deductedValue": "0.00",
            "id": "ASF5Q7Q879WQ",
            "nominalValue": "59.99",
            "obs": "payment mockado",
            "payer": {
                "documentNumber": "20157935000193",
                "documentType": "CPNJ",
                "name": "John Doe SA",
            },
            "paymentValue": "59.99",
            "remittanceInformation": "informação da transferência",
            "status": OrderStatus.PAYED,
            "tags": [],
            "totalValue": "59.99",
            "transaction": {
                "code": "13a654q",
                "date": "2025-01-08T13:44:36Z",
                "endToEnd": "a213e5q564as456f4as56f",
                "value": "59.99",
            },
            "workspaceId": "3870ba5d-d58e-4182-992f-454e5d0e08e2",
        },
        "error": "",
    }
    assert mock_create.call_count == 1
    assert mock_status.call_count == 1
    assert mock_confirm.call_count == 1


def test_transfer_pix_payment_lazy_status_update(
    api_client: SantanderApiClient, mock_api
):
    pix_id = "12345"
    value = Decimal("130000.00")
    description = "Pagamento Teste"
    pix_key = "12345678909"

    mock_create = mock_create_pix_endpoint(
        mock_api, pix_id, value, OrderStatus.PENDING_VALIDATION, pix_key, "CPF"
    )
    mock_confirm = mock_confirm_pix_endpoint(
        mock_api, pix_id, value, OrderStatus.PAYED, pix_key, "CPF"
    )
    mock_status = mock_api.get(
        f"{PIX_ENDPOINT_WITH_WORKSPACE}/{pix_id}",
        [
            {
                "json": get_dict_payment_pix_response(
                    pix_id, value, OrderStatus.PENDING_VALIDATION, pix_key, "CPF"
                )
            },
            {
                "json": get_dict_payment_pix_response(
                    pix_id, value, OrderStatus.PENDING_VALIDATION, pix_key, "CPF"
                )
            },
            {
                "json": get_dict_payment_pix_response(
                    pix_id, value, OrderStatus.READY_TO_PAY, pix_key, "CPF"
                )
            },
            {
                "json": get_dict_payment_pix_response(
                    pix_id, value, OrderStatus.READY_TO_PAY, pix_key, "CPF"
                )
            },
        ],
    )

    transfer_result = transfer_pix(api_client, pix_key, value, description)
    assert transfer_result == {
        "success": True,
        "data": {
            "addedValue": "0.00",
            "debitAccount": {
                "branch": "0001",
                "number": "123456789",
            },
            "deductedValue": "0.00",
            "dictCode": pix_key,
            "dictCodeType": "CPF",
            "id": pix_id,
            "nominalValue": str(value),
            "obs": "payment mockado",
            "payer": {
                "documentNumber": "20157935000193",
                "documentType": "CPNJ",
                "name": "John Doe SA",
            },
            "paymentValue": str(value),
            "remittanceInformation": "informação da transferência",
            "status": OrderStatus.PAYED,
            "tags": [],
            "totalValue": str(value),
            "transaction": {
                "code": "13a654q",
                "date": "2025-01-08T13:44:36Z",
                "endToEnd": "a213e5q564as456f4as56f",
                "value": str(value),
            },
            "workspaceId": "3870ba5d-d58e-4182-992f-454e5d0e08e2",
        },
        "error": "",
    }
    assert mock_create.call_count == 1, "Deveria ter chamado a criação do PIX uma vez"
    assert mock_confirm.call_count == 1, (
        "Deveria ter chamado a confirmação do PIX uma vez"
    )
    assert mock_status.call_count == 3, "Deveria ter chamado o status do PIX três vezes"
