from decimal import ROUND_DOWN, Decimal
import logging
from itertools import cycle
from time import sleep, time
from typing import Literal
import re
import requests
import pathlib

from santander_sdk.api_client.exceptions import (
    SantanderRequestError,
    SantanderValueError,
)

logger = logging.getLogger("santanderLogger")

LENGTH_CNPJ = 14
LENGTH_CPF = 11

DictCodeTypes = Literal["CPF", "CNPJ", "CELULAR", "EMAIL", "EVP"]


def truncate_value(value):
    """Trunca o valor para duas casas decimais"""
    return str(Decimal(value).quantize(Decimal("0.00"), rounding=ROUND_DOWN))


def get_pix_key_type(chave: str) -> DictCodeTypes:
    """Retorna o tipo de chave PIX. Tipos possíveis: CPF, CNPJ, CELULAR, EMAIL, EVP"""
    chave = chave.strip()

    def is_cpf(cpf):
        try:
            return is_valid_cpf(cpf)
        except Exception:
            return False

    def is_cnpj(cnpj):
        try:
            return is_valid_cnpj(cnpj)
        except Exception:
            return False

    if is_cpf(chave):
        return "CPF"
    elif is_cnpj(chave):
        return "CNPJ"
    elif "@" in chave:
        return "EMAIL"
    elif len(chave) == 32 and re.fullmatch(r"[a-zA-Z0-9]+", chave):
        return "EVP"
    # +5511912345678
    elif len(only_numbers(chave)) == 13 and chave.startswith("+"):
        return "CELULAR"
    else:
        raise SantanderValueError(f"Chave Pix em formato inválido: {chave}")


def try_parse_response_to_json(response) -> dict | None:
    try:
        error_content = response.json()
    except requests.exceptions.JSONDecodeError:
        error_content = None
    return error_content


SANTANDER_STATUS_DESCRIPTIONS = {
    200: "Sucesso",
    201: "Recurso criado",
    400: "Erro de informação do cliente",
    401: "Não autorizado/Autenticado",
    403: "Não Autorizado",
    404: "Informação não encontrada",
    406: "O recurso de destino não possui uma representação atual que seria aceitável",
    422: "Entidade não processa/inadequada",
    429: "O usuário enviou muitas solicitações em um determinado período",
    500: "Erro de Servidor, Aplicação está fora",
    501: "O servidor não oferece suporte à funcionalidade necessária para atender à solicitação",
}


def get_status_code_description(status_code: int | str) -> str:
    """Retorna a descrição do status do Santander"""
    return f"{status_code} - {SANTANDER_STATUS_DESCRIPTIONS.get(int(status_code), 'Erro desconhecido')}"


def only_numbers(s):
    return re.sub("[^0-9]", "", s) if s else s


def is_valid_cpf(cpf):
    clean_cpf = only_numbers(cpf)
    if (
        len(clean_cpf) != LENGTH_CPF
        or not clean_cpf.isdigit()
        or len(set(str(clean_cpf))) == 1
    ):
        return False
    digit = {0: 0, 1: 0}
    a = 10
    for c in range(2):
        digit[c] = sum(i * int(clean_cpf[idx]) for idx, i in enumerate(range(a, 1, -1)))

        digit[c] = int(11 - (digit[c] % 11))
        if digit[c] > 9:
            digit[c] = 0
        a = 11

    return int(clean_cpf[9]) == int(digit[0] % 10) and int(clean_cpf[10]) == int(
        digit[1] % 10
    )


def is_valid_cnpj(cnpj):
    clean_cnpj = only_numbers(cnpj)
    if len(clean_cnpj) != LENGTH_CNPJ:
        return False

    if clean_cnpj in (c * LENGTH_CNPJ for c in "1234567890"):
        return False

    cnpj_r = clean_cnpj[::-1]
    for i in range(2, 0, -1):
        cnpj_enum = zip(cycle(range(2, 10)), cnpj_r[i:])
        dv = sum(map(lambda x: int(x[1]) * x[0], cnpj_enum)) * 10 % 11
        if cnpj_r[i - 1 : i] != str(dv % 10):
            return False

    return True


def retry_one_time_on_request_exception(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SantanderRequestError as e:
            logger.error(str(e))
            return func(*args, **kwargs)

    return wrapper


def convert_to_decimal(cents: int) -> Decimal:
    return Decimal(cents) / 100


def document_type(document_number: str) -> Literal["CPF", "CNPJ"]:
    if len(document_number) == 11:
        return "CPF"
    if len(document_number) == 14:
        return "CNPJ"
    raise SantanderValueError('Unknown document type "{document_number}"')


def get_content_from_url(url: str) -> bytes:
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    return response.content


def save_bytes_to_file(content: bytes, file_path: str):
    path = pathlib.Path(file_path)
    path.write_bytes(content)
    return str(path)


def download_file(url: str, file_path: str):
    content = get_content_from_url(url)
    saved_path = save_bytes_to_file(content, file_path)
    return saved_path


def polling_until_condition(
    func, conditional_func, timeout=60, interval=1, *args, **kwargs
):
    """Polling until a condition is met."""
    end_time = time() + timeout
    while time() <= end_time:
        result = func(*args, **kwargs)
        if conditional_func(result):
            return result
        sleep(interval)
    raise TimeoutError("Timeout polling until condition is met")
