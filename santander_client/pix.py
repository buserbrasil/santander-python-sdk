from decimal import Decimal as D
import logging
from time import sleep
from typing import List, Literal

from santander_client.api_client import get_client
from santander_client.api_client.exceptions import (
    SantanderClientException,
    SantanderPaymentException,
    SantanderRejectedTransactionException,
    SantanderRequestException,
    SantanderValueErrorException,
    SantanderTimeoutToChangeStatusException,
)
from datetime import datetime

from .api_client.helpers import (
    convert_to_decimal,
    document_type,
    get_pix_key_type,
    retry_one_time_on_request_exception,
    today,
    truncate_value,
)
from .santander_types import (
    BeneficiaryDataDict,
    ConfirmOrderStatus,
    CreateOrderStatus,
    SantanderAPIErrorResponse,
    SantanderCreatePixResponse,
    TransferPixResult,
)

logger = logging.getLogger("santanderLogger")

PIX_ENDPOINT = "/management_payments_partners/v1/workspaces/:workspaceid/pix_payments"
MAX_UPDATE_STATUS_ATTEMPTS = 10
MAX_UPDATE_STATUS_ATTEMPTS_TO_CONFIRM = 120
PIX_CONFIRM_INTERVAL_TIME = 2

TYPE_ACCOUNT_MAP = {
    "savings": "CONTA_POUPANCA",
    "payment": "CONTA_PAGAMENTO",
    "checking": "CONTA_CORRENTE",
}

SantanderPixResponse = SantanderCreatePixResponse | SantanderAPIErrorResponse

def transfer_pix_payment(pix_info: str | BeneficiaryDataDict, value: D, description: str, tags=[]) -> TransferPixResult:
    """Realiza uma transferência PIX para uma chave PIX ou para um beneficiário
        -   Se for informado uma chave PIX, o valor deve ser uma string com a chave CPF, CNPJ, EMAIL, CELULAR ou chave aleatória
        -   CELULAR deve ser informado no formato +5511912345678 (14 caracteres incluindo o +)
        -   Se for informado um beneficiário, o valor deve ser BeneficiaryDataDict com os dados do beneficiário

    ### Retorno de sucesso:
        -   success: True se a transferência foi realizada com sucesso
        -   data: Dados da transação PIX

    ### Retorno de erro:
        -   success: False se houve algum erro
        -   error: Mensagem de erro
    """
    try:
        if not value > 0:
            raise SantanderValueErrorException(f"Valor inválido para transferência PIX: {value}")

        create_pix_response = _request_create_pix_payment(pix_info, value, description, tags)
        pix_id = create_pix_response.get("id")
        logger.info("Santander - PIX criado com sucesso: {pix_id}")
        payment_status = create_pix_response.get("status")

        if not pix_id:
            raise SantanderClientException("ID do pagamento PIX não foi retornada pela criação do pagamento")

        confirm_response = _confirm_pix_payment(pix_id, value, payment_status)

        return {"success": True, "data": confirm_response}
    except Exception as e:
        error_message = str(e)
        logger.error(error_message)
        return {"success": False, "error": error_message}


def _pix_payment_status_polling(
    pix_id: str, until_status: List[str], context: Literal["CREATE", "CONFIRM"], max_attempts: int
) -> SantanderPixResponse:
    for attempt in range(max_attempts):
        response = _request_pix_payment_status(pix_id, context)
        payment_status = response.get("status")
        logger.info(f"Santander - Verificando status do pagamento PIX por polling: {pix_id} - {payment_status}")

        if payment_status in until_status:
            break

        if attempt == max_attempts - 1:
            raise SantanderTimeoutToChangeStatusException(
                "Limite de tentativas de atualização do status do pagamento PIX atingido", context
            )

        sleep(PIX_CONFIRM_INTERVAL_TIME)

    return response


def _confirm_pix_payment(pix_id: str, value: D, payment_status: CreateOrderStatus) -> SantanderPixResponse:
    """Confirma o pagamento PIX, realizando polling até que o status seja PAYED ou permaneça PENDING_CONFIRMATION.

    Exceções lançadas:
    - SantanderRejectedTransactionException: Se o status for REJECTED (Rejeitado pelo Santander).
    - SantanderTimeoutToChangeStatusException: Desistimos da transação após longa espera na atualização de status ANTES da confirmação.
    """

    if payment_status != CreateOrderStatus.READY_TO_PAY:
        logger.info(f"Santander - PIX não está pronto para pagamento: {pix_id}")
        _pix_payment_status_polling(
            pix_id=pix_id,
            until_status=[CreateOrderStatus.READY_TO_PAY],
            context="CREATE",
            max_attempts=MAX_UPDATE_STATUS_ATTEMPTS,
        )

    try:
        confirm_response = _request_confirm_pix_payment(pix_id, value)
    except SantanderRequestException as e:
        logger.error(f"Santander - Erro ao confirmar pagamento PIX: {str(e)}, {pix_id}, verificando status atual")
        confirm_response = _request_pix_payment_status(pix_id, "CONFIRM")
     
    if confirm_response.get("status") == ConfirmOrderStatus.PAYED:
        return confirm_response

    if not confirm_response.get("status") == ConfirmOrderStatus.PENDING_CONFIRMATION:
        raise SantanderClientException(f"Status inesperado após confirmação: {confirm_response.get('status')} {pix_id}")

    try:
        confirm_response = _pix_payment_status_polling(
            pix_id=pix_id,
            until_status=[ConfirmOrderStatus.PAYED],
            context="CONFIRM",
            max_attempts=MAX_UPDATE_STATUS_ATTEMPTS_TO_CONFIRM,
        )
    except SantanderTimeoutToChangeStatusException as e:
        """ Situação improvável aqui: Após longa espera depois do envio da autorização e confirmação de recebimento da autorização,
        não houve rejeição, mas também não houve atualização final de status mesmo após longa espera.
        Essa decisão pode evitar prejuízos de pagamentos duplicados devido a instabilidades do Santander ou da câmara de compensação."""
        logger.info(f"Santander - Houve timeout na atualização do status de pago do pagamento PIX:", str(e))
        return confirm_response

    return confirm_response


