"""Receipts Types"""

from typing import List, Literal, Optional, TypedDict

from santander_sdk.types import SantanderAPIErrorsFields

ALREADY_REQUESTED_RECEIPT = "006"

PaymentCategoryData = Optional[
    Literal[
        "DEBITO-AUTOMATICO",
        "BOLETOS",
        "TRIBUTOS",
        "CONCESSIONARIAS",
        "DOC",
        "TED",
        "TRANSFERENCIAS-OUTRAS",
        "PIX",
    ]
]


class ListPaymentParams(TypedDict, total=False):
    start_date: str  # Format: YYYY-MM-DD
    end_date: str  # Format: YYYY-MM-DD
    _limit: Optional[str]  # Results per page
    _offset: Optional[str]
    account_agency: Optional[str]
    account_number: Optional[str]
    beneficiary_document: Optional[str]
    category: Optional[PaymentCategoryData]
    start_time: Optional[str]  # Format: HH:MM:SS (24-hour)
    end_time: Optional[str]  # Format: HH:MM:SS (24-hour)


class PaymentPayerPersonDocumentDetails(TypedDict):
    documentTypeCode: Literal["CPF", "CNPJ"]
    documentNumber: str


class PaymentPayerPersonDocument(TypedDict):
    document: PaymentPayerPersonDocumentDetails


class PaymentPayerPerson(TypedDict):
    person: PaymentPayerPersonDocument


class PaymentReceiptPayee(TypedDict):
    name: str


class PaymentAmountInfo(TypedDict):
    """" direct: amount: "10.00 """ ""

    direct: dict


class PaymentReceiptDetails(TypedDict):
    paymentId: str
    commitmentNumber: str
    payer: PaymentPayerPerson
    payee: PaymentReceiptPayee
    paymentAmountInfo: PaymentAmountInfo
    """2025-02-07T17:26:57-03:00"""
    requestValueDate: str


class PaymentReceiptCategory(TypedDict):
    code: PaymentCategoryData


class PaymentReceiptChannel(TypedDict):
    code: str


class PaymentReceipts(TypedDict):
    payment: PaymentReceiptDetails
    category: PaymentReceiptCategory
    channel: PaymentReceiptChannel


class ReceiptRequestResponse(TypedDict):
    requestId: str
    creationDateTime: str  # Format: YYYY-MM-DDTHH:MM:SS-03:00


class ReceiptFileRepository(TypedDict):
    location: Optional[str]


"""
    statusInfo:
        'REQUESTED' represents when the file was requested via POST, but its asynchronous process has not yet completed.
        'AVAILABLE' means that the file is available and can be downloaded. Check fileRepository for the file location.
        'EXPUNGED' or 'ERROR' means you need to request a new file via POST.
"""
ReceiptStatusCode = Literal["REQUESTED", "AVAILABLE", "EXPUNGED", "ERROR"]


class ReceiptStatus:
    REQUESTED = "REQUESTED"
    AVAILABLE = "AVAILABLE"
    EXPUNGED = "EXPUNGED"
    ERROR = "ERROR"


class ReceiptFileStatusInfo(TypedDict):
    statusCode: ReceiptStatusCode


class ReceiptFileResponse(TypedDict):
    fileRepository: ReceiptFileRepository
    mimeType: str
    expirationDate: Optional[str]
    statusInfo: ReceiptFileStatusInfo
    audit: dict


class PaginableResponseLinkHref(TypedDict):
    href: str


class PaginableResponseLinks(TypedDict):
    _first: Optional[PaginableResponseLinkHref]
    _prev: Optional[PaginableResponseLinkHref]
    _next: Optional[PaginableResponseLinkHref]


class PaymentReceiptErrorResponse(TypedDict):
    """Base response error payment receipts
    Example:
    {
        "errors": [
            {
                "code": "006",
                "message": "Já existe comprovante disponível para esta solicitação.",
                "traceId": "12345-0251-4bef-833c-qas123356"
            }
        ]
    }
    """

    error: List[SantanderAPIErrorsFields]


