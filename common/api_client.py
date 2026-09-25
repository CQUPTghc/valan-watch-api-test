"""Small requests wrapper used by the integration tests."""

import logging
from urllib.parse import urlsplit

import requests

from common.assertions import redact_text, safe_response_text


LOGGER = logging.getLogger("valan.api")


class ApiClient:
    def __init__(self, base_url):
        self.base_url = (base_url or "").rstrip("/")
        self.session = requests.Session()

    def set_token(self, token):
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def request(self, method, path, **kwargs):
        """Send a request without logging credentials, payloads or query values."""
        kwargs.setdefault("timeout", 15)
        log_path = redact_text(urlsplit(path).path)
        try:
            response = self.session.request(
                method, self.base_url + path, **kwargs
            )
        except requests.RequestException as exc:
            LOGGER.error("%s %s request failed: %s", method.upper(), log_path,
                         type(exc).__name__)
            raise
        LOGGER.info("%s %s -> HTTP %s", method.upper(), log_path,
                    response.status_code)
        if response.status_code >= 400:
            LOGGER.warning("%s %s failure response: %s", method.upper(),
                           log_path, safe_response_text(response))
        return response

    def get(self, path, params=None, **kwargs):
        return self.request("GET", path, params=params, **kwargs)

    def post(self, path, json=None, **kwargs):
        return self.request("POST", path, json=json, **kwargs)

    def put(self, path, json=None, **kwargs):
        return self.request("PUT", path, json=json, **kwargs)

    def patch(self, path, json=None, **kwargs):
        return self.request("PATCH", path, json=json, **kwargs)

    def delete(self, path, **kwargs):
        return self.request("DELETE", path, **kwargs)
