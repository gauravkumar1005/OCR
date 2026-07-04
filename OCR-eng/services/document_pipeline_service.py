from __future__ import annotations

import asyncio
import json
import logging
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from OCR_Extraction_folder.image_preprocessing import preprocess_image
from OCR_Extraction_folder.layout_block_detection import detect_layout
from OCR_Extraction_folder.ocr_merge_engine import merge_page_blocks_ocr
from document_classify_it import classify_document
from project import config
from quality_assessment.analyzer import LayoutAwareQualityAnalyzer

from .ocr_service import OCRService
from .storage_service import StorageService

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class DocumentPipelineRequest:
    document_id: str
    pdf_path: Path
    output_root: Path
    document_type: str = "combined_document"


class DocumentPipeline:
    def __init__(
        self,
        *,
        ocr_service: OCRService | None = None,
        quality_analyzer: LayoutAwareQualityAnalyzer | None = None,
    ) -> None:
        self.ocr_service = ocr_service or OCRService()
        self.quality_analyzer = quality_analyzer or LayoutAwareQualityAnalyzer()
        self.storage_service = StorageService(Path(config.RESULT_DIR))

    def execute(self, document_request: dict[str, Any] | DocumentPipelineRequest) -> dict[str, Any]:
        request = self._normalize_request(document_request)
        logger.info("OCR pipeline received document_id=%s pdf_path=%s", request.document_id, request.pdf_path)
        logger.info("OCR pipeline output_root=%s document_type=%s", request.output_root, request.document_type)
        logger.info("Selected OCR Engine: %s", self.ocr_service.engine_display_name)

        folders = self._prepare_folders(request)

        logger.info("STEP 1 -> PDF TO IMAGES")
        image_paths = self._convert_pdf_to_images(request.pdf_path, folders["images"])
        logger.info("PDF to images completed document_id=%s page_count=%d", request.document_id, len(image_paths))

        processed_pages: list[dict[str, Any]] = []
        for idx, image_path in enumerate(image_paths, start=1):
            processed_pages.append(
                self._process_page(
                    request=request,
                    page_no=idx,
                    image_path=Path(image_path),
                    folders=folders,
                )
            )

        combined_output = self._merge_pages(request, processed_pages, folders)
        logger.info(
            "OCR pipeline completed document_id=%s page_count=%d",
            request.document_id,
            len(processed_pages),
        )
        return combined_output

    def _normalize_request(
        self,
        document_request: dict[str, Any] | DocumentPipelineRequest,
    ) -> DocumentPipelineRequest:
        if isinstance(document_request, DocumentPipelineRequest):
            return document_request

        pdf_path_value = document_request.get("pdf_path")
        output_root_value = document_request.get("output_root")
        document_id = (document_request.get("document_id") or "").strip()
        document_type = (document_request.get("document_type") or "combined_document").strip() or "combined_document"

        if not pdf_path_value:
            raise ValueError("pdf_path is required for document pipeline execution")
        if not output_root_value:
            raise ValueError("output_root is required for document pipeline execution")
        if not document_id:
            document_id = Path(str(pdf_path_value)).stem

        return DocumentPipelineRequest(
            document_id=document_id,
            pdf_path=Path(pdf_path_value),
            output_root=Path(output_root_value),
            document_type=document_type,
        )

    def _prepare_folders(self, request: DocumentPipelineRequest) -> dict[str, Path]:
        base_output = request.output_root
        folders = {
            "images": base_output / "01_images",
            "enhanced": base_output / "02_enhanced",
            "layout": base_output / "03_layout",
            "regions": base_output / "04_regions",
            "ocr": base_output / "05_ocr",
            "classification": base_output / "06_document_classification",
            "final": base_output / "07_final",
        }

        for folder in folders.values():
            folder.mkdir(parents=True, exist_ok=True)

        return folders

    def _convert_pdf_to_images(self, pdf_path: Path, image_root: Path) -> list[str]:
        from OCR_Extraction_folder.pdf_converter import convert_pdf_to_images

        logger.info("Converting PDF to images at %s", image_root)
        return convert_pdf_to_images(str(pdf_path), str(image_root))

    def _process_page(
        self,
        *,
        request: DocumentPipelineRequest,
        page_no: int,
        image_path: Path,
        folders: dict[str, Path],
    ) -> dict[str, Any]:
        try:
            logger.info("======================================================================")
            logger.info("PROCESSING PAGE %d", page_no)
            logger.info("======================================================================")

            logger.info("STEP 2 -> PREPROCESSING")
            enhanced_image = Path(preprocess_image(str(image_path), str(folders["enhanced"])))
            logger.info("Preprocessing completed page=%d enhanced_image=%s", page_no, enhanced_image)

            logger.info("STEP 3 -> LAYOUT DETECTION")
            layout_result = detect_layout(
                image_path=str(enhanced_image),
                layout_output_folder=str(folders["layout"]),
                cropped_output_folder=str(folders["regions"]),
            )
            cropped_regions = layout_result.get("cropped_regions", [])
            logger.info(
                "Layout detection completed page=%d cropped_regions=%d",
                page_no,
                len(cropped_regions),
            )

            logger.info("STEP 4 -> IMAGE QUALITY ASSESSMENT")
            quality_report = self.quality_analyzer.analyze(
                image_path=str(enhanced_image),
                layout_result=layout_result,
            )
            logger.info("-> Overall Weighted Score: %s/100", quality_report.overall_score)
            logger.info("-> Module Internal Recommendation: %s", quality_report.recommendation.value)

            should_run_ocr = False
            should_run_text_llm = False
            should_run_vision_llm = False

            is_too_noisy = quality_report.noise.normalized_score < 50.0
            is_blurry = quality_report.blur.normalized_score < 60.0
            is_soft_edges = quality_report.edge_sharpness.normalized_score < 60.0

            raw_text = ""
            final_raw_text_output = ""
            selected_ocr_result: dict[str, Any] = {}

            if quality_report.is_blank:
                logger.info("-> [ROUTE: BLANK_PAGE] Empty page. Bypassing processing chains.")
                selected_ocr_result = {
                    "engine": "blank_page",
                    "text": "",
                    "full_text": "",
                    "ocr_data": [],
                }
            elif is_too_noisy or is_blurry or is_soft_edges:
                logger.info("-> [ROUTE: VISION_LLM OVERRIDE] Specific metric point failure detected!")
                if is_too_noisy:
                    logger.info("  Point Failure: Image contains excessive background noise.")
                if is_blurry:
                    logger.info("  Point Failure: Image text is too blurry.")
                if is_soft_edges:
                    logger.info("  Point Failure: Text edge definition is too soft.")
                should_run_vision_llm = True
            else:
                logger.info(
                    "-> [ROUTE: OCR STANDARD] Quality verified (%s). Activating OCR pathway.",
                    quality_report.overall_score,
                )
                should_run_ocr = True
                should_run_text_llm = True

            if should_run_ocr:
                logger.info("STEP 5 -> FULL PAGE OCR")
                selected_ocr_result = self.ocr_service.run_page_ocr(
                    str(enhanced_image),
                    folders["ocr"],
                )
                raw_text = self._extract_text(selected_ocr_result)
                txt_output_path = folders["ocr"] / f"{image_path.stem}_raw.txt"
                txt_output_path.write_text(raw_text, encoding="utf-8")
                logger.info("-> [FILE WRITER] Raw OCR text saved successfully to: %s", txt_output_path)

                alphanumeric_chars = sum(1 for char in raw_text if char.isalnum())
                total_chars = max(1, len(raw_text.strip()))
                alphanumeric_ratio = alphanumeric_chars / total_chars

                if len(raw_text.strip()) < 45 or alphanumeric_ratio < 0.40:
                    logger.info(
                        "[OCR CHECK FAILURE] String has a poor alphanumeric ratio (%s). Text is corrupted noise.",
                        round(alphanumeric_ratio, 2),
                    )
                    logger.info("-> Rerouting page execution flow directly to local Vision LLM fallback.")
                    should_run_vision_llm = True
                    should_run_text_llm = False
                else:
                    logger.info("[OCR QUALITY CHECK] Healthy alphanumeric text output validated.")
                    should_run_text_llm = True

            if should_run_text_llm:
                logger.info("STEP 6 -> PROCESSING STANDARD PATHWAY TEXT")
                final_raw_text_output = raw_text
            elif should_run_vision_llm:
                logger.info("STEP 6 -> RUNNING PIXEL-BASED LOCAL VISION TEXT RECONSTRUCTION")
                logger.info("IMAGE = %s", image_path)
                logger.info("Calling Qwen Vision LLM...")
                vision_response = asyncio.run(
                    self.quality_analyzer.extract_via_vision_llm(
                        image_path=str(enhanced_image),
                        target_prompt=(
                            "You are an advanced Intelligent Document Processing vision engine. "
                            "Analyze the provided image document carefully. "
                            "Transcribe all visible text, numbers, headings, and tabular data exactly as they appear in the visual layout. "
                            "Return ONLY the raw transcribed text. Do not wrap it in markdown code blocks, do not include conversational words, and do not explain your actions."
                        ),
                    )
                )
                final_raw_text_output = vision_response if isinstance(vision_response, str) else str(vision_response)
                selected_ocr_result = {
                    "engine": "qwen2.5-vl-ollama",
                    "model": config.QWEN_VISION_MODEL,
                    "source_image": str(enhanced_image),
                    "text": final_raw_text_output,
                    "full_text": final_raw_text_output,
                    "ocr_data": [],
                }
                logger.info("Qwen Vision response received.")
                logger.info("-> [SUCCESS] Local QWEN has reconstructed clean text directly from the image layout.")

            if final_raw_text_output.strip():
                txt_output_path = folders["ocr"] / f"{image_path.stem}_raw.txt"
                txt_output_path.write_text(final_raw_text_output.strip(), encoding="utf-8")
                logger.info("-> [FILE WRITER] Clean raw text saved successfully to: %s", txt_output_path)
                logger.info("-> Ready for your downstream JSON processing function.")

            if selected_ocr_result and selected_ocr_result.get("engine") == "qwen2.5-vl-ollama":
                page_ocr_json_path = folders["ocr"] / f"{image_path.stem}_ocr.json"
                page_ocr_json_path.write_text(
                    json.dumps(selected_ocr_result, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
                logger.info("OCR JSON written to %s", page_ocr_json_path)

            classification_input = final_raw_text_output if final_raw_text_output.strip() else raw_text
            classification = classify_document(classification_input)
            document_type = classification["document_type"]

            classification_file = folders["classification"] / f"page_{page_no}.json"
            classification_file.write_text(
                json.dumps(classification, indent=4, ensure_ascii=False),
                encoding="utf-8",
            )
            logger.info("Classification saved -> %s", classification_file)

            final_json_path = folders["final"] / f"page_{page_no}_final.json"
            page_json_output = {
                "page_number": page_no,
                "document_id": request.document_id,
                "document_type": document_type,
                "classification": classification,
                "quality_report": quality_report.to_dict(),
                "layout_result": layout_result,
                "raw_text": raw_text,
                "final_raw_text_output": final_raw_text_output,
                "selected_ocr_result": selected_ocr_result,
                "source_image": str(image_path),
                "enhanced_image": str(enhanced_image),
                "document_type_requested": request.document_type,
            }
            self.storage_service.write_json(final_json_path, page_json_output)
            logger.info("Page final JSON saved -> %s", final_json_path)

            return {
                "page_number": page_no,
                "image_path": str(image_path),
                "enhanced_image": str(enhanced_image),
                "ocr_json_path": str(folders["ocr"] / f"{image_path.stem}_ocr.json"),
                "generated_json": selected_ocr_result,
                "classification": classification,
                "quality_report": quality_report.to_dict(),
                "raw_text": raw_text,
                "final_raw_text_output": final_raw_text_output,
                "document_type": document_type,
                "page_json_path": str(final_json_path),
            }
        except Exception as exc:
            logger.error("❌ Error processing Page %d: %s", page_no, exc)
            logger.error(traceback.format_exc())
            return {
                "page_number": page_no,
                "image_path": str(image_path),
                "error": str(exc),
            }

    def _merge_pages(
        self,
        request: DocumentPipelineRequest,
        processed_pages: list[dict[str, Any]],
        folders: dict[str, Path],
    ) -> dict[str, Any]:
        combined_text = "\n\n".join(
            str(page.get("final_raw_text_output") or page.get("raw_text") or "")
            for page in processed_pages
        ).strip()

        merged_regions: list[dict[str, Any]] = []
        for page in processed_pages:
            generated_json = page.get("generated_json") or {}
            if generated_json:
                merged_regions.append({"type": "full_page", "ocr": generated_json})

        merged_page_block = (
            merge_page_blocks_ocr(merged_regions)
            if merged_regions
            else {"ocr_data": [], "text": combined_text}
        )

        combined_output = {
            "document_id": request.document_id,
            "document_type": request.document_type,
            "page_count": len(processed_pages),
            "pages": processed_pages,
            "combined_text": merged_page_block.get("text", combined_text),
            "merged_ocr": merged_page_block,
        }

        output_path = folders["final"] / f"{request.document_id}_ocr_output.json"
        self.storage_service.write_json(output_path, combined_output)
        logger.info("Merged OCR output saved -> %s", output_path)
        return combined_output

    @staticmethod
    def _extract_text(ocr_result: dict[str, Any]) -> str:
        if not isinstance(ocr_result, dict):
            return str(ocr_result)
        return str(ocr_result.get("text") or ocr_result.get("full_text") or ocr_result.get("raw_output") or "")
