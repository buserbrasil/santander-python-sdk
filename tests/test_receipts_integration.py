from re import compile as regex

import pytest
from santander_sdk.payment_receipts import (
    payment_list,
    create_receipt,
    get_receipt,
    receipt_creation_history,
)
from santander_sdk.typing.receipts_types import ListPaymentParams, ReceiptStatus
from tests.mock.santander_mocker import (
    BASE_URL_RECEIPTS,
    mock_auth_endpoint,
    receipt_response_dict,
    receipt_history_response_dict,
)


@pytest.fixture(autouse=True)
def mock_auth(responses):
    mock_auth_endpoint(responses)


def test_create_receipt(client_instance, responses):
    payment_id = "VXB123456789ABCFEF"
    receipt_request_id = "123456-e691-42d0-b659-1234657899"
    responses.add(
        responses.POST,
        regex(f".+/{payment_id}/file_requests"),
        json=receipt_response_dict(receipt_request_id, receipt_location=None),
    )

    receipt = create_receipt(client_instance, payment_id)

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
                "statusInfo": {"statusCode": ReceiptStatus.REQUESTED},
                "audit": {"creationDateTime": None},
            },
        },
        "location": None,
        "payment_id": payment_id,
        "receipt_request_id": "123456-e691-42d0-b659-1234657899",
        "status": ReceiptStatus.REQUESTED,
    }


def test_create_receipt_already_requested(client_instance, responses):
    payment_id = "VXB123456789ABCFEF"
    receipt_request_id = "123456-e691-42d0-b659-1234657899"
    create_response = responses.add(
        responses.POST,
        regex(f".+/{payment_id}/file_requests"),
        status=400,
        json={
            "errors": [
                {
                    "code": "006",
                    "message": "A receipt is already available for this request.",
                    "traceId": "12345-0251-4bef-833c-qas123356",
                }
            ],
        },
    )
    history_response = responses.add(
        responses.GET,
        regex(f".+/{payment_id}/file_requests$"),
        status=200,
        json=receipt_history_response_dict(receipt_request_id, ReceiptStatus.REQUESTED),
    )
    consult_receipt_response = responses.add(
        responses.GET,
        regex(f".+/file_requests/{receipt_request_id}"),
        status=200,
        json=receipt_response_dict(receipt_request_id, ReceiptStatus.REQUESTED),
    )

    receipt = create_receipt(client_instance, payment_id)

    assert receipt == {
        "data": {
            "request": {
                "requestId": receipt_request_id,
                "creationDateTime": "2025-03-07T12:32:38-03:00",
            },
            "file": {
                "fileRepository": {"location": None},
                "mimeType": "application/pdf",
                "expirationDate": None,
                "statusInfo": {"statusCode": ReceiptStatus.REQUESTED},
                "audit": {"creationDateTime": None},
            },
        },
        "location": None,
        "payment_id": payment_id,
        "receipt_request_id": receipt_request_id,
        "status": ReceiptStatus.REQUESTED,
    }
    assert create_response.call_count == 1
    assert history_response.call_count == 1
    assert consult_receipt_response.call_count == 1


def test_create_receipt_already_requested_expunged(client_instance, responses):
    """
    This test covers the scenario where a receipt creation request fails,
    the history is checked, the receipt is consulted, and a new receipt request is created.
    """
    payment_id = "ERRB123456789ABCFEF"
    expunged_receipt_id = "66111-e691-42d0-b659-1234657899"
    new_receipt_id = "945466-AE65-366569-b65q-99999999"

    create_receipt_error_response = responses.add(
        responses.POST,
        regex(f".+/{payment_id}/file_requests"),
        status=400,
        json={
            "errors": [
                {
                    "code": "006",
                    "message": "A receipt is already available for this request.",
                    "traceId": "12345-0251-4bef-833c-qas123356",
                }
            ],
        },
    )

    receipt_history_response = responses.add(
        responses.GET,
        regex(f".+/{payment_id}/file_requests$"),
        status=200,
        json=receipt_history_response_dict(expunged_receipt_id, ReceiptStatus.EXPUNGED),
    )

    receipt_consult_response = responses.add(
        responses.GET,
        regex(f".+/file_requests/{expunged_receipt_id}"),
        status=200,
        json=receipt_response_dict(
            expunged_receipt_id, ReceiptStatus.EXPUNGED, receipt_location=None
        ),
    )

    new_receipt_request_response = responses.add(
        responses.POST,
        regex(f".+/{payment_id}/file_requests"),
        status=200,
        json=receipt_response_dict(new_receipt_id, ReceiptStatus.REQUESTED),
    )

    receipt = create_receipt(client_instance, payment_id)

    assert receipt == {
        "data": {
            "request": {
                "requestId": new_receipt_id,
                "creationDateTime": "2025-03-07T12:32:38-03:00",
            },
            "file": {
                "fileRepository": {"location": None},
                "mimeType": "application/pdf",
                "expirationDate": None,
                "statusInfo": {"statusCode": ReceiptStatus.REQUESTED},
                "audit": {"creationDateTime": None},
            },
        },
        "location": None,
        "payment_id": payment_id,
        "receipt_request_id": new_receipt_id,
        "status": ReceiptStatus.REQUESTED,
    }
    assert create_receipt_error_response.call_count == 1
    assert receipt_history_response.call_count == 1
    assert receipt_consult_response.call_count == 1
    assert new_receipt_request_response.call_count == 1