def _request_create_pix_payment(pix_info: BeneficiaryDataDict, value: D, description: str, tags=[]) -> SantanderPixResponse:
    """Cria uma ordem de pagamento. Caso o status seja REJECTED, a exceção SantanderRejectedTransactionException é lançada.
    Regra de negócio aqui: pagamento por beneficiário na request deve ser informado o bank_code ou ispb, nunca os dois."""
    data = {
        "tags": tags,
        "paymentValue": truncate_value(value),
        "remittanceInformation": description,
    }
    if isinstance(pix_info, str):
        pix_type = get_pix_key_type(pix_info)
        data.update({"dictCode": pix_info, "dictCodeType": pix_type})
    elif isinstance(pix_info, dict):
        try:
            beneficiary = {
                "branch": pix_info["bank_account"]["agencia"],
                "number": f"{pix_info['bank_account']['conta']}{pix_info['bank_account']['conta_dv']}",
                "type": TYPE_ACCOUNT_MAP[pix_info["bank_account"]["tipo_conta"]],
                "documentType": document_type(pix_info["bank_account"]["document_number"]),
                "documentNumber": pix_info["bank_account"]["document_number"],
                "name": pix_info["recebedor"]["name"],
            }
            if pix_info.get("bank_account"):
                if pix_info["bank_account"].get("bank_code_compe"):
                    beneficiary["bankCode"] = pix_info["bank_account"]["bank_code_compe"]
                else:
                    beneficiary["ispb"] = pix_info["bank_account"]["bank_code_ispb"]
            data.update({"beneficiary": beneficiary})
        except KeyError as e:
            raise SantanderValueErrorException(f"Campo obrigatório não informado para o beneficiário: {e}")
    else:
        raise SantanderValueErrorException("Chave PIX ou Beneficiário não informado")

    client = get_client()
    response = client.post(PIX_ENDPOINT, data=data)
    _check_for_rejected_exception(response, "Criação do pagamento PIX")
    return response


def _request_confirm_pix_payment(pix_payment_id: str, value: D) -> SantanderPixResponse:
    """Confirma o pagamento PIX através do PATCH e status AUTHORIZED
    O HTTP code de sucesso é 200, mesmo que o status seja REJECTED
    Caso o status seja REJECTED, a exceção SantanderRejectedTransactionException é lançada
    """
    if not pix_payment_id:
        raise SantanderValueErrorException("pix_payment_id não informado")

    if not value:
        raise SantanderValueErrorException("Valor não informado")

    client = get_client()
    data = {
        "status": "AUTHORIZED",
        "paymentValue": truncate_value(value),
    }
    response = client.patch(f"{PIX_ENDPOINT}/{pix_payment_id}", data=data)
    _check_for_rejected_exception(response, "Confirmação do pagamento PIX")
    return response


@retry_one_time_on_request_exception
def _request_pix_payment_status(pix_payment_id: str, step_description: str) -> SantanderPixResponse:
    """
    Retorna o estado atual do processamento de um pagamento PIX
    O HTTP code de retorno é 200, com o status atual do pagamento
    Caso o status seja REJECTED, a exceção SantanderRejectedTransactionException
    """
    if not pix_payment_id:
        raise SantanderValueErrorException("pix_payment_id não informado")

    client = get_client()
    response = client.get(f"{PIX_ENDPOINT}/{pix_payment_id}")
    _check_for_rejected_exception(response, step_description)
    return response


def _check_for_rejected_exception(pix_response: SantanderPixResponse, step: str):
    """Uma transação quando rejeitada com status REJECTED, não deve ser continuada"""
    if pix_response.get("status") == "REJECTED":
        reject_reason = pix_response.get("rejectReason", "Motivo não retornado pelo Santander")
        raise SantanderRejectedTransactionException(f"Pagamento rejeitado pelo banco na etapa {step} - {reject_reason}")