class ListPaymentsResponse(TypedDict):
    """Base response list payment receipts"""

    """ example: {
    "paymentsReceipts": [
        {
            "payment": {
                "paymentId": "VXB123456789ABCFEF",
                "payer": {
                    "person": {
                        "document": {
                            "documentTypeCode": "CNPJ",
                            "documentNumber": "12345678901234"
                        }
                    }
                },
                "payee": {
                    "name": "STARK BANK S.A."
                },
                "paymentAmountInfo": {
                    "direct": {
                        "amount": "10.00"
                    }
                },
                "requestValueDate": "2025-02-07T17:26:57-03:00"
            },
            "category": {
                "code": "BOLETOS"
            },
            "channel": {
                "code": "GATEWAY DE PAGAMENTOS - VX"
            }
        },
        ..... repeat
        "links": {
            "_first": {
                "href": "https://trust-open.api.santander.com.br/consult_payment_receipts/v1/payment_receipts?_offset=0&_limit=10"
            },
            "_prev": null,
            "_next": {
                "href": "https://trust-open.api.santander.com.br/consult_payment_receipts/v1/payment_receipts?_offset=10&_limit=10"
            }
        }
    }
    """
    paymentsReceipts: List[PaymentReceipts]
    links: PaginableResponseLinks


class ReceiptInfoResponse(TypedDict):
    """Received on Create Receipt and Get Receipt"""

    """ Example: 
    {
        "request": {
            "requestId": "123456-e691-42d0-b659-1234657899",
            "creationDateTime": "2025-03-07T12:32:38-03:00"
        },
        "file": {
            "fileRepository": {
                "location": null
            },
            "mimeType": "application/pdf",
            "expirationDate": null,
            "statusInfo": {
                "statusCode": "REQUESTED"
            },
            "audit": {
                "creationDateTime": null
            }
        }
    }
    """
    request: ReceiptRequestResponse
    file: ReceiptFileResponse


class ReceiptCreationHistoryResponse(TypedDict):
    """Example:
        {
        "paymentReceiptsFileRequests": [
            {
                "request": {
                    "requestId": "XXXXXX-46b9-4895-99e2-AAAAAAAAAA",
                    "creationDateTime": "2025-03-07T15:16:39-03:00"
                },
                "file": {
                    "fileRepository": {
                        "location": null
                    },
                    "mimeType": "application/pdf",
                    "expirationDate": "2025-03-07T19:18:49-03:00",
                    "statusInfo": {
                        "statusCode": "EXPUNGED"
                    },
                    "audit": {
                        "creationDateTime": "2025-03-07T15:16:39-03:00"
                    }
                }
            },
              {
                "request": {
                    "requestId": "XXXXXX-ab92-4378-a26a-BBBBBBBBBBB",
                    "creationDateTime": "2025-03-10T11:56:41-03:00"
                },
                "file": {
                    "fileRepository": {
                        "location": null
                    },
                    "mimeType": "application/pdf",
                    "expirationDate": "2025-03-10T12:01:42-03:00",
                    "statusInfo": {
                        "statusCode": "AVAILABLE"
                    },
                    "audit": {
                        "creationDateTime": "2025-03-10T11:56:42-03:00"
                    }
                }
            }
        ],
        "links": {
            "_first": {
                "href": "https://trust-open.api.santander.com.br/consult_payment_receipts/v1/payment_receipts/XXXXXXXXXXX/file_requests?_offset=0&_limit=10"
            },
            "_prev": null,
            "_next": null,
            "_last": null,
            "_count": 1
        }
    }

    """

    paymentReceiptsFileRequests: List[ReceiptInfoResponse]
    links: PaginableResponseLinks


class ReceiptInfoResult(TypedDict):
    payment_id: str
    receipt_request_id: str
    status: ReceiptStatusCode
    location: Optional[str]
    data: ReceiptInfoResponse
