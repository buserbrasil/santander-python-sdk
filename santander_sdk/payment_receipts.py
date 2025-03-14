"""
First of all, you need to know the process of obtaining the receipt consists of two or three steps:

1 - List Payments: Obtain the payment transaction ID to make the receipt creation request
    (Optional unless you already have the transaction ID).
2 - Create Receipt: Request a receipt creation: the payment transaction ID is required and
    the receipt request ID is returned.
3 - Get Receipt: Obtain the receipt with the transaction ID and the receipt request ID.

Steps and functions to help you handle this:

1) List Payments (With support of filters and handle pages)
    - payment_list: Abstract and handles all pages and returns full results.
    - payment_list_iter_by_pages: Abstract and returns an iterator with each page of results.

2) Create Receipt (with support for handling already requested receipts)
    - create_receipt: Creates a receipt request. This step also tries
      to handle the case when the receipt was already requested by
      retrying the request from history and getting the last request
      to help generate the receipt.

3) Get Receipt
    - get_receipt: Gets the receipt information to download the file.
      We just simplify the most important fields and embed the full response.

Useful functions:

- Receipt Creation History (receipt_creation_history)
    Lists the history of receipt creation requests. This is needed when
    you have already requested a receipt.
    The creation request uses this to try to handle the case when the
    receipt was already requested.

Typing and abstractions:
    We tried to keep the typing as close as possible to the Santander API.
    To make all possibilities as the API can handle,
    we did some abstractions to make the usage easier, like
    returning the most important fields in the response and embedding
    the full response if it's needed for you.

Check out more in the documentation:
https://developer.santander.com.br/api/documentacao/comprovantes-visao-geral/
"""

import logging
from time import sleep
from typing import Generator, List, cast
from santander_sdk.api_client.client import SantanderApiClient
from santander_sdk.api_client.exceptions import (
    SantanderRequestError,
    SantanderValueError,
)
from santander_sdk.typing.receipts_types import (
    ALREADY_REQUESTED_RECEIPT,
    ReceiptInfoResponse,
    PaymentReceipts,
    ListPaymentParams,
    ListPaymentsResponse,
    ReceiptInfoResult,
    ReceiptStatus,
    ReceiptCreationHistoryResponse,
)

RECEIPTS_ENDPOINT = "/consult_payment_receipts/v1/payment_receipts"

logger = logging.getLogger(__name__)


def payment_list(
    client: SantanderApiClient, params: ListPaymentParams
) -> List[PaymentReceipts]:
    """List all payments by filters. Returns all pages of results.
    - See ListPaymentsParams for available filters.
    """
    responses = payment_list_iter_by_pages(client, params)
    payments = []
    for response in responses:
        payments += response["paymentsReceipts"]
    return payments


def payment_list_iter_by_pages(
    client: SantanderApiClient, params: ListPaymentParams
) -> Generator[ListPaymentsResponse, None, None]:
    """Paginated version of list_payments. Each iteration returns a page of results."""
    response = _payment_list_request(client, params)
    yield response
    while "_next" in response.get("links", {}):
        try:
            next_link = response["links"].get("_next")
            if not next_link or not next_link.get("href"):
                break
            next_offset = next_link["href"].split("_offset=")[1].split("&")[0]
            params["_offset"] = next_offset
            response = _payment_list_request(client, params)
            yield response
        except KeyError as e:
            raise Exception(f"Expected the next page, but not found: {e}")


def create_receipt(
    client: SantanderApiClient, payment_id: str, handle_already_created: bool = True
) -> ReceiptInfoResult:
    """Create a payment receipt request.
    You need the request.requestId to get the receipt when it's ready.
    """
    if not payment_id:
        raise SantanderValueError("payment_id is required to create a receipt request.")
    endpoint = f"{RECEIPTS_ENDPOINT}/{payment_id}/file_requests"
    try:
        response = cast(ReceiptInfoResponse, client.post(endpoint, None))
        return _receipt_result(response, payment_id)
    except SantanderRequestError as e:
        if e.status_code == 400 and handle_already_created:
            """if a receipt was already requested the Santander API 
                returns 400 with a code ALREADY_REQUESTED_RECEIPT (006)
            """
            if e.content and any(
                err.get("code") == ALREADY_REQUESTED_RECEIPT
                for err in e.content.get("errors", [])
            ):
                return _handle_already_created(client, payment_id, e)
        raise


def get_receipt(
    client: SantanderApiClient, payment_id: str, receipt_request_id: str
) -> ReceiptInfoResult:
    """Get the payment receipt information to download the file."""
    if not (payment_id and receipt_request_id):
        raise SantanderValueError("payment_id and receipt_request are required")
    endpoint = f"{RECEIPTS_ENDPOINT}/{payment_id}/file_requests/{receipt_request_id}"
    response = cast(ReceiptInfoResponse, client.get(endpoint))
    return _receipt_result(response, payment_id)


def receipt_creation_history(
    client: SantanderApiClient, payment_id: str
) -> ReceiptCreationHistoryResponse:
    """List the history of receipt creation requests."""
    endpoint = f"{RECEIPTS_ENDPOINT}/{payment_id}/file_requests"
    response = client.get(endpoint)
    return cast(ReceiptCreationHistoryResponse, response)


def _payment_list_request(
    client: SantanderApiClient, params: ListPaymentParams
) -> ListPaymentsResponse:
    """List payments by filters.
    Limited to 1000 results per page and 30 days of history.
    """
    if not params.get("_limit"):
        params["_limit"] = "1000"
    response = client.get(RECEIPTS_ENDPOINT, params=cast(dict, params))
    return cast(ListPaymentsResponse, response)


def _handle_already_created(
    client: SantanderApiClient, payment_id: str, error: SantanderRequestError
) -> ReceiptInfoResult:
    """This retrieve the request from history to renew the file.
    After retrieving from history, we need to refresh the status to generate a new one.
    If there is an error, we need to create a new request after getting the receipt.
    This happens when a receipt was requested a long time ago or the previous
    attempt returned an error like EXPUNGED or ERROR.
    """
    logger.info("Receipt already requested. Trying to get the receipt request ID.")
    receipt_history = receipt_creation_history(client, payment_id)
    if not receipt_history["paymentReceiptsFileRequests"]:
        logger.error("No previous receipts in history")
        raise
    last_from_history = receipt_history["paymentReceiptsFileRequests"][-1]
    request_id = last_from_history["request"]["requestId"]
    result = get_receipt(client, payment_id, request_id)
    if result["status"] not in [ReceiptStatus.EXPUNGED, ReceiptStatus.ERROR]:
        return result

    logger.info("The last receipt is in an error state, creating another one.")
    sleep(0.5)
    endpoint = f"{RECEIPTS_ENDPOINT}/{payment_id}/file_requests"
    response = cast(ReceiptInfoResponse, client.post(endpoint, None))
    return _receipt_result(response, payment_id)


def _receipt_result(
    response: ReceiptInfoResponse, payment_id: str
) -> ReceiptInfoResult:
    """Just simplify the most important fields and embed the full response."""
    return ReceiptInfoResult(
        payment_id=payment_id,
        receipt_request_id=response["request"]["requestId"],
        status=response["file"]["statusInfo"]["statusCode"],
        location=response["file"]["fileRepository"].get("location"),
        data=response,
    )
