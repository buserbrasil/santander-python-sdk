import pytest
from decimal import Decimal as D
from unittest.mock import MagicMock, patch

from santander_sdk.api_client.exceptions import (
    SantanderRejectedError,
    SantanderStatusTimeoutError,
)
from santander_sdk.types import OrderStatus
from santander_sdk.transfer_flow import SantanderPaymentFlow
from tests.mock.santander_mocker import get_dict_payment_pix_response

PIX_ENDPOINT = "/management_payments_partners/v1/workspaces/:workspaceid/pix_payments"


@pytest.fixture
def api_client():
    return MagicMock()


@pytest.fixture
def payment_flow(api_client):
    logger = MagicMock()
    return SantanderPaymentFlow(api_client, PIX_ENDPOINT, logger)


@pytest.fixture
def mock_sleep():
    with patch("santander_sdk.transfer_flow.sleep", return_value=None) as mock:
        yield mock


@pytest.fixture
def lazy_status_update(api_client):
    def _lazy_status_update(payment_id, statuses):
        api_client.get.side_effect = [
            get_dict_payment_pix_response(payment_id, D("100.00"), status)
            for status in statuses
        ]

    return _lazy_status_update


def test_create_payment(payment_flow, api_client):
    data = {"paymentValue": "100.00", "remittanceInformation": "Test Payment"}
    response = {"id": "12345", "status": OrderStatus.PENDING_VALIDATION}
    api_client.post.return_value = response

    result = payment_flow.create_payment(data)
    assert result == response
    api_client.post.assert_called_once_with(PIX_ENDPOINT, data=data)


def test_ensure_ready_to_pay(payment_flow, api_client):
    confirm_data = {"id": "12345", "status": OrderStatus.PENDING_VALIDATION}
    api_client.get.return_value = {"id": "12345", "status": OrderStatus.READY_TO_PAY}

    payment_flow.ensure_ready_to_pay(confirm_data)
    api_client.get.assert_called_once_with(f"{PIX_ENDPOINT}/12345")


def test_ensure_ready_to_pay_lazy(payment_flow, api_client, lazy_status_update):
    confirm_data = {"id": "12345", "status": OrderStatus.PENDING_VALIDATION}
    lazy_status_update(
        "12345",
        [
            OrderStatus.PENDING_CONFIRMATION,
            OrderStatus.PENDING_VALIDATION,
            OrderStatus.READY_TO_PAY,
        ],
    )
    payment_flow.ensure_ready_to_pay(confirm_data)
    assert api_client.get.call_count == 3


def test_confirm_payment(payment_flow, api_client):
    confirm_data = {"status": "AUTHORIZED", "paymentValue": "100.00"}
    payment_id = "12345"
    response = {"id": payment_id, "status": OrderStatus.PAYED}
    api_client.patch.return_value = response

    result = payment_flow.confirm_payment(confirm_data, payment_id)
    assert result == response
    api_client.patch.assert_called_once_with(
        f"{PIX_ENDPOINT}/{payment_id}", data=confirm_data
    )


def test_check_for_rejected_error(payment_flow):
    response = {"status": OrderStatus.REJECTED, "rejectReason": "Insufficient funds"}
    with pytest.raises(SantanderRejectedError):
        payment_flow._check_for_rejected_error(response)


def test_request_payment_status(payment_flow, api_client):
    payment_id = "12345"
    response = {"id": payment_id, "status": OrderStatus.PENDING_VALIDATION}
    api_client.get.return_value = response

    result = payment_flow._request_payment_status(payment_id)
    assert result == response
    api_client.get.assert_called_once_with(f"{PIX_ENDPOINT}/{payment_id}")


def test_request_confirm_payment(payment_flow, api_client):
    confirm_data = {"status": "AUTHORIZED", "paymentValue": "100.00"}
    payment_id = "12345"
    response = {"id": payment_id, "status": OrderStatus.PAYED}
    api_client.patch.return_value = response

    result = payment_flow._request_confirm_payment(confirm_data, payment_id)
    assert result == response
    api_client.patch.assert_called_once_with(
        f"{PIX_ENDPOINT}/{payment_id}", data=confirm_data
    )


@pytest.mark.parametrize("attemps_to_be_ready", [0, 2])
def test_payment_status_polling(
    payment_flow, api_client, mock_sleep, lazy_status_update, attemps_to_be_ready
):
    payment_id = "12345"
    lazy_status_update(
        payment_id,
        [OrderStatus.PENDING_VALIDATION] * attemps_to_be_ready
        + [OrderStatus.READY_TO_PAY],
    )

    result = payment_flow._payment_status_polling(
        payment_id, [OrderStatus.READY_TO_PAY], 10
    )
    assert result.get("status") == OrderStatus.READY_TO_PAY
    api_client.get.assert_called_with(f"{PIX_ENDPOINT}/{payment_id}")
    assert mock_sleep.call_count == attemps_to_be_ready


def test_payment_status_polling_timeout(
    payment_flow, api_client, mock_sleep, lazy_status_update
):
    payment_id = "12345"
    lazy_status_update(payment_id, [OrderStatus.PENDING_VALIDATION] * 3)

    with pytest.raises(SantanderStatusTimeoutError):
        payment_flow._payment_status_polling(payment_id, [OrderStatus.READY_TO_PAY], 3)
    assert api_client.get.call_count == 3
    assert mock_sleep.call_count == 2
