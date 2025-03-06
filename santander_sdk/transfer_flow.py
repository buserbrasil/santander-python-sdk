import logging
from time import sleep
from typing import List, Literal, cast

from santander_sdk.api_client.client import SantanderApiClient
from santander_sdk.api_client.exceptions import (
    SantanderClientError,
    SantanderRejectedError,
    SantanderRequestError,
    SantanderStatusTimeoutError,
)

from santander_sdk.api_client.helpers import (
    retry_one_time_on_request_exception,
)
from santander_sdk.types import (
    ConfirmOrderStatus,
    CreateOrderStatus,
    OrderStatus,
    OrderStatusType,
    SantanderPixResponse,
)

MAX_UPDATE_STATUS_AFTER_CONFIRM = 120
MAX_UPDATE_STATUS_BEFORE_CONFIRM = 10
UPDATE_STATUS_INTERVAL_TIME = 2


class SantanderPaymentFlow:
    current_step: Literal["CREATE", "CONFIRM"] = "CREATE"

    def __init__(
        self,
        client: SantanderApiClient,
        endpoint: str,
        logger: logging.Logger | None = None,
    ):
        self.client = client
        self.logger = logger or logging.getLogger(__name__)
        self.endpoint = endpoint

    def create_payment(self, data: dict) -> SantanderPixResponse:
        response = cast(
            SantanderPixResponse, self.client.post(self.endpoint, data=data)
        )
        self._check_for_rejected_error(response)
        self.logger.info("Payment created: ", response.get("id"))
        return response

    def ensure_ready_to_pay(self, confirm_data) -> None:
        payment_status = confirm_data.get("status")
        if payment_status != CreateOrderStatus.READY_TO_PAY:
            self.logger.info("PIX is not ready for payment", payment_status)
            self._payment_status_polling(
                payment_id=confirm_data.get("id"),
                until_status=[CreateOrderStatus.READY_TO_PAY],
                max_update_attemps=MAX_UPDATE_STATUS_BEFORE_CONFIRM,
            )

    def confirm_payment(
        self, confirm_data: dict, payment_id: str
    ) -> SantanderPixResponse:
        try:
            confirm_response = self._request_confirm_payment(confirm_data, payment_id)
        except SantanderRequestError as e:
            self.logger.error(str(e), payment_id, "checking current status")
            confirm_response = self._request_payment_status(payment_id)

        if not confirm_response.get("status") == ConfirmOrderStatus.PAYED:
            try:
                confirm_response = self._resolve_lazy_status_payed(
                    payment_id, confirm_response.get("status")
                )
            except SantanderStatusTimeoutError as e:
                self.logger.info("Timeout occurred while updating status:", str(e))
        return confirm_response

    @retry_one_time_on_request_exception
    def _request_payment_status(self, payment_id: str) -> SantanderPixResponse:
        if not payment_id:
            raise ValueError("payment_id not provided")
        response = self.client.get(f"{self.endpoint}/{payment_id}")
        response = cast(SantanderPixResponse, response)
        self._check_for_rejected_error(response)
        return response

    def _request_confirm_payment(
        self, confirm_data: dict, payment_id: str
    ) -> SantanderPixResponse:
        self.current_step = "CONFIRM"
        if not payment_id:
            raise ValueError("payment_id not provided")
        response = self.client.patch(f"{self.endpoint}/{payment_id}", data=confirm_data)
        response = cast(SantanderPixResponse, response)
        self._check_for_rejected_error(response)
        return response

    def _check_for_rejected_error(self, payment_response: SantanderPixResponse):
        if not payment_response.get("status") == OrderStatus.REJECTED:
            return
        reject_reason = payment_response.get(
            "rejectReason", "Reason not returned by Santander"
        )
        raise SantanderRejectedError(
            f"Payment rejected by the bank at step {self.current_step} - {reject_reason}"
        )

    def _resolve_lazy_status_payed(
        self, payment_id: str, current_status: OrderStatusType
    ) -> None:
        if not current_status == ConfirmOrderStatus.PENDING_CONFIRMATION:
            raise SantanderClientError(
                f"Unexpected status after confirmation: {current_status}"
            )
        confirm_response = self._payment_status_polling(
            payment_id=payment_id,
            until_status=[ConfirmOrderStatus.PAYED],
            max_update_attemps=MAX_UPDATE_STATUS_AFTER_CONFIRM,
        )
        return confirm_response

    def _payment_status_polling(
        self, payment_id: str, until_status: List[str], max_update_attemps: int
    ) -> SantanderPixResponse:
        for attempt in range(1, max_update_attemps + 1):
            response = self._request_payment_status(payment_id)
            self.logger.info(
                f"Checking status by polling: {payment_id} - {response.get('status')}"
            )
            if response.get("status") in until_status:
                break
            if attempt == max_update_attemps:
                raise SantanderStatusTimeoutError(
                    "Status update attempt limit reached", self.current_step
                )
            sleep(UPDATE_STATUS_INTERVAL_TIME)

        return response
