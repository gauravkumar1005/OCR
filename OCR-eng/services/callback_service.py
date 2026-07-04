from __future__ import annotations

import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)


class CallbackService:
    def __init__(self, timeout: tuple[int, int]) -> None:
        self.timeout = timeout

    def send_callback(self, callback_url: str, payload: dict[str, Any]) -> requests.Response:
        logger.info("Sending callback to %s", callback_url)
        response = requests.post(callback_url, json=payload, timeout=self.timeout)
        logger.info("Callback status code/body: %s | %s", response.status_code, response.text)
        response.raise_for_status()
        return response
