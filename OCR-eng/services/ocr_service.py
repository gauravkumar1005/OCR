from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from OCR_Extraction_folder.multimodal_extractor import multimodal_extract

from project import config

logger = logging.getLogger(__name__)

_QWEN_ENGINE_VALUES = {"qwen", "qwen2.5-vl", "ollama"}


class OCRService:
    def __init__(self) -> None:
        self.engine = (config.OCR_ENGINE or "paddleocr").strip().lower()
        self.engine_display_name = config.OCR_ENGINE_DISPLAY_NAME
        logger.info("OCR service initialized with engine=%s", self.engine_display_name)

    def run_page_ocr(self, image_path: str, page_folder: Path) -> dict[str, Any]:
        logger.info(
            "Running OCR on image=%s selected_engine=%s",
            image_path,
            self.engine_display_name,
        )

        if self.engine in _QWEN_ENGINE_VALUES:
            logger.info("Qwen2.5-VL (Ollama) selected; PaddleOCR preprocessing is bypassed for this page")
            return self._run_qwen_ocr(image_path, page_folder)

        logger.info("PaddleOCR selected; using multimodal_extract preprocessing/extraction path")
        return self._run_paddle_ocr(image_path, page_folder)

    def _run_paddle_ocr(self, image_path: str, page_folder: Path) -> dict[str, Any]:
        page_result = multimodal_extract(image_path, output_folder=str(page_folder))
        generated_json_path = page_folder / f"{Path(image_path).stem}_ocr.json"
        if generated_json_path.exists():
            logger.info("OCR JSON loaded from %s", generated_json_path)
            return json.loads(generated_json_path.read_text(encoding="utf-8"))

        logger.info("OCR JSON file not found; returning in-memory PaddleOCR result")
        if isinstance(page_result, dict):
            return page_result
        return {
            "engine": "paddleocr",
            "text": str(page_result),
            "full_text": str(page_result),
        }

    def _run_qwen_ocr(self, image_path: str, page_folder: Path) -> dict[str, Any]:
        from quality_assessment.analyzer import LayoutAwareQualityAnalyzer

        analyzer = LayoutAwareQualityAnalyzer()
        target_prompt = (
            "You are an advanced Intelligent Document Processing vision engine. "
            "Analyze the provided image document carefully. "
            "Transcribe all visible text, numbers, headings, and tabular data exactly as they appear in the visual layout. "
            "Return ONLY the raw transcribed text. Do not wrap it in markdown code blocks, do not include conversational words, and do not explain your actions."
        )

        transcript = asyncio.run(
            analyzer.extract_via_vision_llm(
                image_path=image_path,
                target_prompt=target_prompt,
            )
        )

        generated_json = {
            "engine": "qwen2.5-vl-ollama",
            "model": config.QWEN_VISION_MODEL,
            "source_image": image_path,
            "text": transcript,
            "full_text": transcript,
        }

        generated_json_path = page_folder / f"{Path(image_path).stem}_ocr.json"
        generated_json_path.write_text(
            json.dumps(generated_json, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("OCR JSON written to %s", generated_json_path)
        return generated_json
