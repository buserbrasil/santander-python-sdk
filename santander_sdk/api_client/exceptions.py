from typing import Literal


class SantanderError(Exception):
    def __init__(self, *args):
        super().__init__(*args)

    def __str__(self):
        return f"Santander - {super().__str__()}"


class SantanderRequestError(SantanderError):
    def __init__(self, message: str, status_code: int, content: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.content = content

    def __str__(self):
        error_content = self.content or "No response details"
        return (
            f"Request failed: {super().__str__()} - {self.status_code} {error_content}"
        )


class SantanderClientError(SantanderError):
    def __init__(self, message):
        super().__init__(message)

    def __str__(self):
        return f"Santander client error: {super().__str__()}"


class SantanderValueError(SantanderError, ValueError):
    def __init__(self, message):
        super().__init__(message)

    def __str__(self):
        return f"Internal data error: {super().__str__()}"


class SantanderRejectedError(SantanderError):
    def __init__(self, message):
        super().__init__(message)

    def __str__(self):
        return f"Payment rejection: {super().__str__()}"


class SantanderStatusTimeoutError(SantanderError):
    def __init__(self, message, step: Literal["CREATE", "CONFIRM"]):
        super().__init__(message)
        self.step = step

    def __str__(self):
        return f"Status update timeout after several attempts: {super().__str__()}"
