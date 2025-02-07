from typing import Literal, TypedDict, Any


class SantanderAPIErrorsFields(TypedDict):
    _code: str
    _field: str
    _message: str


class SantanderAPIErrorResponse(TypedDict):
    """
    Resposta de erro da API do Santander.

    Os seguintes status seguem esse padrão:

    - 400: Erro de informação do cliente
    - 403: Não Autorizado
    - 404: Informação não encontrada
    - 406: O recurso de destino não possui uma representação atual que seria aceitável
    - 422: Entidade não processa/inadequada
    - 429: O usuário enviou muitas solicitações em um determinado período
    - 500: Erro de Servidor, Aplicação está fora
    - 501: O servidor não oferece suporte à funcionalidade necessária para atender à solicitação

    Atributos:
    _errorCode (int): Código de erro.
    _message (str): Mensagem de erro com no máximo 30 caracteres.
    _details (str): Detalhe da mensagem de erro com no máximo 100 caracteres.
    _timestamp (str): Data e hora que acontece o erro, seguindo o padrão RFC 3339, ISO 8601.
    _traceId (str): Identificador único entre todas as chamadas, utilizado para rastreamento de transações.
    _errors (list[SantanderErrors]): Informações adicionais sobre o erro, contendo:
        - _code (str): Código de erro específico.
        - _field (str): Identificação do campo com erro.
        - _message (str): Descrição da mensagem de erro.
    """

    _errorCode: int
    _message: str
    _details: str
    _timestamp: str
    _traceId: str
    _errors: list[SantanderAPIErrorsFields]


class SantanderAPIUnauthorizedResponse(TypedDict):
    """
    Resposta de erro de autenticação da API do Santander.
    Como por exemplo falta de autorização, token expirado, dados de autenticação inválidos.
    """

    timestamp: str
    httpStatus: str
    errorCode: int
    trackingId: str


class SantanderBeneficiary(TypedDict):
    """Usado para fins de tipagem em outras classes"""

    name: str
    documentType: Literal["CPF", "CNPJ"]
    documentNumber: str
    bankCode: str
    ispb: str
    branch: str
    number: str
    type: Literal["CONTA_CORRENTE", "CONTA_POUPANCA", "CONTA_PAGAMENTO"]


class SantanderPayer(TypedDict):
    """Usado para fins de tipagem em outras classes"""

    name: str
    documentType: Literal["CPF", "CNPJ"]
    documentNumber: str


class SantanderTransaction(TypedDict):
    """
    Usado para fins de tipagem em outras classes

    Atributos:
        value (str | None): Valor da transação.
        code (str | None): Código de autenticação bancária da transação.
        date (str): Data em que acontece a transação seguindo o padrão RFC 3339/ISO 8601.
        endToEnd (str | None): Identificador E2E do pagamento, iniciado com a letra E (maiúsculo), tem 32 caracteres.
    """

    value: str | None
    code: str | None
    date: str
    endToEnd: str | None


class SantanderDebitAccount(TypedDict):
    """
    Usado para fins de tipagem em outras classes
    Atributos:
        branch (str): A agência da conta.
        number (str): O número da conta.
    """

    branch: str
    number: str


class CreateOrderStatus:
    READY_TO_PAY = "READY_TO_PAY"
    PENDING_VALIDATION = "PENDING_VALIDATION"
    REJECTED = "REJECTED"


class ConfirmOrderStatus:
    PAYED = "PAYED"
    PENDING_CONFIRMATION = "PENDING_CONFIRMATION"
    REJECTED = "REJECTED"


class OrderStatus(ConfirmOrderStatus, CreateOrderStatus):
    pass


class SantanderCreatePixResponse(TypedDict):
    """
    Resposta da criação de transações pix do Santander (POST).
    - Os campos mais importantes aqui são o id, status, paymentValue e transaction.

    ### Status
    'status' com sucesso:
        - READY_TO_PAY é o status de pronto para pagamento e a garantia que o cliente pode seguir
            para a próxima etapa.
        - PENDING_VALIDATION é o status de pendência de validação dos dados nas câmaras de compensação.
    'status' com erro:
        - REJECTED é o status de rejeição do pagamento.

    ### Campos de retorno opcionais (meramente informativos, que inclusive são enviados por nós):
       - Caso seja um pagamento por chave, o campo dictCode e dictCodeType.
       - O mesmo vale para o beneficiary, caso seja um pagamento por beneficiário.
    """

    id: str
    workspaceId: str
    debitAccount: str
    remittanceInformation: str
    nominalValue: str
    totalValue: str
    payer: SantanderPayer
    transaction: SantanderTransaction
    tags: list[str]
    paymentValue: str
    status: Literal["READY_TO_PAY", "PENDING_VALIDATION", "REJECTED"]
    dictCode: str | None
    dictCodeType: Literal["CPF", "CNPJ", "CELULAR", "EMAIL", "EVP"] | None
    beneficiary: SantanderBeneficiary | None


class SantanderPixStatusResponse(TypedDict):
    """
    Resposta de transações pix do Santander tanto pelo PATCH quanto pelo GET.
    - Os campos mais importantes aqui são o id, status, paymentValue e transaction.

    ### Status
    'status' de sucesso:
        - PAYED é o status de pagamento efetuado com sucesso.
        - PENDING_CONFIRMATION é o status de pendência de confirmação do pagamento, esse status
        pode acontecer caso alguma câmara de compensação fique fora do ar no exato momento da
        chamada das APIs, se o banco recebedor está avaliando a transação, se o cliente ficar sem saldo
        em conta, entre outros casos.

    'status' de erro:
        - REJECTED é o status de rejeição do pagamento.

    ### Campos de retorno opcionais (meramente informativos, que inclusive são enviados por nós):
       - Caso seja um pagamento por chave, o campo dictCode e dictCodeType.
       - O mesmo vale para o beneficiary, caso seja um pagamento por beneficiário.
    """

    id: str
    workspaceId: str
    debitAccount: str
    remittanceInformation: str
    nominalValue: str
    totalValue: str
    payer: SantanderPayer
    transaction: SantanderTransaction
    tags: list[str]
    paymentValue: str
    status: Literal[
        "READY_TO_PAY",
        "PENDING_VALIDATION",
        "PAYED",
        "PENDING_CONFIRMATION",
        "REJECTED",
    ]
    dictCode: str | None
    dictCodeType: Literal["CPF", "CNPJ", "CELULAR", "EMAIL", "EVP"] | None
    beneficiary: SantanderBeneficiary | None


class BankAccountDict(TypedDict):
    agencia: str
    conta: str
    conta_dv: str
    tipo_conta: Literal["checking", "savings", "salary", "payment"]
    document_number: str
    bank_code_compe: str | None
    bank_code_ispb: str | None


class ReceiverDataDict(BankAccountDict):
    name: str


class BeneficiaryDataDict(TypedDict):
    """Dados do beneficiário para transferência PIX"""

    "Dados do recebedor para transferência PIX"
    bank_account: BankAccountDict
    recebedor: ReceiverDataDict


class TransferPixResult(TypedDict):
    success: bool
    data: SantanderPixStatusResponse | None
    error: Any | None
