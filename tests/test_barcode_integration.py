"""Some inicial data to start tests and mocks"""

import pytest
from santander_sdk.barcode_payment import pay_barcode
from tests.mock.santander_mocker import barcode_response_dict, mock_barcode_response
from decimal import Decimal as D

BARCODE_TEST = "8464000000028735002403040150349033427080404014"
TEST_ID = "6c016190-0ab9-4c12-931f-8d6fbf0fd9ab"


@pytest.mark.usefixtures("mock_auth")
def test_transfer_boleto_paymenat_success(client_instance, responses):
    json_create = barcode_response_dict(TEST_ID, BARCODE_TEST, "READY_TO_PAY")
    mock_create = mock_barcode_response(responses, json_create, "CREATE")

    json_status = barcode_response_dict(TEST_ID, BARCODE_TEST, "PAYED")
    mock_status = mock_barcode_response(responses, json_status, "STATUS")

    json_confirm = barcode_response_dict(TEST_ID, BARCODE_TEST, "PENDING_CONFIRMATION")
    mock_confirm = mock_barcode_response(responses, json_confirm, "CONFIRM")

    result = pay_barcode(
        client_instance, BARCODE_TEST, D("200.15"), "2025-01-17", ["tag1", "tag2"]
    )

    assert result["success"] is True
    assert mock_confirm.call_count == 1
    assert mock_create.call_count == 1
    assert mock_status.call_count == 1

    assert result["data"] == {
        "id": "6c016190-0ab9-4c12-931f-8d6fbf0fd9ab",
        "workspaceId": "8e33d56c-204f-461e-aebe-08baaab6479e",
        "code": "8464000000028735002403040150349033427080404014",
        "debitAccount": {"branch": "1", "number": "100022349"},
        "status": "PAYED",
        "rejectReason": None,
        "paymentType": "TAXES",
        "accountingDate": "2025-01-17",
        "finalPayer": {
            "name": "JAJA PENUMPER ALFA LTDA",
            "documentType": "CNPJ",
            "documentNumber": "63918424000150",
        },
        "totalValue": "200.15",
        "concessionary": {"code": 48, "name": "AES ELETROPAULO"},
        "transaction": {
            "value": "200.15",
            "code": "VX43C02501171347300469",
            "date": "2025-01-17T16:47:30Z",
        },
        "paymentValue": "200.15",
        "tags": ["tag1", "tag2"],
    }


# need more tests here
