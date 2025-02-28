from decimal import Decimal as D
from unittest.mock import MagicMock

from santander_sdk.api_client.exceptions import SantanderRejectedError
from santander_sdk.pix import (
    PIX_ENDPOINT,
    get_transfer,
    transfer_pix,
)

from mock.santander_mocker import (
    santander_beneciary_john,
    get_dict_payment_pix_response,
    beneciary_john_dict_json,
)
from santander_sdk.types import OrderStatus

import pytest

espected_create_pix_dict = {
    "tags": ["bf: 1234", "nf: 1234", "nf_data: 2021-10-10"],
    "paymentValue": "123.00",
    "remittanceInformation": "Pagamento Teste",
    "dictCode": "12345678909",
    "dictCodeType": "CPF",
}
tags = ["bf: 1234", "nf: 1234", "nf_data: 2021-10-10"]
create_pix_response = get_dict_payment_pix_response(
    "1234", D("123"), OrderStatus.PENDING_VALIDATION
)
ready_to_pay_response = get_dict_payment_pix_response(
    "1234", D("123"), OrderStatus.READY_TO_PAY
)
confirm_response = get_dict_payment_pix_response("1234", D("123"), OrderStatus.PAYED)


@pytest.fixture
def api_client():
    return MagicMock()


@pytest.fixture
def mock_sdk(mocker):
    mock_sdk = MagicMock()
    mock_sdk.create = mocker.patch(
        "santander_sdk.pix.SantanderPaymentFlow.create_payment"
    )
    mock_sdk.ready_to_pay = mocker.patch(
        "santander_sdk.pix.SantanderPaymentFlow.ensure_ready_to_pay"
    )
    mock_sdk.confirm = mocker.patch(
        "santander_sdk.pix.SantanderPaymentFlow.confirm_payment"
    )
    mock_sdk.get_transfer = mocker.patch("santander_sdk.pix.get_transfer")
    mock_sdk.ready_to_pay.return_value = ready_to_pay_response
    mock_sdk.create.return_value = create_pix_response
    mock_sdk.confirm.return_value = confirm_response
    mock_sdk.get_transfer.return_value = confirm_response
    return mock_sdk


def test_request_create_pix_payment_by_key(api_client, mock_sdk):
    test_cases = [
        ("CPF", "12345678909"),
        ("CNPJ", "12345678000195"),
        ("CELULAR", "+5511999999999"),
        ("EVP", "ea56sf2q987as6ea56sf2q987as6ea56"),
    ]
    for key_type, key_value in test_cases:
        response = transfer_pix(
            api_client,
            key_value,
            D("123"),
            "Pagamento Teste",
            tags=tags,
        )
        assert response["success"] is True
        mock_sdk.create.assert_called_with(
            {
                "tags": tags,
                "paymentValue": "123.00",
                "remittanceInformation": "Pagamento Teste",
                "dictCode": key_value,
                "dictCodeType": key_type,
            }
        )
        mock_sdk.ready_to_pay.assert_called_once_with(create_pix_response)
        mock_sdk.confirm.assert_called_with(
            {
                "status": "AUTHORIZED",
                "paymentValue": "123.00",
            },
            "1234",
        )
        mock_sdk.create.reset_mock()
        mock_sdk.ready_to_pay.reset_mock()
        mock_sdk.confirm.reset_mock()


def test_request_create_pix_payment_with_beneficiary(api_client, mock_sdk):
    response = transfer_pix(
        api_client, santander_beneciary_john, D("1248.33"), "Pagamento de teste", tags
    )
    assert response["success"] is True
    mock_sdk.create.assert_called_with(
        {
            "tags": tags,
            "paymentValue": "1248.33",
            "remittanceInformation": "Pagamento de teste",
            "beneficiary": beneciary_john_dict_json,
        }
    )
    mock_sdk.ready_to_pay.assert_called_once_with(create_pix_response)
    mock_sdk.confirm.assert_called_with(
        {
            "status": "AUTHORIZED",
            "paymentValue": "1248.33",
        },
        "1234",
    )


def test_request_pix_payment_status(api_client):
    api_client.get.return_value = confirm_response
    result = get_transfer(api_client, "2175814018608")
    api_client.get.assert_called_with(f"{PIX_ENDPOINT}/2175814018608")
    assert result == confirm_response


@pytest.mark.parametrize("value", [D("-21.55"), D("0"), D("0.00"), None])
def test_transfer_pix_payment_invalid_value(api_client, mock_sdk, value):
    transfer_result = transfer_pix(api_client, "12345678909", value, "test")
    assert transfer_result["success"] is False
    assert "Invalid value for PIX transfer" in transfer_result["error"]


def test_transfer_pix_payment_no_pix_id(api_client, mock_sdk):
    mock_sdk.create.return_value["id"] = None
    result = transfer_pix(api_client, "12345678909", D("100.00"), "Pagamento Teste")
    assert result["success"] is False
    assert "Payment ID was not returned on creation" in result["error"]


def test_transfer_pix_payment_rejected(api_client, mock_sdk):
    mock_sdk.create.side_effect = SantanderRejectedError("Rejected by bank")
    result = transfer_pix(api_client, "12345678909", D("100.00"), "Pagamento Teste")
    assert result["success"] is False
    assert "Payment rejection" in result["error"]
