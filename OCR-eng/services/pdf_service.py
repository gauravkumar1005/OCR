from __future__ import annotations

import logging
from pathlib import Path

from OCR_Extraction_folder.pdf_converter import convert_pdf_to_images

logger = logging.getLogger(__name__)


class PDFService:
    def convert_pdf_to_images(self, pdf_path: Path, image_root: Path) -> list[str]:
        logger.info("Converting PDF to images at %s", image_root)
        return convert_pdf_to_images(str(pdf_path), str(image_root))
