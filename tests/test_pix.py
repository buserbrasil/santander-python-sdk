import unittest
from decimal import Decimal as D
from unittest.mock import patch

from santander_client.api_client.exceptions import (
    SantanderRejectedTransactionException,
    SantanderTimeoutToChangeStatusException,
)
from santander_client.pix import (
    PIX_ENDPOINT,
    TYPE_ACCOUNT_MAP,
    _check_for_rejected_exception,
    _confirm_pix_payment,
    _pix_payment_status_polling,
    _request_confirm_pix_payment,
    _request_create_pix_payment,
    _request_pix_payment_status,
    transfer_pix_payment,
)
from mock.santander_mocker import (
    beneficiary_dict_john_cc,
    get_dict_payment_pix_response,
)
from santander_client.types import CreateOrderStatus


class UnitTestPix(unittest.TestCase):
    @patch("santander_client.pix.get_client")
    def test_request_create_pix_payment_by_key(self, mock_get_client):
        pix_id = "A5Q41DS5Q5AS4"
        tags = ["bf: 1234", "nf: 1234", "nf_data: 2021-10-10"]
        mock_get_client.return_value.post.return_value = get_dict_payment_pix_response(
            pix_id, D("123"), "PENDING_VALIDATION"
        )
        mock_client_post = mock_get_client.return_value.post
        test_cases = [
            ("CPF", "12345678909"),
            ("CNPJ", "12345678000195"),
            ("CELULAR", "+5511999999999"),
            ("EVP", "ea56sf2q987as6ea56sf2q987as6ea56"),
        ]
        for key_type, key_value in test_cases:
            with self.subTest(key_type=key_type, key_value=key_value):
                response = _request_create_pix_payment(key_value, D("123"), "Pagamento Teste", tags=tags)
                self.assertEqual(response["id"], pix_id)
                self.assertEqual(response["status"], "PENDING_VALIDATION")
                self.assertEqual(response["paymentValue"], 123.00)

                expected_body_request = {
                    "tags": tags,
                    "paymentValue": "123.00",
                    "remittanceInformation": "Pagamento Teste",
                    "dictCode": key_value,
                    "dictCodeType": key_type,
                }
                mock_client_post.assert_called_with(
                    "/management_payments_partners/v1/workspaces/:workspaceid/pix_payments", data=expected_body_request
                )

    @patch("santander_client.pix.get_client")
    def test_request_create_pix_payment_with_beneficiary(self, mock_get_client):
        value = D("1248.33")
        pix_id = "QAF65E6Q-A2SQ6A-Q5AS-6Q5"
        description = "Pagamento Teste"
        tags = ["bf: 1234", "nf: 1234", "nf_data: 2021-10-10"]
        mock_get_client.return_value.post.return_value = get_dict_payment_pix_response(
            pix_id, value, "PENDING_VALIDATION", beneficiary_dict_john_cc
        )
        mock_client_post = mock_get_client.return_value.post

        response = _request_create_pix_payment(beneficiary_dict_john_cc, value, description, tags=tags)
        self.assertEqual(response["id"], pix_id)
        self.assertEqual(response["status"], "PENDING_VALIDATION")
        self.assertEqual(response["paymentValue"], value)

        john_bank_account = beneficiary_dict_john_cc["bank_account"]
        expected_body_request = {
            "tags": tags,
            "paymentValue": str(value),
            "remittanceInformation": description,
            "beneficiary": {
                "branch": beneficiary_dict_john_cc["bank_account"]["agencia"],
                "number": f"{john_bank_account['conta']}{john_bank_account['conta_dv']}",
                "type": TYPE_ACCOUNT_MAP["checking"],
                "documentType": "CPF",
                "documentNumber": john_bank_account["document_number"],
                "name": beneficiary_dict_john_cc["recebedor"]["name"],
                "bankCode": john_bank_account["bank_code_compe"],
            },
        }
        mock_client_post.assert_called_with(PIX_ENDPOINT, data=expected_body_request)

    @patch("santander_client.pix.get_client")
    def test_request_confirm_pix_payment(self, mock_get_client):
        pix_id = "12345"
        value = D("1248.33")
        mock_get_client.return_value.patch.return_value = get_dict_payment_pix_response(pix_id, value, "PAYED")
        mock_client_patch = mock_get_client.return_value.patch

        confirm_result = _request_confirm_pix_payment(pix_id, value)
        self.assertEqual(confirm_result["status"], "PAYED")
        self.assertEqual(confirm_result["id"], pix_id)
        self.assertEqual(confirm_result["paymentValue"], value)
        self.assertEqual(confirm_result["dictCode"], "12345678909")
        self.assertEqual(confirm_result["dictCodeType"], "CPF")

        expected_body_request = {
            "paymentValue": str(value),
            "status": "AUTHORIZED",
        }
        mock_client_patch.assert_called_with(f"{PIX_ENDPOINT}/{pix_id}", data=expected_body_request)

    @patch("santander_client.pix.get_client")
    def test_request_pix_payment_status(self, mock_get_client):
        pix_id = "A5Q5A6S54F-56AS45F6F6"
        mock_get_client.return_value.get.return_value = get_dict_payment_pix_response(
            pix_id, D("12156.66"), "PENDING_VALIDATION"
        )
        status_result = _request_pix_payment_status(pix_payment_id=pix_id, step_description="CREATE")

        self.assertEqual(status_result["status"], "PENDING_VALIDATION")
        mock_get_client.return_value.get.assert_called_with(f"{PIX_ENDPOINT}/{pix_id}")

    @patch("santander_client.pix.get_client")
    def test_confirm_pix_payment(self, mock_get_client):
        pix_id = "12345"
        value = D("100.00")
        mock_get_client.return_value.patch.return_value = get_dict_payment_pix_response(pix_id, value, "PAYED")

        payment_status = CreateOrderStatus.READY_TO_PAY

        confirm_result = _confirm_pix_payment(pix_id, value, payment_status)
        self.assertEqual(confirm_result["status"], "PAYED")
        self.assertEqual(confirm_result["paymentValue"], 100.00)
        self.assertEqual(confirm_result["dictCode"], "12345678909")
        self.assertEqual(confirm_result["dictCodeType"], "CPF")

    def test_check_for_rejected_exception(self):
        pix_response = {"status": "REJECTED"}
        with self.assertRaises(SantanderRejectedTransactionException):
            _check_for_rejected_exception(pix_response, "Criação do pagamento PIX")

    @patch("santander_client.pix.sleep", return_value=None)
    @patch("santander_client.pix.get_client")
    def test_transfer_pix_payment_success(self, mock_get_client, mock_sleep):
        pix_id = "2A1F6556Q6AS"
        tags = ["bf: 1234", "nf: 1234", "nf_data: 2021-10-10"]
        mock_get_client.return_value.post.return_value = get_dict_payment_pix_response(
            pix_id, D("100.00"), "PENDING_VALIDATION"
        )
        mock_get_client.return_value.patch.return_value = get_dict_payment_pix_response(
            pix_id, D("100.00"), "PENDING_CONFIRMATION"
        )
        mock_get_client.return_value.get.side_effect = [
            get_dict_payment_pix_response(pix_id, D("100.00"), "READY_TO_PAY"),
            get_dict_payment_pix_response(pix_id, D("100.00"), "PENDING_CONFIRMATION"),
            get_dict_payment_pix_response(pix_id, D("100.00"), "PAYED"),
        ]
        expected_post_data = {
            "dictCode": "12345678909",
            "dictCodeType": "CPF",
            "paymentValue": "100.00",
            "remittanceInformation": "Pagamento Teste",
            "tags": tags
        }
        pix_key = "12345678909"
        value = D("100.00")

        transfer_result = transfer_pix_payment(pix_key, value, "Pagamento Teste", tags=tags)
        self.assertTrue(transfer_result["success"])
        self.assertEqual(transfer_result["data"]["status"], "PAYED")
        self.assertEqual(transfer_result["data"]["paymentValue"], value)
        self.assertEqual(transfer_result["data"]["dictCode"], "12345678909")
        self.assertEqual(transfer_result["data"]["dictCodeType"], "CPF")
        self.assertEqual(transfer_result["data"]["id"], pix_id)
        mock_get_client.return_value.post.assert_called_with(
            "/management_payments_partners/v1/workspaces/:workspaceid/pix_payments",
            data=expected_post_data
        )

    @patch("santander_client.pix.get_client")
    def test_transfer_pix_payment_invalid_value(self, mock_get_client):
        pix_key = "12345678909"
        description = "Pagamento Teste valor inválido"

        transfer_result = transfer_pix_payment(pix_key, D("-21.55"), description)
        self.assertFalse(transfer_result["success"])
        transfer_result = transfer_pix_payment(pix_key, D("0"), description)
        self.assertFalse(transfer_result["success"])
        transfer_result = transfer_pix_payment(pix_key, D("0.00"), description)
        self.assertFalse(transfer_result["success"])
        self.assertIn("Valor inválido para transferência PIX", transfer_result["error"])
        transfer_result = transfer_pix_payment(pix_key, "", description)
        self.assertFalse(transfer_result["success"])

    @patch("santander_client.pix.get_client")
    def test_transfer_pix_payment_no_pix_id(self, mock_get_client):
        mock_get_client.return_value.post.return_value = get_dict_payment_pix_response(
            "", D("100.00"), "PENDING_VALIDATION"
        )
        response = transfer_pix_payment("12345678909", D("100.00"), "Pagamento Teste")
        self.assertFalse(response["success"])
        self.assertIn("ID do pagamento PIX não foi retornada pela criação do pagamento", response["error"])

    @patch("santander_client.pix.get_client")
    def test_transfer_pix_payment_rejected(self, mock_get_client):
        pix_key = "12345678909"
        value = D("100.00")

        mock_get_client.return_value.post.return_value = get_dict_payment_pix_response(pix_key, value, "REJECTED")

        response = transfer_pix_payment(pix_key, value, "Pagamento Teste")
        self.assertFalse(response["success"])
        self.assertIn("Pagamento rejeitado pelo banco na etapa Criação do pagamento PIX", response["error"])

    @patch("santander_client.pix._request_pix_payment_status")
    @patch("santander_client.pix.sleep", return_value=None)
    def test_pix_payment_status_polling_timeout(self, mock_sleep, mock_request_pix_payment_status):
        pix_id = "ABCDE"
        mock_request_pix_payment_status.return_value = get_dict_payment_pix_response(
            pix_id, D("1234"), "PENDING_VALIDATION"
        )

        with self.assertRaises(SantanderTimeoutToChangeStatusException):
            _pix_payment_status_polling(pix_id=pix_id, until_status=["READY_TO_PAY"], context="CREATE", max_attempts=3)
        self.assertEqual(mock_request_pix_payment_status.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)

    @patch("santander_client.pix._request_pix_payment_status")
    @patch("santander_client.pix.sleep", return_value=None)
    def test_pix_payment_status_polling_status_reached(self, mock_sleep, mock_request_pix_payment_status):
        pix_id = "6S54A654A6QAS"
        mock_request_pix_payment_status.side_effect = [
            get_dict_payment_pix_response(pix_id, D("55423.21"), "PENDING"),
            get_dict_payment_pix_response(pix_id, D("55423.21"), "PENDING"),
            get_dict_payment_pix_response(pix_id, D("55423.21"), "READY_TO_PAY"),
        ]
        response = _pix_payment_status_polling(
            pix_id=pix_id, until_status=["READY_TO_PAY"], context="CREATE", max_attempts=5
        )
        self.assertEqual(response["status"], "READY_TO_PAY")
        self.assertEqual(mock_request_pix_payment_status.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)

    @patch("santander_client.pix._request_pix_payment_status")
    @patch("santander_client.pix.sleep", return_value=None)
    def test_pix_payment_status_polling_multiple_status_reached(self, mock_sleep, mock_request_pix_payment_status):
        pix_id = "6S54A654A6E"
        mock_request_pix_payment_status.side_effect = [
            get_dict_payment_pix_response(pix_id, D("637.33"), "PENDING"),
            get_dict_payment_pix_response(pix_id, D("637.33"), "PENDING"),
            get_dict_payment_pix_response(pix_id, D("637.33"), "READY_TO_PAY"),
            get_dict_payment_pix_response(pix_id, D("637.33"), "PAYED"),
        ]

        response = _pix_payment_status_polling(
            pix_id=pix_id, until_status=["READY_TO_PAY", "PAYED"], context="CREATE", max_attempts=5
        )
        self.assertEqual(response["status"], "READY_TO_PAY")
        self.assertEqual(mock_request_pix_payment_status.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)
