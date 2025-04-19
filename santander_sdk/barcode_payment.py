from datetime import date, datetime
from decimal import Decimal as D
import logging
from typing import Literal, cast

from santander_sdk import (
    SantanderApiClient,
    SantanderValueError,
    truncate_value,
    today,
)
from santander_sdk.api_client.helpers import to_iso_date_string
from santander_sdk.transfer_flow import SantanderPaymentFlow
from santander_sdk.types import SantanderPixResponse, TransferPixResult

SantanderBoletoResponse = SantanderPixResponse
TransferBoletoReponse = TransferPixResult

logger = logging.getLogger("__name__")

BASE_ENDPOINT = "/management_payments_partners/v1/workspaces/:workspaceid"
BANKSLIP_ENDPOINT = f"{BASE_ENDPOINT}/bank_slip_payments"
BARCODE_ENDPOINT = f"{BASE_ENDPOINT}/barcode_payments"

BarCodeType = Literal["barcode", "bankslip"]


def pay_barcode(
    client: SantanderApiClient,
    barcode: str,
    value: D,
    payment_date: str | date,
    tags: list[str] = [],
) -> TransferBoletoReponse:
    payment_id = ""
    try:
        flow = SantanderPaymentFlow(client, _resolve_endpoint(barcode), logger)
        create_response = flow.create_payment(
            {
                "code": barcode,
                "tags": tags,
                "paymentData": to_iso_date_string(payment_date),
            }
        )
        payment_id = create_response["id"]
        flow.ensure_ready_to_pay(create_response)

        confirm_response = flow.confirm_payment(
            {
                "status": "AUTHORIZED",
                "paymentValue": truncate_value(value),
                "debitAccount": create_response["debitAccount"],
                "finalPayer": create_response["finalPayer"],
            },
            payment_id,
        )
        return {
            "success": True,
            "id": payment_id,
            "data": confirm_response,
            "error": "",
        }
    except Exception as e:
        logger.exception(str(e))
        return {"success": False, "id": payment_id, "error": str(e), "data": None}


def get_barcode_status(
    client: SantanderApiClient, payment_id: str, barCodeType: BarCodeType
) -> SantanderBoletoResponse:
    if not payment_id:
        raise SantanderValueError("pix_payment_id not provided")
    endpoint = (
        BANKSLIP_ENDPOINT if barCodeType == BarCodeType.barcode else BARCODE_ENDPOINT
    )
    response = client.get(f"{endpoint}/{payment_id}")
    return cast(SantanderBoletoResponse, response)


def _resolve_endpoint(barcode: str) -> str:
    # precisa melhorar
    return BANKSLIP_ENDPOINT if len(barcode) < 40 else BARCODE_ENDPOINT