def test_get_receipt(client_instance, responses):
    payment_id = "VXB123456789ABCFEF"
    receipt_request_id = "123456-e691-42d0-b659-1234657899"

    consult_receipt_dict = receipt_response_dict(
        receipt_request_id,
        ReceiptStatus.AVAILABLE,
        receipt_location=f"{BASE_URL_RECEIPTS}/files/receipt.pdf",
    )
    consult_receipt_response = responses.add(
        responses.GET,
        regex(f".+/file_requests/{receipt_request_id}"),
        status=200,
        json=consult_receipt_dict,
    )
    receipt = get_receipt(client_instance, payment_id, receipt_request_id)
    assert receipt == {
        "data": {
            "request": {
                "requestId": receipt_request_id,
                "creationDateTime": "2025-03-07T12:32:38-03:00",
            },
            "file": {
                "fileRepository": {
                    "location": f"{BASE_URL_RECEIPTS}/files/receipt.pdf"
                },
                "mimeType": "application/pdf",
                "expirationDate": "2025-04-07T12:32:38-03:00",
                "statusInfo": {"statusCode": ReceiptStatus.AVAILABLE},
                "audit": {"creationDateTime": "2025-03-07T12:32:38-03:00"},
            },
        },
        "location": f"{BASE_URL_RECEIPTS}/files/receipt.pdf",
        "payment_id": payment_id,
        "receipt_request_id": receipt_request_id,
        "status": ReceiptStatus.AVAILABLE,
    }
    assert consult_receipt_response.call_count == 1


def test_receipt_creation_history(client_instance, responses):
    payment_id = "VXB123456789ABCFEF"
    receipt_history_response = responses.add(
        responses.GET,
        regex(f".+/{payment_id}/file_requests$"),
        status=200,
        json={
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
                        "statusInfo": {"statusCode": ReceiptStatus.REQUESTED},
                        "audit": {"creationDateTime": None},
                    },
                }
            ],
            "links": {
                "_first": {"href": f"{BASE_URL_RECEIPTS}?_offset=0&_limit=10"},
                "_prev": None,
                "_next": None,
            },
        },
    )
    history = receipt_creation_history(client_instance, payment_id)

    assert receipt_history_response.call_count == 1
    assert len(history["paymentReceiptsFileRequests"]) == 1
    assert history["paymentReceiptsFileRequests"][0] == {
        "request": {
            "requestId": "123456-e691-42d0-b659-1234657899",
            "creationDateTime": "2025-03-07T12:32:38-03:00",
        },
        "file": {
            "fileRepository": {"location": None},
            "mimeType": "application/pdf",
            "expirationDate": None,
            "statusInfo": {"statusCode": ReceiptStatus.REQUESTED},
            "audit": {"creationDateTime": None},
        },
    }


def test_payment_list(client_instance, responses):
    """Test payment list with pagination."""
    receipt_history_response = responses.add(
        responses.GET,
        regex(".+/consult_payment_receipts/v1/payment_receipts"),
        status=200,
        json={
            "paymentsReceipts": [
                {
                    "payment": {
                        "paymentId": f"VXB123456789ABCFEF{i}",
                        "payer": "Test Payer",
                        "payee": {"name": "STARK BANK S.A."},
                        "paymentAmountInfo": {"direct": {"amount": "10.00"}},
                        "requestValueDate": "2025-02-07T17:26:57-03:00",
                    },
                    "category": {"code": "BOLETOS"},
                    "channel": {"code": "GATEWAY DE PAGAMENTOS - VX"},
                }
                for i in range(1, 11)
            ],
            "links": {
                "_first": {"href": f"{BASE_URL_RECEIPTS}?_offset=0&_limit=100"},
                "_prev": None,
                "_next": None,
            },
        },
    )

    result = payment_list(
        client_instance,
        ListPaymentParams(start_date="2025-01-01", end_date="2025-01-31"),
    )
    assert receipt_history_response.call_count == 1
    assert len(result) == 10
    assert result[0] == {
        "payment": {
            "paymentId": "VXB123456789ABCFEF1",
            "payer": "Test Payer",
            "payee": {"name": "STARK BANK S.A."},
            "paymentAmountInfo": {"direct": {"amount": "10.00"}},
            "requestValueDate": "2025-02-07T17:26:57-03:00",
        },
        "category": {"code": "BOLETOS"},
        "channel": {"code": "GATEWAY DE PAGAMENTOS - VX"},
    }
    assert result[-1]["payment"]["paymentId"] == "VXB123456789ABCFEF10"
