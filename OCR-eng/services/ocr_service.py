from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any

from OCR_Extraction_folder.multimodal_extractor import multimodal_extract

from project import config

logger = logging.getLogger(__name__)

_QWEN_ENGINE_VALUES = {"qwen", "qwen2.5-vl", "ollama"}
_QWEN_VISION_PROMPT = (
    "You are an advanced Intelligent Document Processing vision engine. "
    "Analyze the provided image document carefully. "
    "Transcribe all visible text, numbers, headings, and tabular data exactly as they appear in the visual layout. "
    "Return ONLY the raw transcribed text. Do not wrap it in markdown code blocks, do not include conversational words, and do not explain your actions."
)


class OCRService:
    def __init__(self) -> None:
        self.engine = (config.OCR_ENGINE or "paddleocr").strip().lower()
        self.engine_display_name = config.OCR_ENGINE_DISPLAY_NAME
        self.qwen_analyzer = None

        logger.info("OCR_ENGINE env raw value: %s", os.getenv("OCR_ENGINE", "<unset>"))
        logger.info("OCR_ENGINE config value: %s", self.engine)
        logger.info("OCR service initialized with engine=%s", self.engine_display_name)

        if self.engine in _QWEN_ENGINE_VALUES:
            logger.info("OCR engine branch selected: Qwen")
            self.qwen_analyzer = self._initialize_qwen_analyzer()
        else:
            logger.info("OCR engine branch selected: PaddleOCR")

    def _initialize_qwen_analyzer(self):
        try:
            from quality_assessment.analyzer import LayoutAwareQualityAnalyzer

            analyzer = LayoutAwareQualityAnalyzer()
            logger.info(
                "Qwen analyzer initialized successfully base_url=%s model=%s",
                config.OLLAMA_BASE_URL,
                config.QWEN_VISION_MODEL,
            )
            return analyzer
        except Exception as exc:
            logger.exception("Failed to initialize Qwen analyzer")
            raise RuntimeError(
                "OCR_ENGINE=qwen was configured, but Qwen2.5-VL (Ollama) could not be initialized. "
                f"base_url={config.OLLAMA_BASE_URL}, model={config.QWEN_VISION_MODEL}. Error: {exc}"
            ) from exc

    def run_page_ocr(self, image_path: str, page_folder: Path) -> dict[str, Any]:
        logger.info(
            "Running OCR on image=%s selected_engine=%s",
            image_path,
            self.engine_display_name,
        )
        logger.info("OCR_ENGINE branch check: engine=%s qwen_enabled=%s", self.engine, self.engine in _QWEN_ENGINE_VALUES)

        if self.engine in _QWEN_ENGINE_VALUES:
            logger.info("Entering Qwen branch")
            return self._run_qwen_ocr(image_path, page_folder)

        logger.info("Entering PaddleOCR branch")
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
        if self.qwen_analyzer is None:
            raise RuntimeError("Qwen analyzer is not initialized. OCR_ENGINE=qwen cannot continue.")

        logger.info("Calling Qwen Vision LLM...")
        transcript = asyncio.run(
            self.qwen_analyzer.extract_via_vision_llm(
                image_path=image_path,
                target_prompt=_QWEN_VISION_PROMPT,
            )
        )
        logger.info("Qwen Vision response received.")

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
