import pytest
from unittest.mock import patch
from santander_sdk.api_client.exceptions import SantanderRequestError
from santander_sdk.payment_receipts import (
    payment_list,
    payment_list_iter_by_pages,
    create_receipt,
    get_receipt,
    receipt_creation_history,
)
from santander_sdk.typing.receipts_types import ListPaymentParams, ReceiptStatus
from tests.mock.santander_mocker import BASE_URL_RECEIPTS, receipt_response_dict


@pytest.fixture
def mock_client():
    with patch("santander_sdk.payment_receipts.SantanderApiClient") as mock:
        yield mock


@pytest.fixture
def sdk_with_payments_result(mock_client):
    mock_client.return_value.get.return_value = {
        "paymentsReceipts": [
            {
                "payment": {
                    "paymentId": "VXB123456789ABCFEF",
                    "payer": "not Import for tests",
                    "payee": {"name": "STARK BANK S.A."},
                    "paymentAmountInfo": {"direct": {"amount": "10.00"}},
                    "requestValueDate": "2025-02-07T17:26:57-03:00",
                },
                "category": {"code": "BOLETOS"},
                "channel": {"code": "GATEWAY DE PAGAMENTOS - VX"},
            }
        ],
        "links": {
            "_first": {"href": f"{BASE_URL_RECEIPTS}?_offset=0&_limit=10"},
            "_prev": None,
            "_next": None,
        },
    }
    return mock_client.return_value


@pytest.fixture
def sdk_with_create_receipt_result(mock_client):
    mock_client.return_value.post.return_value = receipt_response_dict(
        "123456-e691-42d0-b659-1234657899", ReceiptStatus.REQUESTED
    )
    return mock_client.return_value


@pytest.fixture
def sdk_with_get_receipt_result(mock_client):
    mock_client.return_value.get.return_value = receipt_response_dict(
        "123456-e691-42d0-b659-1234657899",
        ReceiptStatus.AVAILABLE,
        receipt_location="https://api.santander.com.br/files/receipt.pdf",
    )
    return mock_client.return_value


@pytest.fixture
def sdk_with_file_history_result(mock_client):
    mock_client.return_value.get.return_value = {
        "paymentReceiptsFileRequests": [
            receipt_response_dict("123456-e691-42d0-b659-1234657899")
        ],
        "links": {
            "_first": {"href": f"{BASE_URL_RECEIPTS}?_offset=0&_limit=10"},
            "_prev": None,
            "_next": None,
        },
    }
    return mock_client.return_value


def test_payment_list(sdk_with_payments_result):
    params = ListPaymentParams(start_date="2025-01-01", end_date="2025-01-31")
    payments = payment_list(sdk_with_payments_result, params)
    assert len(payments) == 1
    assert payments[0]["payment"]["paymentId"] == "VXB123456789ABCFEF"
    sdk_with_payments_result.get.assert_called_once_with(
        "/consult_payment_receipts/v1/payment_receipts", params=params
    )


def test_create_receipt(sdk_with_create_receipt_result):
    payment_id = "VXB123456789ABCFEF"

    receipt = create_receipt(sdk_with_create_receipt_result, payment_id)
    assert receipt == {
        "data": {
            "request": {
                "requestId": "123456-e691-42d0-b659-1234657899",
                "creationDateTime": "2025-03-07T12:32:38-03:00",
            },
            "file": {
                "fileRepository": {"location": None},
                "mimeType": "application/pdf",
                "expirationDate": None,
                "statusInfo": {"statusCode": "REQUESTED"},
                "audit": {"creationDateTime": None},
            },
        },
        "payment_id": payment_id,
        "receipt_request_id": "123456-e691-42d0-b659-1234657899",
        "status": "REQUESTED",
        "location": None,
    }


