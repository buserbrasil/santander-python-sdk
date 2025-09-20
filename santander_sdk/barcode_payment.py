from datetime import date
from decimal import Decimal as D
from typing import Literal, cast

from santander_sdk import SantanderApiClient
from santander_sdk.api_client.exceptions import SantanderClientError
from santander_sdk.api_client.helpers import (
    to_iso_date_string,
    truncate_value,
)
from santander_sdk.transfer_flow import SantanderPaymentFlow
from santander_sdk.types import SantanderResponse, TransferResult

SantanderBoletoResponse = SantanderResponse
TransferBoletoReponse = TransferResult

BASE_ENDPOINT = "/management_payments_partners/v1/workspaces/:workspaceid"
BANKSLIP_ENDPOINT = f"{BASE_ENDPOINT}/bank_slip_payments"  # Boleto bancário
BARCODE_ENDPOINT = f"{BASE_ENDPOINT}/barcode_payments"  # Boleto de arrecadação

BarCodeType = Literal["barcode", "bankslip"]


def pay_barcode(
    client: SantanderApiClient,
    barcode: str,
    value: D,
    payment_date: str | date,
    tags: list[str] = [],
    bar_code_type: BarCodeType = "bankslip",
) -> TransferBoletoReponse:
    payment_id = ""
    flow = SantanderPaymentFlow(client, _resolve_endpoint(bar_code_type))
    try:
        # Step 1: Create the payment
        create_barcode_response = flow.create_payment(
            {
                "code": barcode,
                "tags": tags,
                "paymentData": to_iso_date_string(payment_date),
            }
        )
        payment_id = create_barcode_response.get("id")
        if not payment_id:
            raise SantanderClientError("Payment ID was not returned on creation")
        if create_barcode_response.get("status") is None:
            raise SantanderClientError("Payment status was not returned on creation")

        # Step 2: Ensure the payment is ready to be confirmed
        flow.ensure_ready_to_pay(create_barcode_response)

        # Step 3: Confirm the payment
        confirm_response = flow.confirm_payment(
            {
                "status": "AUTHORIZED",
                "paymentValue": truncate_value(value),
                "debitAccount": create_barcode_response.get("debitAccount"),
                "finalPayer": create_barcode_response.get("finalPayer"),
            },
            payment_id,
        )
        return {
            "success": True,
            "request_id": flow.request_id,
            "data": confirm_response,
            "error": "",
        }
    except Exception as e:
        error_message = str(e)
        client.logger.error(error_message)
        return {
            "success": False,
            "request_id": flow.request_id,
            "error": error_message,
            "data": None,
        }


def get_barcode_status(
    client: SantanderApiClient, payment_id: str, barCodeType: BarCodeType
) -> SantanderBoletoResponse:
    if not payment_id:
        raise ValueError("pix_payment_id not provided")
    endpoint = _resolve_endpoint(barCodeType)
    response = client.get(f"{endpoint}/{payment_id}")
    return cast(SantanderBoletoResponse, response)


def _resolve_endpoint(bar_code_type: BarCodeType) -> str:
    if bar_code_type not in ("bankslip", "barcode"):
        raise ValueError("bar_code_type must be 'bankslip' or 'barcode'")
    if bar_code_type == "bankslip":
        return BANKSLIP_ENDPOINT
    return BARCODE_ENDPOINT
