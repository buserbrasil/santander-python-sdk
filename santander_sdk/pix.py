from decimal import Decimal as D
import logging
from time import sleep
from typing import List, Literal, cast

from santander_sdk.api_client.client import SantanderApiClient
from santander_sdk.api_client.exceptions import (
    SantanderClientException,
    SantanderRejectedTransactionException,
    SantanderRequestException,
    SantanderValueErrorException,
    SantanderTimeoutToChangeStatusException,
)

from santander_sdk.api_client.helpers import (
    document_type,
    get_pix_key_type,
    retry_one_time_on_request_exception,
    truncate_value,
)
from santander_sdk.types import (
    BeneficiaryDataDict,
    ConfirmOrderStatus,
    CreateOrderStatus,
    OrderStatus,
    OrderStatusType,
    SantanderPixResponse,
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


def transfer_pix_payment(
    client: SantanderApiClient,
    pix_info: str | BeneficiaryDataDict,
    value: D,
    description: str,
    tags: list[str] = [],
) -> TransferPixResult:
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
            raise SantanderValueErrorException(
                f"Valor inválido para transferência PIX: {value}"
            )

        create_pix_response = _request_create_pix_payment(
            client, pix_info, value, description, tags
        )
        pix_id = create_pix_response.get("id")
        logger.info("Santander - PIX criado com sucesso: {pix_id}")
        payment_status = create_pix_response.get("status")

        if not pix_id:
            raise SantanderClientException(
                "ID do pagamento não foi retornada na criação"
            )

        if payment_status is None:
            raise SantanderClientException(
                "Status do pagamento não retornado na criação"
            )

        confirm_response = _confirm_pix_payment(client, pix_id, value, payment_status)

        return {"success": True, "data": confirm_response, "error": ""}
    except Exception as e:
        error_message = str(e)
        logger.error(error_message)
        return {"success": False, "error": error_message, "data": None}


def _pix_payment_status_polling(
    client: SantanderApiClient,
    pix_id: str,
    until_status: List[str],
    context: Literal["CREATE", "CONFIRM"],
    max_attempts: int,
) -> SantanderPixResponse:
    response = _request_pix_payment_status(client, pix_id, context)
    if response.get("status") in until_status:
        return response

    for attempt in range(max_attempts - 1):
        response = _request_pix_payment_status(client, pix_id, context)
        payment_status = response.get("status")
        logger.info(
            f"Santander - Verificando status do pagamento PIX por polling: {pix_id} - {payment_status}"
        )

        if payment_status in until_status:
            break

        if attempt == max_attempts - 2:
            raise SantanderTimeoutToChangeStatusException(
                "Limite de tentativas de atualização do status do pagamento PIX atingido",
                context,
            )

        sleep(PIX_CONFIRM_INTERVAL_TIME)

    return response


def _confirm_pix_payment(
    client: SantanderApiClient, pix_id: str, value: D, payment_status: OrderStatusType
) -> SantanderPixResponse:
    """Confirma o pagamento PIX, realizando polling até que o status seja PAYED ou permaneça PENDING_CONFIRMATION.

    Exceções lançadas:
    - SantanderRejectedTransactionException: Se o status for REJECTED (Rejeitado pelo Santander).
    - SantanderTimeoutToChangeStatusException: Desistimos da transação após longa espera na atualização de status ANTES da confirmação.
    """

    if payment_status != CreateOrderStatus.READY_TO_PAY:
        logger.info(f"Santander - PIX não está pronto para pagamento: {pix_id}")
        _pix_payment_status_polling(
            client,
            pix_id=pix_id,
            until_status=[CreateOrderStatus.READY_TO_PAY],
            context="CREATE",
            max_attempts=MAX_UPDATE_STATUS_ATTEMPTS,
        )

    try:
        confirm_response = _request_confirm_pix_payment(client, pix_id, value)
    except SantanderRequestException as e:
        logger.error(
            f"Santander - Erro ao confirmar pagamento PIX: {str(e)}, {pix_id}, verificando status atual"
        )
        confirm_response = _request_pix_payment_status(client, pix_id, "CONFIRM")

    if confirm_response.get("status") == ConfirmOrderStatus.PAYED:
        return confirm_response

    if not confirm_response.get("status") == ConfirmOrderStatus.PENDING_CONFIRMATION:
        raise SantanderClientException(
            f"Status inesperado após confirmação: {confirm_response.get('status')} {pix_id}"
        )

    try:
        confirm_response = _pix_payment_status_polling(
            client,
            pix_id=pix_id,
            until_status=[ConfirmOrderStatus.PAYED],
            context="CONFIRM",
            max_attempts=MAX_UPDATE_STATUS_ATTEMPTS_TO_CONFIRM,
        )
    except SantanderTimeoutToChangeStatusException as e:
        """ Situação improvável aqui: Após longa espera depois do envio da autorização e confirmação de recebimento da autorização,
        não houve rejeição, mas também não houve atualização final de status mesmo após longa espera.
        Essa decisão pode evitar prejuízos de pagamentos duplicados devido a instabilidades do Santander ou da câmara de compensação."""
        logger.info(
            "Santander - Houve timeout na atualização do status de pago do pagamento PIX:",
            str(e),
        )
        return confirm_response

    return confirm_response


def _request_create_pix_payment(
    client: SantanderApiClient,
    pix_info: BeneficiaryDataDict | str,
    value: D,
    description: str,
    tags: list[str] = [],
) -> SantanderPixResponse:
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
                "documentType": document_type(
                    pix_info["bank_account"]["document_number"]
                ),
                "documentNumber": pix_info["bank_account"]["document_number"],
                "name": pix_info["recebedor"]["name"],
            }
            bank_account = pix_info["bank_account"]
            bank_code = bank_account.get("bank_code_compe", "")
            bank_ispb = bank_account.get("bank_code_ispb", "")
            if bank_code:
                beneficiary["bankCode"] = bank_code
            elif bank_ispb:
                beneficiary["ispb"] = bank_ispb
            else:
                raise SantanderValueErrorException("A chave de entrada é inválida")

            data.update({"beneficiary": beneficiary})
        except KeyError as e:
            raise SantanderValueErrorException(
                f"Campo obrigatório não informado para o beneficiário: {e}"
            )
    else:
        raise SantanderValueErrorException("Chave PIX ou Beneficiário não informado")

    response = cast(SantanderPixResponse, client.post(PIX_ENDPOINT, data=data))
    _check_for_rejected_exception(response, "Criação do pagamento PIX")
    return response


