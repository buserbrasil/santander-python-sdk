from abc import ABC, abstractmethod


class SantanderAbstractApiClient(ABC):
    @abstractmethod
    def get(self, endpoint: str, params: dict = None) -> dict:
        pass

    @abstractmethod
    def post(self, endpoint: str, data: dict) -> dict:
        pass

    @abstractmethod
    def put(self, endpoint: str, data: dict) -> dict:
        pass

    @abstractmethod
    def delete(self, endpoint: str) -> dict:
        pass

    @abstractmethod
    def patch(self, endpoint: str, data: dict) -> dict:
        pass
