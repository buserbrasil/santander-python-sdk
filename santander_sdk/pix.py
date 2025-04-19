from decimal import Decimal as D
import logging
from typing import cast

from santander_sdk.api_client.client import SantanderApiClient
from santander_sdk.api_client.exceptions import (
    SantanderValueError,
)

from santander_sdk.api_client.helpers import (
    get_pix_key_type,
    truncate_value,
)
from santander_sdk.transfer_flow import SantanderPaymentFlow
from santander_sdk.types import (
    SantanderBeneficiary,
    SantanderPixResponse,
    TransferPixResult,
)

logger = logging.getLogger("santanderLogger")
PIX_ENDPOINT = "/management_payments_partners/v1/workspaces/:workspaceid/pix_payments"


def transfer_pix(
    client: SantanderApiClient,
    pix_key: str | SantanderBeneficiary,
    value: D,
    description: str,
    tags: list[str] = [],
) -> TransferPixResult:
    id = ""
    try:
        if value is None or value <= 0:
            raise SantanderValueError(f"Invalid value for PIX transfer: {value}")

        flow = SantanderPaymentFlow(client, PIX_ENDPOINT, logger)
        data = _data_dict(pix_key, value, description, tags)
        create_pix_response = flow.create_payment(data)
        id = create_pix_response["id"]
        if not id:
            raise SantanderValueError(
                f"Response without id. Response: {create_pix_response}"
            )

        flow.ensure_ready_to_pay(create_pix_response)

        confirm_response = flow.confirm_payment(
            {
                "status": "AUTHORIZED",
                "paymentValue": truncate_value(value),
            },
            id,
        )
        return {"success": True, "id": id, "data": confirm_response, "error": ""}
    except Exception as e:
        logger.error(str(e))
        return {"success": False, "id": id, "data": None, "error": str(e)}


def get_transfer(
    client: SantanderApiClient, pix_payment_id: str
) -> SantanderPixResponse:
    if not pix_payment_id:
        raise SantanderValueError("pix_payment_id not provided")
    response = client.get(f"{PIX_ENDPOINT}/{pix_payment_id}")
    return cast(SantanderPixResponse, response)


def _data_dict(
    pix_key: SantanderBeneficiary | str,
    value: D,
    description: str,
    tags: list = [],
) -> dict:
    data = {
        "tags": tags,
        "paymentValue": truncate_value(value),
        "remittanceInformation": description,
    }
    if isinstance(pix_key, str):
        pix_type = get_pix_key_type(pix_key)
        data.update({"dictCode": pix_key, "dictCodeType": pix_type})
        return data

    if isinstance(pix_key, dict):
        beneficiary = cast(dict, pix_key.copy())
        if beneficiary.get("bankCode") is None and beneficiary.get("ispb") is None:
            raise SantanderValueError("Either 'bankCode' or 'ispb' must be provided")
        if beneficiary.get("bankCode") and beneficiary.get("ispb"):
            beneficiary.pop("ispb")
            data.update({"beneficiary": beneficiary})
        return data

    raise SantanderValueError("PIX key or Beneficiary not provided")
