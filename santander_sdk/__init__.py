from santander_sdk.api_client.client import SantanderApiClient
from santander_sdk.api_client.client_configuration import SantanderClientConfiguration
from santander_sdk.api_client.helpers import (
    get_pix_key_type,
    document_type,
)

from santander_sdk.pix import transfer_pix, get_transfer
from santander_sdk.types import SantanderBeneficiary
from santander_sdk.typing.receipts_types import (
    ListPaymentParams,
    ListPaymentsResponse,
    ReceiptCreationHistoryResponse,
    ReceiptInfoResult,
)
from santander_sdk.payment_receipts import (
    payment_list,
    payment_list_iter_by_pages,
    create_receipt,
    get_receipt,
    receipt_creation_history,
)
from santander_sdk.api_client.exceptions import (
    SantanderRequestError,
    SantanderValueError,
    SantanderError,
)

__all__ = [
    "SantanderApiClient",
    "SantanderClientConfiguration",
    # Pix
    "SantanderBeneficiary",
    "get_pix_key_type",
    "document_type",
    "transfer_pix",
    "get_transfer",
    # payment_receipts
    "payment_list",
    "create_receipt",
    "get_receipt",
    "receipt_creation_history",
    "payment_list_iter_by_pages",
    # receipts_types
    "ListPaymentParams",
    "ReceiptInfoResult",
    "ListPaymentsResponse",
    "ReceiptCreationHistoryResponse",
    # Comom exceptions
    "SantanderRequestError",
    "SantanderValueError",
    "SantanderError",
]
