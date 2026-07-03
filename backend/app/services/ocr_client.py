from __future__ import annotations

import asyncio
import logging
from typing import Any

import requests

from app.core.config import Settings
from app.exceptions.base import OCRException

logger = logging.getLogger(__name__)


class OCRClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.timeout = (10.0, 300.0)
        logger.info(
            "OCR settings loaded OCR_ENGINE_URL=%s OCR_API_URL=%s",
            settings.OCR_ENGINE_URL or "<empty>",
            settings.OCR_API_URL or "<empty>",
        )

    def process_document(self, payload: dict[str, Any]) -> dict[str, Any]:
        base_url = self._get_base_url()
        if not base_url:
            raise OCRException("OCR_ENGINE_URL is not configured")

        headers = {"Content-Type": "application/json"}
        if self.settings.OCR_API_KEY:
            headers["Authorization"] = f"Bearer {self.settings.OCR_API_KEY}"

        url = f"{base_url.rstrip('/')}/ocr/process"
        safe_headers = dict(headers)
        if "Authorization" in safe_headers:
            safe_headers["Authorization"] = "<redacted>"

        logger.info("Sending OCR request url=%s", url)
        logger.info("OCR request headers=%s", safe_headers)
        logger.debug("OCR request payload=%s", payload)
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
            body_text = response.text
            try:
                body_json = response.json()
            except ValueError:
                body_json = None
            logger.info("OCR response status_code=%s", response.status_code)
            logger.info("OCR response body=%s", body_text)
            return {
                "status_code": response.status_code,
                "body": body_text,
                "json": body_json,
            }
        except requests.RequestException as exc:
            logger.exception("OCR request failed url=%s payload=%s", url, payload)
            raise OCRException(f"OCR processing request failed: {exc}") from exc

    def get_request_url(self) -> str:
        base_url = self._get_base_url()
        return f"{base_url.rstrip('/')}/ocr/process" if base_url else ""

    async def health_check(self) -> bool:
        base_url = self._get_base_url()
        if not base_url:
            return False

        def _check() -> bool:
            try:
                response = requests.get(f"{base_url.rstrip('/')}/health", timeout=(10.0, 10.0))
                return 200 <= response.status_code < 300
            except requests.RequestException:
                return False

        return await asyncio.to_thread(_check)

    def _get_base_url(self) -> str:
        return self.settings.OCR_ENGINE_URL or self.settings.OCR_API_URL
