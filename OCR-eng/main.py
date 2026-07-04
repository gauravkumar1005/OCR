from __future__ import annotations

import logging
from pathlib import Path

from services.document_pipeline import DocumentPipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

PDF_PATH = Path("TEST_PDF/MEDSAVE.pdf")
BASE_OUTPUT = Path("RESULT") / PDF_PATH.stem


def main() -> None:
    pipeline = DocumentPipeline()
    result = pipeline.execute(
        {
            "document_id": PDF_PATH.stem,
            "document_type": "combined_document",
            "pdf_path": PDF_PATH,
            "output_root": BASE_OUTPUT,
        }
    )

    logger.info("Main pipeline completed document_id=%s page_count=%s", result.get("document_id"), result.get("page_count"))
    logger.info("Output directory: %s", BASE_OUTPUT)


if __name__ == "__main__":
    main()
