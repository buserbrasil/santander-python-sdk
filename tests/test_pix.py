from typing import cast
import unittest
from decimal import Decimal as D
from unittest.mock import MagicMock, patch

from santander_sdk.api_client.exceptions import (
    SantanderRejectedTransactionException,
    SantanderTimeoutToChangeStatusException,
)
from santander_sdk.pix import (
    PIX_ENDPOINT,
    _check_for_rejected_exception,
    _confirm_pix_payment,
    _pix_payment_status_polling,
    _request_confirm_pix_payment,
    _request_create_pix_payment,
    _request_pix_payment_status,
    transfer_pix_payment,
)
from mock.santander_mocker import (
    santander_beneciary_john,
    get_dict_payment_pix_response,
    beneciary_john_dict_json,
)
from santander_sdk.types import OrderStatus, SantanderTransferResponse


class UnitTestPix(unittest.TestCase):
    def setUp(self) -> None:
        self.api_client = MagicMock()
        return super().setUp()

    def test_request_create_pix_payment_by_key(self):
        pix_id = "A5Q41DS5Q5AS4"
        tags = ["bf: 1234", "nf: 1234", "nf_data: 2021-10-10"]

        self.api_client.post.return_value = get_dict_payment_pix_response(
            pix_id, D("123"), OrderStatus.PENDING_VALIDATION
        )
        test_cases = [
            ("CPF", "12345678909"),
            ("CNPJ", "12345678000195"),
            ("CELULAR", "+5511999999999"),
            ("EVP", "ea56sf2q987as6ea56sf2q987as6ea56"),
        ]
        for key_type, key_value in test_cases:
            with self.subTest(key_type=key_type, key_value=key_value):
                response = _request_create_pix_payment(
                    self.api_client,
                    key_value,
                    D("123"),
                    "Pagamento Teste",
                    tags=tags,
                )
                assert response == {
                    "addedValue": "0.00",
                    "debitAccount": {
                        "branch": "0001",
                        "number": "123456789",
                    },
                    "deductedValue": "0.00",
                    "dictCode": "12345678909",
                    "dictCodeType": "CPF",
                    "id": "A5Q41DS5Q5AS4",
                    "nominalValue": "123",
                    "obs": "payment mockado",
                    "payer": {
                        "documentNumber": "20157935000193",
                        "documentType": "CPNJ",
                        "name": "John Doe SA",
                    },
                    "paymentValue": "123",
                    "remittanceInformation": "informação da transferência",
                    "status": OrderStatus.PENDING_VALIDATION,
                    "tags": [],
                    "totalValue": "123",
                    "transaction": {
                        "code": "13a654q",
                        "date": "2025-01-08T13:44:36Z",
                        "endToEnd": "a213e5q564as456f4as56f",
                        "value": "123",
                    },
                    "workspaceId": "3870ba5d-d58e-4182-992f-454e5d0e08e2",
                }

                expected_body_request = {
                    "tags": tags,
                    "paymentValue": "123.00",
                    "remittanceInformation": "Pagamento Teste",
                    "dictCode": key_value,
                    "dictCodeType": key_type,
                }
                self.api_client.post.assert_called_with(
                    "/management_payments_partners/v1/workspaces/:workspaceid/pix_payments",
                    data=expected_body_request,
                )

    def test_request_create_pix_payment_with_beneficiary(self):
        value = D("1248.33")
        pix_id = "QAF65E6Q-A2SQ6A-Q5AS-6Q5"
        description = "Pagamento Teste"
        tags = ["bf: 1234", "nf: 1234", "nf_data: 2021-10-10"]
        self.api_client.post.return_value = get_dict_payment_pix_response(
            pix_id, value, OrderStatus.PENDING_VALIDATION, santander_beneciary_john
        )

        response = _request_create_pix_payment(
            self.api_client,
            santander_beneciary_john,
            value,
            description,
            tags=tags,
        )
        assert response == {
            "addedValue": "0.00",
            "beneficiary": beneciary_john_dict_json,
            "debitAccount": {
                "branch": "0001",
                "number": "123456789",
            },
            "deductedValue": "0.00",
            "id": "QAF65E6Q-A2SQ6A-Q5AS-6Q5",
            "nominalValue": "1248.33",
            "obs": "payment mockado",
            "payer": {
                "documentNumber": "20157935000193",
                "documentType": "CPNJ",
                "name": "John Doe SA",
            },
            "paymentValue": "1248.33",
            "remittanceInformation": "informação da transferência",
            "status": OrderStatus.PENDING_VALIDATION,
            "tags": [],
            "totalValue": "1248.33",
            "transaction": {
                "code": "13a654q",
                "date": "2025-01-08T13:44:36Z",
                "endToEnd": "a213e5q564as456f4as56f",
                "value": "1248.33",
            },
            "workspaceId": "3870ba5d-d58e-4182-992f-454e5d0e08e2",
        }

        expected_body_request = {
            "tags": tags,
            "paymentValue": str(value),
            "remittanceInformation": description,
            "beneficiary": beneciary_john_dict_json,
        }
        self.api_client.post.assert_called_with(
            PIX_ENDPOINT, data=expected_body_request
        )

    def test_request_confirm_pix_payment(self):
        pix_id = "12345"
        value = D("1248.33")
        self.api_client.patch.return_value = get_dict_payment_pix_response(
            pix_id, value, OrderStatus.PAYED
        )

        confirm_result = _request_confirm_pix_payment(self.api_client, pix_id, value)
        assert confirm_result == {
            "addedValue": "0.00",
            "debitAccount": {
                "branch": "0001",
                "number": "123456789",
            },
            "deductedValue": "0.00",
            "dictCode": "12345678909",
            "dictCodeType": "CPF",
            "id": "12345",
            "nominalValue": "1248.33",
            "obs": "payment mockado",
            "payer": {
                "documentNumber": "20157935000193",
                "documentType": "CPNJ",
                "name": "John Doe SA",
            },
            "paymentValue": "1248.33",
            "remittanceInformation": "informação da transferência",
            "status": OrderStatus.PAYED,
            "tags": [],
            "totalValue": "1248.33",
            "transaction": {
                "code": "13a654q",
                "date": "2025-01-08T13:44:36Z",
                "endToEnd": "a213e5q564as456f4as56f",
                "value": "1248.33",
            },
            "workspaceId": "3870ba5d-d58e-4182-992f-454e5d0e08e2",
        }

        self.api_client.patch.assert_called_with(
            f"{PIX_ENDPOINT}/{pix_id}",
            data={
                "paymentValue": str(value),
                "status": "AUTHORIZED",
            },
        )

    def test_request_pix_payment_status(self):
        pix_id = "A5Q5A6S54F-56AS45F6F6"
        self.api_client.get.return_value = get_dict_payment_pix_response(
            pix_id, D("12156.66"), OrderStatus.PENDING_VALIDATION
        )
        status_result = _request_pix_payment_status(
            self.api_client, pix_payment_id=pix_id, step_description="CREATE"
        )

        status = status_result.get("status", "")
        self.assertEqual(status, OrderStatus.PENDING_VALIDATION)
        self.api_client.get.assert_called_with(f"{PIX_ENDPOINT}/{pix_id}")

    def test_confirm_pix_payment(self):
        pix_id = "12345"
        value = D("100.00")
        self.api_client.patch.return_value = get_dict_payment_pix_response(
            pix_id, value, OrderStatus.PAYED
        )

        confirm_result = _confirm_pix_payment(
            self.api_client, pix_id, value, OrderStatus.READY_TO_PAY
        )
        assert confirm_result == {
            "addedValue": "0.00",
            "debitAccount": {
                "branch": "0001",
                "number": "123456789",
            },
            "deductedValue": "0.00",
            "dictCode": "12345678909",
            "dictCodeType": "CPF",
            "id": "12345",
            "nominalValue": "100.00",
            "obs": "payment mockado",
            "payer": {
                "documentNumber": "20157935000193",
                "documentType": "CPNJ",
                "name": "John Doe SA",
            },
            "paymentValue": "100.00",
            "remittanceInformation": "informação da transferência",
            "status": OrderStatus.PAYED,
            "tags": [],
            "totalValue": "100.00",
            "transaction": {
                "code": "13a654q",
                "date": "2025-01-08T13:44:36Z",
                "endToEnd": "a213e5q564as456f4as56f",
                "value": "100.00",
            },
            "workspaceId": "3870ba5d-d58e-4182-992f-454e5d0e08e2",
        }

    def test_check_for_rejected_exception(self):
        transfer_dict = get_dict_payment_pix_response(
            "123", D("100.00"), OrderStatus.REJECTED
        )
        pix_response = cast(SantanderTransferResponse, transfer_dict)
        with self.assertRaises(SantanderRejectedTransactionException):
            _check_for_rejected_exception(pix_response, "Criação do pagamento PIX")

    @patch("santander_sdk.pix.sleep", return_value=None)
    def test_transfer_pix_payment_success(self, mock_sleep):
        pix_id = "2A1F6556Q6AS"
        tags = ["bf: 1234", "nf: 1234", "nf_data: 2021-10-10"]
        self.api_client.post.return_value = get_dict_payment_pix_response(
            pix_id, D("100.00"), OrderStatus.PENDING_VALIDATION
        )
        self.api_client.patch.return_value = get_dict_payment_pix_response(
            pix_id, D("100.00"), OrderStatus.PENDING_CONFIRMATION
        )
        self.api_client.get.side_effect = [
            get_dict_payment_pix_response(
                pix_id, D("100.00"), OrderStatus.READY_TO_PAY
            ),
            get_dict_payment_pix_response(
                pix_id, D("100.00"), OrderStatus.PENDING_CONFIRMATION
            ),
            get_dict_payment_pix_response(pix_id, D("100.00"), OrderStatus.PAYED),
        ]
        expected_post_data = {
            "dictCode": "12345678909",
            "dictCodeType": "CPF",
            "paymentValue": "100.00",
            "remittanceInformation": "Pagamento Teste",
            "tags": tags,
        }
        pix_key = "12345678909"
        value = D("100.00")

        transfer_result = transfer_pix_payment(
            self.api_client,
            pix_key,
            value,
            "Pagamento Teste",
            tags=tags,
        )
        assert transfer_result == {
            "data": {
                "addedValue": "0.00",
                "debitAccount": {
                    "branch": "0001",
                    "number": "123456789",
                },
                "deductedValue": "0.00",
                "dictCode": "12345678909",
                "dictCodeType": "CPF",
                "id": "2A1F6556Q6AS",
                "nominalValue": "100.00",
                "obs": "payment mockado",
                "payer": {
                    "documentNumber": "20157935000193",
                    "documentType": "CPNJ",
                    "name": "John Doe SA",
                },
                "paymentValue": "100.00",
                "remittanceInformation": "informação da transferência",
                "status": OrderStatus.PAYED,
                "tags": [],
                "totalValue": "100.00",
                "transaction": {
                    "code": "13a654q",
                    "date": "2025-01-08T13:44:36Z",
                    "endToEnd": "a213e5q564as456f4as56f",
                    "value": "100.00",
                },
                "workspaceId": "3870ba5d-d58e-4182-992f-454e5d0e08e2",
            },
            "success": True,
            "error": "",
        }
        self.api_client.post.assert_called_with(
            "/management_payments_partners/v1/workspaces/:workspaceid/pix_payments",
            data=expected_post_data,
        )

    @patch("santander_sdk.pix.sleep", return_value=None)
    def test_transfer_pix_payment_invalid_value(self, mock_sleep):
        pix_key = "12345678909"
        description = "Pagamento Teste valor inválido"

        transfer_result = transfer_pix_payment(
            self.api_client, pix_key, D("-21.55"), description
        )
        self.assertFalse(transfer_result["success"])
        transfer_result = transfer_pix_payment(
            self.api_client, pix_key, D("0"), description
        )
        self.assertFalse(transfer_result["success"])
        transfer_result = transfer_pix_payment(
            self.api_client, pix_key, D("0.00"), description
        )
        self.assertFalse(transfer_result["success"])
        self.assertIn("Valor inválido para transferência PIX", transfer_result["error"])
        transfer_result = transfer_pix_payment(
            self.api_client, pix_key, D("21.23"), description
        )
        self.assertFalse(transfer_result["success"])

    def test_transfer_pix_payment_no_pix_id(self):
        self.api_client.post.return_value = get_dict_payment_pix_response(
            "", D("100.00"), OrderStatus.PENDING_VALIDATION
        )
        response = transfer_pix_payment(
            self.api_client, "12345678909", D("100.00"), "Pagamento Teste"
        )
        self.assertFalse(response["success"])
        self.assertIn(
            "ID do pagamento não foi retornada na criação",
            response["error"],
        )

    def test_transfer_pix_payment_rejected(self):
        pix_key = "12345678909"
        value = D("100.00")

        self.api_client.post.return_value = get_dict_payment_pix_response(
            pix_key, value, OrderStatus.REJECTED
        )

        response = transfer_pix_payment(
            self.api_client, pix_key, value, "Pagamento Teste"
        )
        self.assertFalse(response["success"])
        self.assertIn(
            "Pagamento rejeitado pelo banco na etapa Criação do pagamento PIX",
            response["error"],
        )

    @patch("santander_sdk.pix._request_pix_payment_status")
    @patch("santander_sdk.pix.sleep", return_value=None)
    def test_pix_payment_status_polling_timeout(
        self, mock_sleep, mock_request_pix_payment_status
    ):
        pix_id = "ABCDE"
        mock_request_pix_payment_status.return_value = get_dict_payment_pix_response(
            pix_id, D("1234"), OrderStatus.PENDING_VALIDATION
        )

        with self.assertRaises(SantanderTimeoutToChangeStatusException):
            _pix_payment_status_polling(
                self.api_client,
                pix_id=pix_id,
                until_status=[OrderStatus.READY_TO_PAY],
                context="CREATE",
                max_attempts=3,
            )
        self.assertEqual(mock_request_pix_payment_status.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 1)

    @patch("santander_sdk.pix._request_pix_payment_status")
    @patch("santander_sdk.pix.sleep", return_value=None)
    def test_pix_payment_status_polling_status_reached(
        self, mock_sleep, mock_request_pix_payment_status
    ):
        pix_id = "6S54A654A6QAS"
        mock_request_pix_payment_status.side_effect = [
            get_dict_payment_pix_response(pix_id, D("55423.21"), "PENDING"),
            get_dict_payment_pix_response(pix_id, D("55423.21"), "PENDING"),
            get_dict_payment_pix_response(
                pix_id, D("55423.21"), OrderStatus.READY_TO_PAY
            ),
        ]
        response = _pix_payment_status_polling(
            self.api_client,
            pix_id=pix_id,
            until_status=[OrderStatus.READY_TO_PAY],
            context="CREATE",
            max_attempts=5,
        )
        status = response.get("status", "")
        self.assertEqual(status, OrderStatus.READY_TO_PAY)
        self.assertEqual(mock_request_pix_payment_status.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 1)

    @patch("santander_sdk.pix._request_pix_payment_status")
    @patch("santander_sdk.pix.sleep", return_value=None)
    def test_pix_payment_status_polling_multiple_status_reached(
        self, mock_sleep, mock_request_pix_payment_status
    ):
        pix_id = "6S54A654A6E"
        mock_request_pix_payment_status.side_effect = [
            get_dict_payment_pix_response(pix_id, D("637.33"), "PENDING"),
            get_dict_payment_pix_response(pix_id, D("637.33"), "PENDING"),
            get_dict_payment_pix_response(
                pix_id, D("637.33"), OrderStatus.READY_TO_PAY
            ),
            get_dict_payment_pix_response(pix_id, D("637.33"), OrderStatus.PAYED),
        ]

        response = _pix_payment_status_polling(
            self.api_client,
            pix_id=pix_id,
            until_status=[OrderStatus.READY_TO_PAY, OrderStatus.PAYED],
            context="CREATE",
            max_attempts=5,
        )
        status = response.get("status", "")
        self.assertEqual(status, OrderStatus.READY_TO_PAY)
        self.assertEqual(mock_request_pix_payment_status.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 1)
