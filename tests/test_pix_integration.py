import json
import pytest
from decimal import Decimal

from responses import RequestsMock
import responses
from santander_sdk.api_client.client import SantanderApiClient
from santander_sdk.transfer_flow import (
    MAX_UPDATE_STATUS_AFTER_CONFIRM,
    MAX_UPDATE_STATUS_BEFORE_CONFIRM,
)
from santander_sdk.pix import transfer_pix
from mock.santander_mocker import (
    PIX_ENDPOINT_WITH_WORKSPACE,
    mock_auth_endpoint,
    mock_workspaces_endpoint,
    santander_beneciary_john,
    beneciary_john_dict_json,
    get_dict_payment_pix_response,
    mock_confirm_pix_endpoint,
    mock_create_pix_endpoint,
    mock_pix_status_endpoint,
)
from santander_sdk.types import OrderStatus


@pytest.fixture
def mock_api(mocker, responses: RequestsMock):
    mocker.patch("santander_sdk.transfer_flow.sleep", return_value=None)
    mock_workspaces_endpoint()
    mock_auth_endpoint(responses)
    return responses


def test_transfer_pix_payment_success(mock_api, client_instance):
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
        client_instance, pix_key, value, description, tags=["teste"]
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
    request_body = mock_create.calls[0].request.body
    assert request_body is not None
    assert json.loads(request_body) == {
        "tags": ["teste"],
        "paymentValue": "100.00",
        "remittanceInformation": description,
        "dictCode": pix_key,
        "dictCodeType": "CPF",
    }


def test_transfer_pix_payment_timeout_create(
    client_instance: SantanderApiClient, mock_api
):
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
    transfer_result = transfer_pix(client_instance, pix_key, value, description)

    assert transfer_result == {
        "success": False,
        "error": "Status update timeout after several attempts: Santander - Status update attempt limit reached",
        "data": None,
    }
    assert mock_create.call_count == 1
    assert mock_status.call_count == MAX_UPDATE_STATUS_BEFORE_CONFIRM


def test_transfer_pix_payment_timeout_before_authorize(
    client_instance: SantanderApiClient, mock_api
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

    transfer_result = transfer_pix(client_instance, pix_key, value, description)
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
    assert mock_status.call_count == MAX_UPDATE_STATUS_AFTER_CONFIRM


def test_transfer_pix_payment_rejected_on_create(
    client_instance: SantanderApiClient, mock_api
):
    pix_id = "QASF4568E48Q"
    value = Decimal("100.00")
    description = "Pagamento Teste"
    pix_key = "12345678909"

    mock_create = mock_create_pix_endpoint(
        mock_api, pix_id, value, OrderStatus.REJECTED, pix_key, "CPF"
    )

    transfer_result = transfer_pix(client_instance, pix_key, value, description)
    assert transfer_result == {
        "success": False,
        "error": "Payment rejection: Santander - Payment rejected by the bank at step CREATE - Reason not returned by Santander",
        "data": None,
    }
    assert mock_create.call_count == 1


def test_transfer_pix_payment_rejected_on_confirm(
    client_instance: SantanderApiClient, mock_api
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

    transfer_result = transfer_pix(client_instance, pix_key, value, description)
    assert transfer_result == {
        "success": False,
        "error": "Payment rejection: Santander - Payment rejected by the bank at step CONFIRM - Reason not returned by Santander",
        "data": None,
    }
    assert mock_create.call_count == 1
    assert mock_confirm.call_count == 1


def test_transfer_pix_payment_with_beneficiary(
    client_instance: SantanderApiClient, mock_api
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
        client_instance, santander_beneciary_john, value, description
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
    client_instance: SantanderApiClient, mock_api
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

    mock_status_pending = mock_api.add(
        responses.GET,
        f"{PIX_ENDPOINT_WITH_WORKSPACE}/{pix_id}",
        json=get_dict_payment_pix_response(
            pix_id, value, OrderStatus.PENDING_VALIDATION, pix_key, "CPF"
        ),
    )
    mock_status_ready = mock_api.add(
        responses.GET,
        f"{PIX_ENDPOINT_WITH_WORKSPACE}/{pix_id}",
        json=get_dict_payment_pix_response(
            pix_id, value, OrderStatus.READY_TO_PAY, pix_key, "CPF"
        ),
    )
    transfer_result = transfer_pix(client_instance, pix_key, value, description)
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
    assert mock_create.call_count == 1
    assert mock_confirm.call_count == 1
    assert mock_status_pending.call_count == 1
    assert mock_status_ready.call_count == 1
