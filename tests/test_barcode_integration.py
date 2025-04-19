""" Some inicial data to start tests and mocks"""

from santander_sdk.barcode_payment import pay_barcode
from santander_sdk.types import OrderStatus
from tests.mock.santander_mocker import barcode_response_dict, mock_barcode_response
from decimal import Decimal as D

BARCODE_TEST = "8464000000028735002403040150349033427080404014"
TEST_ID = "6c016190-0ab9-4c12-931f-8d6fbf0fd9ab"
    
def test_transfer_boleto_payment_success(client_instance, responses, mock_auth):
    
    json_create = barcode_response_dict(TEST_ID, BARCODE_TEST, OrderStatus.READY_TO_PAY)
    mock_create = mock_barcode_response(responses, json_create, "CREATE")
    
    json_status = barcode_response_dict(TEST_ID, BARCODE_TEST, OrderStatus.PAYED)
    mock_status = mock_barcode_response(responses, json_status, "STATUS")
    
    json_confirm = barcode_response_dict(TEST_ID, BARCODE_TEST, OrderStatus.PENDING_CONFIRMATION)
    mock_confirm = mock_barcode_response(responses, json_confirm, "CONFIRM")
  
    result = pay_barcode(client_instance, BARCODE_TEST, D("200.15"), "2025-01-17", ["tag1", "tag2"])
    
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
        "totalValue": '200.15',
        "concessionary": {"code": 48, "name": "AES ELETROPAULO"},
        "transaction": {
            "value": '200.15',
            "code": "VX43C02501171347300469",
            "date": "2025-01-17T16:47:30Z",
        },
        "paymentValue": '200.15',
        "tags": ["tag1", "tag2"],
    }
    
def test_transfer_boleto_payment_long_success_scenario(client_instance, responses, mock_auth):
    json_create = barcode_response_dict(TEST_ID, BARCODE_TEST, OrderStatus.PENDING_VALIDATION)
    mock_create = mock_barcode_response(responses, json_create, "CREATE")
    
    json_status = barcode_response_dict(TEST_ID, BARCODE_TEST, OrderStatus.READY_TO_PAY)
    mock_status = mock_barcode_response(responses, json_status, "STATUS")
    
    json_confirm = barcode_response_dict(TEST_ID, BARCODE_TEST, OrderStatus.PENDING_CONFIRMATION)
    mock_confirm = mock_barcode_response(responses, json_confirm, "CONFIRM")
  
    json_status = barcode_response_dict(TEST_ID, BARCODE_TEST, OrderStatus.PAYED)
    mock_status_lazy = mock_barcode_response(responses, json_status, "STATUS")
    
    result = pay_barcode(client_instance, BARCODE_TEST, D("200.15"), "2025-01-17", ["tag1", "tag2"])
    
    assert result["success"] is True
    assert mock_confirm.call_count == 1
    assert mock_create.call_count == 1
    assert mock_status.call_count == 1
    assert mock_status_lazy.call_count == 1
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
        "totalValue": '200.15',
        "concessionary": {"code": 48, "name": "AES ELETROPAULO"},
        "transaction": {
            "value": '200.15',
            "code": "VX43C02501171347300469",
            "date": "2025-01-17T16:47:30Z",
        },
        "paymentValue": '200.15',
        "tags": ["tag1", "tag2"],
    }


# def test_transfer_boleto_arrecadacao_payment_success(mock_api):
#     boleto_numero="846400000002873500240304015034903342708040401400"

#     assert transfer_result["success"] is True
#     assert transfer_result["data"] == {
#         "id": "6c016190-0ab9-4c12-931f-8d6fbf0fd9ab",
#         "workspaceId": "85841a74-ca1e-46e5-b75f-66074a679e04",
#         "code": "8464000000028735002403040150349033427080404014",
#         "concessionary": {"code": 48, "name": "AES ELETROPAULO"},
#         "debitAccount": {"branch": "1", "number": "100022349"},
#         "status": "PAYED",
#         "rejectReason": None,
#         "paymentType": "TAXES",
#         "accountingDate": "2025-01-17",
#         "finalPayer": {
#             "name": "JAJA PENUMPER ALFA LTDA",
#             "documentType": "CNPJ",
#             "documentNumber": "63918424000150",
#         },
#         "totalValue": 200.15,
#         "transaction": {
#             "value": 200.15,
#             "code": "VX43C02501171347300469",
#             "date": "2025-01-17T16:47:30Z",
#         },
#         "paymentValue": 2500.0,
#         "tags": ["tag1", "tag2"],
#     }

# def test_transfer_boleto_payment_rejected(mock_api):
#     boleto_numero="8464000000028735002403040150349033427080404014"
#     assert response["success"] is False
#     assert (
#         response["error"]
#         == "Rejeição de pagamento: Santander - Pagamento BOLETO rejeitado pelo banco - Motivo não retornado pelo Santander"
#     )
#     assert mock_create.call_count == 1
