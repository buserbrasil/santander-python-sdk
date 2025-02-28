import unittest
from unittest.mock import MagicMock, patch

from santander_sdk.api_client.helpers import (
    get_status_code_description,
    retry_one_time_on_request_exception,
    truncate_value,
    get_pix_key_type,
)
from santander_sdk.api_client.exceptions import (
    SantanderRequestError,
    SantanderValueError,
)


class UnitTestHelpers(unittest.TestCase):
    def test_truncate_value(self):
        self.assertEqual(truncate_value("123.456"), "123.45")
        self.assertEqual(truncate_value("123.4"), "123.40")
        self.assertEqual(truncate_value("1234567.95"), "1234567.95")
        self.assertEqual(truncate_value(12354.994), "12354.99")
        self.assertEqual(truncate_value(1.0099), "1.00")

    def test_get_pix_key_type(self):
        self.assertEqual(get_pix_key_type("12345678909"), "CPF")
        self.assertEqual(get_pix_key_type("12.345.678/0001-95"), "CNPJ")
        self.assertEqual(get_pix_key_type("+5511912345678"), "CELULAR")
        self.assertEqual(get_pix_key_type("email@example.com"), "EMAIL")
        self.assertEqual(get_pix_key_type("1234567890abcdef1234567890abcdef"), "EVP")

    def test_get_pix_key_type_invalid(self):
        with self.assertRaises(SantanderValueError):
            get_pix_key_type("234567890abcdef1234567890abcdef")

        with self.assertRaises(SantanderValueError):
            get_pix_key_type("55 34 12345678")

    def test_get_status_code_description(self):
        self.assertEqual(get_status_code_description(200), "200 - Sucesso")
        self.assertEqual(get_status_code_description(392), "392 - Erro desconhecido")

    @patch("santander_sdk.api_client.helpers.logger.error")
    def test_retry_one_time_on_request_exception(self, mock_logger_error):
        mock_func = MagicMock()
        mock_func.side_effect = [
            SantanderRequestError("Bad", 400, {"message": "Bad Request"}),
            "Success",
        ]

        decorated_func = retry_one_time_on_request_exception(mock_func)
        result = decorated_func()

        self.assertEqual(result, "Success")
        self.assertEqual(mock_func.call_count, 2)
        mock_logger_error.assert_called_once_with(
            "Request failed: Santander - Bad - 400 {'message': 'Bad Request'}"
        )