def test_get_receipt(sdk_with_get_receipt_result):
    payment_id = "VXB123456789ABCFEF"
    receipt_request_id = "123456-e691-42d0-b659-1234657899"

    receipt = get_receipt(sdk_with_get_receipt_result, payment_id, receipt_request_id)

    assert receipt == {
        "data": {
            "request": {
                "requestId": "123456-e691-42d0-b659-1234657899",
                "creationDateTime": "2025-03-07T12:32:38-03:00",
            },
            "file": {
                "fileRepository": {
                    "location": "https://api.santander.com.br/files/receipt.pdf"
                },
                "mimeType": "application/pdf",
                "expirationDate": "2025-04-07T12:32:38-03:00",
                "statusInfo": {"statusCode": "AVAILABLE"},
                "audit": {"creationDateTime": "2025-03-07T12:32:38-03:00"},
            },
        },
        "payment_id": payment_id,
        "receipt_request_id": "123456-e691-42d0-b659-1234657899",
        "status": "AVAILABLE",
        "location": "https://api.santander.com.br/files/receipt.pdf",
    }


def test_receipt_creation_history(sdk_with_file_history_result):
    payment_id = "VXB123456789ABCFEF"
    history = receipt_creation_history(sdk_with_file_history_result, payment_id)
    assert history == {
        "paymentReceiptsFileRequests": [
            {
                "request": {
                    "requestId": "123456-e691-42d0-b659-1234657899",
                    "creationDateTime": "2025-03-07T12:32:38-03:00",
                },
                "file": {
                    "fileRepository": {"location": None},
                    "mimeType": "application/pdf",
                    "expirationDate": None,
                    "statusInfo": {"statusCode": "REQUESTED"},
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


def test_payment_list_iter_by_pages(mock_client):
    mock_client_instance = mock_client.return_value
    mock_client_instance.get.side_effect = [
        {
            "paymentsReceipts": [
                {
                    "payment": {
                        "paymentId": f"VXB123456789ABCFEF{i}",
                        "payer": "Test Payer",
                        "payee": {"name": "STARK BANK S.A."},
                        "paymentAmountInfo": {"direct": {"amount": f"1{i}.00"}},
                        "requestValueDate": "2025-02-07T17:26:57-03:00",
                    },
                    "category": {"code": "BOLETOS"},
                    "channel": {"code": "GATEWAY DE PAGAMENTOS - VX"},
                }
            ],
            "links": {
                "_first": {"href": f"{BASE_URL_RECEIPTS}?_offset=0&_limit=1"},
                "_prev": {"href": f"{BASE_URL_RECEIPTS}?_offset={i}&_limit=1"}
                if i == 0
                else None,
                "_next": {"href": f"{BASE_URL_RECEIPTS}?_offset={i}&_limit=1"}
                if i < 4
                else None,
            },
        }
        for i in range(0, 5)
    ]
    params = ListPaymentParams(
        start_date="2025-01-01", end_date="2025-01-31", _limit="1"
    )

    for i, page in enumerate(payment_list_iter_by_pages(mock_client_instance, params)):
        payment = page["paymentsReceipts"][0]["payment"]
        assert payment["paymentId"] == f"VXB123456789ABCFEF{i}"
        assert payment["paymentAmountInfo"]["direct"]["amount"] == f"1{i}.00"
    assert mock_client_instance.get.call_count == 5


@patch("santander_sdk.payment_receipts._handle_already_created", return_value="called")
def test_create_receipt_already_requested(mock_handle_already_created, mock_client):
    client_instance = mock_client.return_value
    expected_exception = SantanderRequestError(
        message="Failied",
        status_code=400,
        content={
            "errors": [
                {
                    "code": "006",
                    "message": "Já existe comprovante disponível para esta solicitação.",
                    "traceId": "12345-0251-4bef-833c-qas123356",
                }
            ]
        },
    )
    client_instance.post.side_effect = expected_exception
    payment_id = "VXB123456789ABCFEF"
    create_receipt(client_instance, payment_id)
    mock_handle_already_created.assert_called_once_with(
        client_instance, payment_id, expected_exception
    )
