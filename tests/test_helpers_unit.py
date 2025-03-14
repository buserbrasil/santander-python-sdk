import pytest
from unittest.mock import MagicMock, patch
import responses

from santander_sdk.api_client.helpers import (
    download_file,
    get_status_code_description,
    polling_until_condition,
    retry_one_time_on_request_exception,
    save_bytes_to_file,
    truncate_value,
    get_pix_key_type,
)
from santander_sdk.api_client.exceptions import (
    SantanderRequestError,
    SantanderValueError,
)


def test_truncate_value():
    assert truncate_value("123.456") == "123.45"
    assert truncate_value("123.4") == "123.40"
    assert truncate_value("1234567.95") == "1234567.95"
    assert truncate_value(12354.994) == "12354.99"
    assert truncate_value(1.0099) == "1.00"


def test_get_pix_key_type():
    assert get_pix_key_type("12345678909") == "CPF"
    assert get_pix_key_type("12.345.678/0001-95") == "CNPJ"
    assert get_pix_key_type("+5511912345678") == "CELULAR"
    assert get_pix_key_type("email@example.com") == "EMAIL"
    assert get_pix_key_type("1234567890abcdef1234567890abcdef") == "EVP"


def test_get_pix_key_type_invalid():
    with pytest.raises(SantanderValueError):
        get_pix_key_type("234567890abcdef1234567890abcdef")

    with pytest.raises(SantanderValueError):
        get_pix_key_type("55 34 12345678")


def test_get_status_code_description():
    assert get_status_code_description(200) == "200 - Sucesso"
    assert get_status_code_description(392) == "392 - Erro desconhecido"


@pytest.fixture
def mock_sleep_time():
    with (
        patch(
            "santander_sdk.api_client.helpers.sleep", return_value=None
        ) as mock_sleep,
        patch(
            "santander_sdk.api_client.helpers.time", side_effect=[0, 1, 2, 3, 4, 5]
        ) as mock_time,
    ):
        yield mock_sleep, mock_time


@patch("santander_sdk.api_client.helpers.logger.error")
def test_retry_one_time_on_request_exception(mock_logger_error):
    mock_func = MagicMock()
    mock_func.side_effect = [
        SantanderRequestError("Bad", 400, {"message": "Bad Request"}),
        "Success",
    ]

    decorated_func = retry_one_time_on_request_exception(mock_func)
    result = decorated_func()

    assert result == "Success"
    assert mock_func.call_count == 2
    mock_logger_error.assert_called_once_with(
        "Request failed: Santander - Bad - 400 {'message': 'Bad Request'}"
    )


def test_save_bytes_to_file(tmp_path):
    content = b"test content"
    file_path = tmp_path / "test_file.txt"
    result = save_bytes_to_file(content, str(file_path))
    assert result == str(file_path)
    assert file_path.read_bytes() == content


@responses.activate
def test_download_file(tmp_path):
    url = "http://example.com/file"
    file_path = tmp_path / "downloaded_file.txt"
    responses.add(responses.GET, url, body=b"file content", status=200)

    result = download_file(url, str(file_path))

    assert result == str(file_path)
    assert file_path.read_bytes() == b"file content"
    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == url


def test_polling_until_condition(mock_sleep_time):
    mock_sleep, _ = mock_sleep_time
    func = MagicMock(side_effect=[False, False, True])

    def conditional_func(x):
        return x

    result = polling_until_condition(func, conditional_func, timeout=10, interval=1)

    assert result is True
    assert func.call_count == 3
    mock_sleep.assert_called_with(1)


def test_polling_until_condition_timeout(mock_sleep_time):
    mock_sleep, _ = mock_sleep_time
    func = MagicMock(return_value=False)

    def conditional_func(x):
        return x

    with pytest.raises(TimeoutError):
        polling_until_condition(func, conditional_func, timeout=4, interval=1)

    assert func.call_count == 4
    mock_sleep.assert_called_with(1)
