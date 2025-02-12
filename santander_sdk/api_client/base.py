from urllib.parse import urljoin

from requests import Session


class BaseURLSession(Session):
    def __init__(self, base_url):
        self.base_url = base_url
        super().__init__()

    def prepare_request(self, request):
        request.url = urljoin(self.base_url, request.url)
        return super().prepare_request(request)
