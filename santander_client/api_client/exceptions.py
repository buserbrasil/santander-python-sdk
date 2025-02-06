from typing import Literal


class SantanderException(Exception):
    def __init__(self, *args):
        super().__init__(*args)

    def __str__(self):
        return f"Santander - {super().__str__()}"


class SantanderConfigurationException(SantanderException):
    def __init__(self, *args):
        super().__init__(*args)

    def __str__(self):
        return f"Erro de configuração: {super().__str__()}"


class SantanderRequestException(SantanderException):
    def __init__(self, message: str, status_code: int, content: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.content = content

    def __str__(self):
        error_content = self.content or "Sem detalhes na resposta"
        return f"Falha na requisição: {super().__str__()} - {self.status_code} {error_content}"


class SantanderClientException(SantanderException):
    def __init__(self, message):
        super().__init__(message)

    def __str__(self):
        return f"Erro no cliente Santander: {super().__str__()}"


class SantanderWorkspaceException(SantanderException):
    def __init__(self, message):
        super().__init__(message)

    def __str__(self):
        return f"Erro no workspace: {super().__str__()}"


class SantanderValueErrorException(SantanderException):
    def __init__(self, message):
        super().__init__(message)

    def __str__(self):
        return f"Erro interno nos dados: {super().__str__()}"


class SantanderRejectedTransactionException(SantanderException):
    def __init__(self, message):
        super().__init__(message)

    def __str__(self):
        return f"Rejeição de pagamento: {super().__str__()}"


class SantanderTimeoutToChangeStatusException(SantanderException):
    def __init__(self, message, step: Literal["CREATE", "CONFIRM"]):
        super().__init__(message)
        self.step = step

    def __str__(self):
        return f"Timeout na atualização do status após várias tentativas: {super().__str__()}"


class SantanderPaymentException(SantanderException):
    def __init__(self, message):
        super().__init__(message)

    def __str__(self):
        return f"Algo Falhou: {super().__str__()}"
