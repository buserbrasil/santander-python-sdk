import unittest
from unittest.mock import MagicMock, patch

from santander_client.api_client.helpers import (
    get_status_code_description,
    retry_one_time_on_request_exception,
    truncate_value,
    get_pix_key_type,
)
from santander_client.api_client.exceptions import (
    SantanderClientException,
    SantanderConfigurationException,
    SantanderException,
    SantanderRejectedTransactionException,
    SantanderRequestException,
    SantanderValueErrorException,
    SantanderWorkspaceException,
    SantanderTimeoutToChangeStatusException,
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
        with self.assertRaises(SantanderValueErrorException):
            get_pix_key_type("234567890abcdef1234567890abcdef")

        with self.assertRaises(SantanderValueErrorException):
            get_pix_key_type("55 34 12345678")

    def test_get_status_code_description(self):
        self.assertEqual(get_status_code_description(200), "200 - Sucesso")
        self.assertEqual(get_status_code_description(392), "392 - Erro desconhecido")

    @patch("santander_client.api_client.helpers.logger.error")
    def test_retry_one_time_on_request_exception(self, mock_logger_error):
        mock_func = MagicMock()
        mock_func.side_effect = [
            SantanderRequestException("Deu ruim", 400, {"message": "Bad Request"}),
            "Success",
        ]

        decorated_func = retry_one_time_on_request_exception(mock_func)
        result = decorated_func()

        self.assertEqual(result, "Success")
        self.assertEqual(mock_func.call_count, 2)
        mock_logger_error.assert_called_once_with(
            "Falha na requisição: Santander - Deu ruim - 400 {'message': 'Bad Request'}"
        )


class UnitTestExceptions(unittest.TestCase):
    def test_custom_exception_messages(self):
        self.assertEqual(
            str(SantanderValueErrorException("chave pix inválida")),
            "Erro interno nos dados: Santander - chave pix inválida",
        )
        self.assertEqual(
            str(
                SantanderRejectedTransactionException("Criação da transação rejeitada")
            ),
            "Rejeição de pagamento: Santander - Criação da transação rejeitada",
        )
        self.assertEqual(
            str(SantanderTimeoutToChangeStatusException("Timeout", "CREATE")),
            "Timeout na atualização do status após várias tentativas: Santander - Timeout",
        )
        self.assertEqual(
            str(
                SantanderRequestException(
                    "Falha na requisição", 400, {"message": "Bad Request"}
                )
            ),
            "Falha na requisição: Santander - Falha na requisição - 400 {'message': 'Bad Request'}",
        )
        self.assertEqual(
            str(SantanderClientException("Erro no cliente")),
            "Erro no cliente Santander: Santander - Erro no cliente",
        )
        self.assertEqual(
            str(SantanderConfigurationException("Falta o account_id")),
            "Erro de configuração: Santander - Falta o account_id",
        )
        self.assertEqual(
            str(SantanderWorkspaceException("id não encontrado")),
            "Erro no workspace: Santander - id não encontrado",
        )

        assert isinstance(
            SantanderValueErrorException("chave pix inválida"), SantanderException
        )