def _request_confirm_pix_payment(
    client: SantanderApiClient, pix_payment_id: str, value: D
) -> SantanderPixResponse:
    """Confirma o pagamento PIX através do PATCH e status AUTHORIZED
    O HTTP code de sucesso é 200, mesmo que o status seja REJECTED
    Caso o status seja REJECTED, a exceção SantanderRejectedTransactionException é lançada
    """
    if not pix_payment_id:
        raise SantanderValueErrorException("pix_payment_id não informado")

    if not value:
        raise SantanderValueErrorException("Valor não informado")

    data = {
        "status": "AUTHORIZED",
        "paymentValue": truncate_value(value),
    }
    response = client.patch(f"{PIX_ENDPOINT}/{pix_payment_id}", data=data)
    response = cast(SantanderPixResponse, response)
    _check_for_rejected_exception(response, "Confirmação do pagamento PIX")
    return response


@retry_one_time_on_request_exception
def _request_pix_payment_status(
    client: SantanderApiClient, pix_payment_id: str, step_description: str
) -> SantanderPixResponse:
    """
    Retorna o estado atual do processamento de um pagamento PIX
    O HTTP code de retorno é 200, com o status atual do pagamento
    Caso o status seja REJECTED, a exceção SantanderRejectedTransactionException
    """
    if not pix_payment_id:
        raise SantanderValueErrorException("pix_payment_id não informado")

    response = client.get(f"{PIX_ENDPOINT}/{pix_payment_id}")
    response = cast(SantanderPixResponse, response)
    _check_for_rejected_exception(response, step_description)
    return response


def _check_for_rejected_exception(pix_response: SantanderPixResponse, step: str):
    """Uma transação quando rejeitada com status REJECTED, não deve ser continuada"""
    if pix_response.get("status") == OrderStatus.REJECTED:
        reject_reason = pix_response.get(
            "rejectReason", "Motivo não retornado pelo Santander"
        )
        raise SantanderRejectedTransactionException(
            f"Pagamento rejeitado pelo banco na etapa {step} - {reject_reason}"
        )
