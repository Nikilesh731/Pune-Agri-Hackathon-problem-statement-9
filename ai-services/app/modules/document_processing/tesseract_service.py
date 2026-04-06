"""
Tesseract OCR service for image text extraction.
"""
from typing import List
import io
import logging

from app.modules.document_processing.runtime_health import (
    get_available_tesseract_languages,
    get_tesseract_config,
    resolve_tesseract_binary,
)


class TesseractService:
    """Tesseract-based OCR service for image text extraction."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("[OCR] Tesseract service initialized")

    def _resolve_tesseract_binary(self):
        return resolve_tesseract_binary()

    def _get_ocr_language_candidates(self) -> List[str]:
        available_languages = set(get_available_tesseract_languages())
        preferred_languages = [language for language in ("eng", "hin", "mar") if language in available_languages]

        if preferred_languages:
            candidates = ["+".join(preferred_languages)]
        else:
            candidates = ["eng"]

        if "eng" not in preferred_languages:
            candidates.append("eng")

        return list(dict.fromkeys(candidates))

    def extract_text_from_image_bytes(self, file_content: bytes, filename: str) -> str:
        """Extract text from image bytes using Tesseract OCR."""
        import pytesseract
        from PIL import Image
        import PIL.ImageEnhance

        tesseract_path = self._resolve_tesseract_binary()
        if not tesseract_path:
            raise ValueError("OCR_FAILURE: Tesseract binary not found")

        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        self.logger.info(f"[OCR] Using Tesseract at: {tesseract_path}")

        try:
            image = Image.open(io.BytesIO(file_content))

            if image.mode != "RGB":
                image = image.convert("RGB")

            enhancer = PIL.ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)

            gray_image = image.convert("L")

            try:
                import numpy as np

                img_array = np.array(gray_image)
                threshold = 128
                img_array = np.where(img_array > threshold, 255, 0).astype(np.uint8)
                processed_image = Image.fromarray(img_array, mode="L")
            except ImportError:
                processed_image = gray_image.point(lambda x: 0 if x < 128 else 255, mode="1")

            try:
                tesseract_config = get_tesseract_config()
                language_candidates = self._get_ocr_language_candidates()

                extracted_text = ""
                selected_language = ""
                last_language_error = None

                for language_code in language_candidates:
                    try:
                        if tesseract_config:
                            extracted_text = pytesseract.image_to_string(
                                processed_image,
                                lang=language_code,
                                config=tesseract_config,
                            )
                        else:
                            extracted_text = pytesseract.image_to_string(
                                processed_image,
                                lang=language_code,
                            )
                        selected_language = language_code
                        break
                    except Exception as lang_error:
                        last_language_error = lang_error
                        self.logger.warning(f"[OCR] OCR failed with {language_code}, trying fallback: {lang_error}")

                if not extracted_text.strip() and last_language_error is not None:
                    raise last_language_error

                self.logger.info(f"[OCR] OCR completed for {filename} using {selected_language or 'eng'}")
            except Exception as lang_error:
                self.logger.warning(f"[OCR] OCR language fallback failed for {filename}: {lang_error}")
                if get_tesseract_config():
                    extracted_text = pytesseract.image_to_string(processed_image, lang="eng", config=get_tesseract_config())
                else:
                    extracted_text = pytesseract.image_to_string(processed_image, lang="eng")

            text_length = len(extracted_text.strip())

            if text_length == 0:
                raise ValueError("OCR failed: no text could be extracted from image")

            if text_length < 20:
                self.logger.warning(f"[OCR] Very low text extraction from image {filename}: {text_length} chars")
                extracted_text = f"[LOW_OCR_QUALITY] {extracted_text.strip()}"

            ocr_error_patterns = [
                "|||||||",
                "||||||",
                "|||||",
                "||||",
                "_____",
                "____",
                "___",
                "[illegible]",
                "[unreadable]",
                "[unclear]",
            ]

            for pattern in ocr_error_patterns:
                if pattern in extracted_text.lower():
                    self.logger.warning(f"[OCR] Detected handwriting pattern '{pattern}' in {filename}")
                    extracted_text = f"[HANDWRITING_DETECTED] {extracted_text.strip()}"
                    break

            self.logger.info(f"[OCR] Image OCR extraction complete: {text_length} chars")
            return extracted_text.strip()

        except Exception as ocr_error:
            self.logger.error(f"[OCR] Tesseract OCR processing failed: {ocr_error}")
            raise ValueError(f"OCR_FAILURE: Tesseract extraction failed - {str(ocr_error)}")