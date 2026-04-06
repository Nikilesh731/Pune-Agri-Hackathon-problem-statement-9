"""
Document Ingestion Service
Purpose: Document parsing using PyMuPDF + OCR with stable dependency stack
"""
import logging
import os
import shutil
import tempfile
import json
import re
from typing import Dict, Any, Optional, List
from pathlib import Path
import uuid

try:
    import pytesseract
    from PIL import Image
    import cv2
    import numpy as np
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


class GraniteDoclingService:
    """
    Document ingestion service using PyMuPDF + OCR
    
    This service provides:
    - PyMuPDF-based document parsing
    - Tesseract OCR for images and scanned PDFs
    - OCR fallback when needed
    - Clean JSON response format
    - Production-safe error handling
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._ocr_available = None
        self._ocr_languages_available = []
        self._tesseract_path = None
        
        # Check OCR availability
        self._check_ocr_availability()
    
    def _check_ocr_availability(self):
        """Check if OCR (Tesseract) is available"""
        if OCR_AVAILABLE:
            try:
                self._tesseract_path = self._resolve_tesseract_binary()
                if not self._tesseract_path:
                    self._ocr_available = False
                    self.logger.info("[OCR] Tesseract unavailable (fallback disabled)")
                    return

                if os.name == "nt":
                    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
                elif self._tesseract_path:
                    pytesseract.pytesseract.tesseract_cmd = self._tesseract_path
                pytesseract.get_tesseract_version()
                self._ocr_available = True
                try:
                    self._ocr_languages_available = pytesseract.get_languages(config="") or []
                except Exception:
                    self._ocr_languages_available = []
                self.logger.info(f"[OCR] Tesseract available at {self._tesseract_path}")
            except Exception as e:
                self.logger.info(f"[OCR] Tesseract unavailable (fallback disabled): {e}")
                self._ocr_available = False
        else:
            self.logger.info("[OCR] OCR dependencies not installed (fallback disabled)")
            self._ocr_available = False

    def _resolve_tesseract_binary(self) -> Optional[str]:
        """Resolve Tesseract on Windows or from PATH."""
        try:
            current_path = getattr(pytesseract.pytesseract, "tesseract_cmd", "") or shutil.which("tesseract")
            if current_path:
                pytesseract.pytesseract.tesseract_cmd = current_path
                pytesseract.get_tesseract_version()
                return current_path
        except Exception:
            pass

        windows_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        if os.path.exists(windows_path):
            try:
                pytesseract.pytesseract.tesseract_cmd = windows_path
                pytesseract.get_tesseract_version()
                return windows_path
            except Exception:
                return None

        return None

    def _detect_file_type(self, filename: str) -> str:
        """Detect file type from filename"""
        if not filename:
            return "unknown"
        extension = Path(filename).suffix.lower()
        type_mapping = {
            '.pdf': 'pdf',
            '.jpg': 'image',
            '.jpeg': 'image',
            '.png': 'image',
            '.tiff': 'image',
            '.bmp': 'image',
        }
        return type_mapping.get(extension, 'unknown')

    def _detect_source_type(self, filename: str) -> str:
        return self._detect_file_type(filename)

    def _safe_text(self, value: Any) -> str:
        return value if isinstance(value, str) else ""

    def _safe_list(self, value: Any) -> List[Any]:
        return value if isinstance(value, list) else []

    def _safe_dict(self, value: Any) -> Dict[str, Any]:
        return value if isinstance(value, dict) else {}

    def _flatten_text(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        if isinstance(value, (int, float, bool)):
            return str(value)
        if isinstance(value, dict):
            parts = [self._flatten_text(item) for item in value.values()]
            return " ".join(part for part in parts if part).strip()
        if isinstance(value, list):
            parts = [self._flatten_text(item) for item in value]
            return " ".join(part for part in parts if part).strip()
        return str(value)

    def _quality_issues(self, raw_text: str) -> List[str]:
        issues: List[str] = []
        text = re.sub(r"\s+", " ", raw_text or "").strip()

        if not text:
            issues.append("empty_text")
            return issues

        if len(text) < 50:
            issues.append("very_short_text")

        alpha_count = sum(1 for char in text if char.isalpha())
        symbol_count = sum(1 for char in text if not char.isalnum() and not char.isspace())
        if alpha_count < 5:
            issues.append("too_little_alphabetic_content")
        if symbol_count > max(10, int(len(text) * 0.4)):
            issues.append("mostly_symbols")

        return issues

    def _is_text_quality_good(self, raw_text: str) -> bool:
        return len(self._quality_issues(raw_text)) == 0

    def _is_text_quality_poor(self, raw_text: str) -> bool:
        text = re.sub(r"\s+", " ", raw_text or "").strip()
        if not text or len(text) < 50:
            return True
        issues = self._quality_issues(raw_text)
        return any(issue in {"too_little_alphabetic_content", "mostly_symbols"} for issue in issues) or not self._is_text_quality_good(raw_text)

    def _merge_text_content(self, primary_text: str, secondary_text: str) -> str:
        primary_lines = [line.strip() for line in (primary_text or "").splitlines() if line.strip()]
        secondary_lines = [line.strip() for line in (secondary_text or "").splitlines() if line.strip()]
        merged_lines: List[str] = []
        seen_lines = set()

        for line in primary_lines + secondary_lines:
            normalized = re.sub(r"\s+", " ", line).strip()
            if not normalized or normalized in seen_lines:
                continue
            seen_lines.add(normalized)
            merged_lines.append(line)

        if not merged_lines:
            return (primary_text or secondary_text or "").strip()

        return "\n".join(merged_lines).strip()

    def _merge_structured_items(self, primary_items: List[Dict[str, Any]], secondary_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        merged_items: List[Dict[str, Any]] = []
        seen_signatures = set()

        for item in primary_items + secondary_items:
            if not isinstance(item, dict):
                continue
            signature = (
                item.get("page_number"),
                item.get("block_number"),
                re.sub(r"\s+", " ", self._flatten_text(item.get("text", ""))).strip(),
            )
            if signature in seen_signatures:
                continue
            seen_signatures.add(signature)
            merged_items.append(item)

        return merged_items

    def _build_metadata(self, file_type: str, raw_text: str, pages: List[Dict[str, Any]], blocks: List[Dict[str, Any]], tables: List[Dict[str, Any]], parser: str) -> Dict[str, Any]:
        return {
            "file_type": file_type,
            "processing_method": parser,
            "text_length": len(raw_text),
            "page_count": len(pages),
            "has_tables": len(tables) > 0,
            "has_blocks": len(blocks) > 0,
            "warnings": [],
            "ocr_languages_available": self._ocr_languages_available,
        }

    def _create_temp_file(self, file_data: bytes, filename: str) -> str:
        """Create temporary file for processing"""
        temp_dir = tempfile.gettempdir()
        temp_filename = f"granite_docling_{uuid.uuid4().hex}_{filename}"
        temp_path = os.path.join(temp_dir, temp_filename)
        
        try:
            with open(temp_path, 'wb') as f:
                f.write(file_data)
            return temp_path
        except Exception as e:
            self.logger.error(f"[TEMP] Failed to create temp file: {e}")
            raise ValueError(f"Failed to create temporary file: {e}")
    
    def _cleanup_temp_file(self, temp_path: str):
        """Clean up temporary file"""
        try:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        except Exception as e:
            self.logger.warning(f"[TEMP] Failed to cleanup temp file {temp_path}: {e}")

    def _extract_with_pymupdf(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """Extract text from PDF using PyMuPDF"""
        try:
            import fitz
        except ImportError:
            raise ValueError("PyMuPDF not available")
        
        try:
            self.logger.info(f"[PYMUPDF] Processing {file_type} file")
            doc = fitz.open(file_path)
            pages: List[Dict[str, Any]] = []
            blocks: List[Dict[str, Any]] = []
            raw_parts: List[str] = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                page_text = page.get_text()
                if page_text and page_text.strip():
                    raw_parts.append(page_text.strip())
                    pages.append({
                        "page_number": page_num + 1,
                        "text": page_text.strip(),
                    })
                    blocks.append({
                        "block_number": page_num + 1,
                        "type": "text",
                        "text": page_text.strip(),
                        "page_number": page_num + 1
                    })
            
            doc.close()
            raw_text = "\n".join(raw_parts).strip()
            
            return {
                "raw_text": raw_text,
                "pages": pages,
                "blocks": blocks,
                "tables": [],
                "metadata": self._build_metadata(file_type, raw_text, pages, blocks, [], "pymupdf"),
            }
            
        except Exception as e:
            self.logger.error(f"[PYMUPDF] Extraction failed: {e}")
            raise ValueError(f"PyMuPDF extraction failed: {e}")
    
    def _extract_with_ocr(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """Extract text using OCR fallback"""
        if not self._ocr_available:
            raise ValueError("OCR not available")
        
        try:
            self.logger.info(f"[OCR] Processing {file_type} file")
            if file_type == 'image':
                image = Image.open(file_path)
                return self._ocr_image(image, os.path.basename(file_path))

            if file_type == 'pdf':
                return self._ocr_pdf(file_path, os.path.basename(file_path))

            raise ValueError(f"OCR fallback is not supported for file type: {file_type}")
            
        except Exception as e:
            self.logger.error(f"[OCR] Extraction failed: {e}")
            raise ValueError(f"OCR extraction failed: {e}")

    def _get_available_ocr_languages(self) -> List[str]:
        if not self._ocr_available:
            return []

        if self._ocr_languages_available:
            return self._ocr_languages_available

        try:
            self._ocr_languages_available = pytesseract.get_languages(config="") or []
        except Exception:
            self._ocr_languages_available = []
        return self._ocr_languages_available

    def _get_ocr_language_candidates(self) -> List[str]:
        available_languages = set(self._get_available_ocr_languages())

        preferred = []
        for lang in ["eng", "hin", "mar"]:
            if lang in available_languages:
                preferred.append(lang)

        if preferred:
            return ["+".join(preferred)]

        return ["eng"]

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        from PIL import ImageFilter, ImageOps

        if image.mode not in ("L", "RGB"):
            image = image.convert("RGB")

        image = ImageOps.grayscale(image)
        image = ImageOps.autocontrast(image)
        image = image.filter(ImageFilter.MedianFilter(size=3))
        return image.point(lambda value: 0 if value < 160 else 255, mode="1")

    def _ocr_image(self, image: Image.Image, filename: str, page_number: Optional[int] = None) -> Dict[str, Any]:
        if not self._ocr_available:
            raise ValueError("OCR not available")

        processed_image = self._preprocess_image(image)
        language_candidates = self._get_ocr_language_candidates()
        attempted_languages: List[str] = []
        used_language = ""

        extracted_text = ""
        last_error: Optional[Exception] = None
        for language in language_candidates:
            attempted_languages.append(language)
            try:
                extracted_text = pytesseract.image_to_string(processed_image, lang=language)
                used_language = language
                break
            except Exception as exc:
                last_error = exc
                if language != "eng":
                    self.logger.warning(f"[OCR] language fallback triggered for {filename}: {exc}")

        if not extracted_text.strip() and last_error is not None:
            raise ValueError(f"OCR failed: {last_error}")

        extracted_text = re.sub(r"\s+", " ", extracted_text).strip()
        page_index = page_number or 1
        return {
            "raw_text": extracted_text,
            "pages": [{"page_number": page_index, "text": extracted_text}],
            "blocks": [{"block_number": 1, "type": "ocr_text", "text": extracted_text, "page_number": page_index}],
            "tables": [],
            "metadata": {
                "file_type": self._detect_source_type(filename),
                "processing_method": "ocr",
                "text_length": len(extracted_text),
                "page_count": 1,
                "has_tables": False,
                "has_blocks": True,
                "ocr_languages_attempted": attempted_languages,
                "ocr_languages_used": [used_language] if used_language else [],
                "ocr_languages_available": self._get_available_ocr_languages(),
                "warnings": [],
            },
        }

    def _extract_pdf_page_images(self, file_path: str) -> List[Image.Image]:
        try:
            import fitz
        except Exception as exc:
            raise ValueError(f"PDF rendering support unavailable: {exc}")

        images: List[Image.Image] = []
        document = fitz.open(file_path)
        try:
            for page_number in range(len(document)):
                page = document.load_page(page_number)
                pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
                images.append(image)
        finally:
            document.close()
        return images

    def _ocr_pdf(self, file_path: str, filename: str) -> Dict[str, Any]:
        page_images = self._extract_pdf_page_images(file_path)
        page_results: List[Dict[str, Any]] = []
        blocks: List[Dict[str, Any]] = []
        raw_parts: List[str] = []
        attempted_languages: List[str] = []
        used_languages: List[str] = []

        for index, page_image in enumerate(page_images, start=1):
            page_result = self._ocr_image(page_image, filename, page_number=index)
            page_results.extend(page_result["pages"])
            blocks.extend(page_result["blocks"])
            if page_result["raw_text"]:
                raw_parts.append(page_result["raw_text"])
            attempted_languages.extend(page_result["metadata"].get("ocr_languages_attempted", []))
            used_languages.extend(page_result["metadata"].get("ocr_languages_used", []))

        raw_text = "\n".join(part for part in raw_parts if part).strip()
        metadata = {
            "file_type": "pdf",
            "processing_method": "ocr",
            "text_length": len(raw_text),
            "page_count": len(page_results),
            "has_tables": False,
            "has_blocks": len(blocks) > 0,
            "ocr_languages_attempted": list(dict.fromkeys(attempted_languages)),
            "ocr_languages_used": list(dict.fromkeys(used_languages)),
            "ocr_languages_available": self._get_available_ocr_languages(),
            "warnings": [],
        }

        return {
            "raw_text": raw_text,
            "pages": page_results,
            "blocks": blocks,
            "tables": [],
            "metadata": metadata,
        }
    
    def _build_ocr_failure_response(
        self,
        file_type: str,
        errors: List[str],
        warnings: List[str],
        pymupdf_result: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        base_result = pymupdf_result or {
            "raw_text": "",
            "pages": [],
            "blocks": [],
            "tables": [],
            "metadata": {},
        }

        response = {
            "success": bool(pymupdf_result),
            "source_type": file_type,
            "parser": "pymupdf" if pymupdf_result else "none",
            "raw_text": base_result.get("raw_text", ""),
            "pages": base_result.get("pages", []),
            "blocks": base_result.get("blocks", []),
            "tables": base_result.get("tables", []),
            "metadata": dict(base_result.get("metadata", {})),
            "ocr_used": True,
            "fallback_used": True,
            "errors": errors,
            "risk_flags": [
                {
                    "code": "OCR_FAILURE",
                    "severity": "high",
                    "message": "OCR fallback failed after low-quality initial extraction",
                }
            ],
            "decision_support": {
                "decision": "manual_review_required",
                "confidence": 0.0,
                "reasoning": ["OCR fallback failed after low-quality initial extraction"],
            },
        }

        response_metadata = response["metadata"]
        response_metadata["warnings"] = warnings
        response_metadata["ocr_fallback_failed"] = True
        response_metadata["ocr_used"] = True
        response_metadata["fallback_used"] = True
        response["metadata"] = response_metadata

        return response

    def _merge_extraction_results(self, primary_result: Dict[str, Any], secondary_result: Dict[str, Any]) -> Dict[str, Any]:
        merged_result = dict(primary_result)
        merged_result["raw_text"] = self._merge_text_content(primary_result.get("raw_text", ""), secondary_result.get("raw_text", ""))
        merged_result["pages"] = self._merge_structured_items(primary_result.get("pages", []), secondary_result.get("pages", []))
        merged_result["blocks"] = self._merge_structured_items(primary_result.get("blocks", []), secondary_result.get("blocks", []))
        if not merged_result.get("tables") and secondary_result.get("tables"):
            merged_result["tables"] = secondary_result.get("tables", [])

        metadata = dict(merged_result.get("metadata", {}))
        metadata["ocr_fallback_used"] = True
        metadata["ocr_text_length"] = len(secondary_result.get("raw_text", ""))
        warnings = list(metadata.get("warnings", []))
        if "ocr_fallback_used" not in warnings:
            warnings.append("ocr_fallback_used")
        metadata["warnings"] = warnings
        merged_result["metadata"] = metadata

        return merged_result
    
    def _check_text_quality(self, text: str) -> bool:
        """Check if extracted text quality is sufficient"""
        if not text or not text.strip():
            return False
        
        text = text.strip()
        
        # Check minimum length
        if len(text) < 20:
            return False
        
        # Check if text contains meaningful content
        alpha_chars = sum(1 for c in text if c.isalpha())
        if alpha_chars < 5:
            return False

        symbol_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())
        if symbol_chars > max(10, int(len(text) * 0.4)):
            return False
        
        return True
    
    def parse_document(self, file_path: str) -> Dict[str, Any]:
        """
        Parse document using PyMuPDF first, OCR fallback if needed
        
        Args:
            file_path: Local file path to the document
            
        Returns:
            Structured JSON response in the specified format
        """
        filename = os.path.basename(file_path)
        file_type = self._detect_source_type(filename)
        
        if file_type == 'unknown':
            return {
                "success": False,
                "source_type": "unknown",
                "parser": "none",
                "raw_text": "",
                "pages": [],
                "blocks": [],
                "tables": [],
                "metadata": {},
                "ocr_used": False,
                "fallback_used": False,
                "errors": [f"Unsupported file type: {filename}"]
            }
        
        errors: List[str] = []
        warnings: List[str] = []
        ocr_used = False
        fallback_used = False
        primary_result: Optional[Dict[str, Any]] = None
        primary_quality_poor = False
        
        # Try PyMuPDF first for PDFs, direct image loading for images
        if file_type == 'pdf':
            try:
                self.logger.info(f"[PARSER] Starting PyMuPDF parsing for {filename}")
                primary_result = self._extract_with_pymupdf(file_path, file_type)
                primary_quality_poor = self._is_text_quality_poor(primary_result.get('raw_text', ''))

                # Check text quality
                if not primary_quality_poor:
                    self.logger.info(f"[PARSER] PyMuPDF parsing successful for {filename}")
                    metadata = primary_result.get("metadata", {})
                    metadata.setdefault("warnings", warnings)
                    return {
                        "success": True,
                        "source_type": file_type,
                        "parser": "pymupdf",
                        "raw_text": primary_result['raw_text'],
                        "pages": primary_result['pages'],
                        "blocks": primary_result['blocks'],
                        "tables": primary_result['tables'],
                        "metadata": metadata,
                        "ocr_used": False,
                        "fallback_used": False,
                        "errors": []
                    }
                else:
                    self.logger.warning(f"[PARSER] PyMuPDF low quality for {filename}")
                    warnings.append("PyMuPDF extraction quality poor")
                    errors.append("PyMuPDF extraction quality poor")
                    
            except Exception as e:
                self.logger.error(f"[PARSER] PyMuPDF failed for {filename}: {e}")
                errors.append(f"PyMuPDF failed: {str(e)}")
        elif file_type == 'image':
            try:
                self.logger.info(f"[PARSER] Loading image for {filename}")
                image = Image.open(file_path)
                primary_result = self._ocr_image(image, filename)
                if self._check_text_quality(primary_result.get('raw_text', '')):
                    self.logger.info(f"[PARSER] Direct image OCR successful for {filename}")
                    metadata = primary_result.get("metadata", {})
                    metadata.setdefault("warnings", warnings)
                    return {
                        "success": True,
                        "source_type": file_type,
                        "parser": "ocr",
                        "raw_text": primary_result['raw_text'],
                        "pages": primary_result['pages'],
                        "blocks": primary_result['blocks'],
                        "tables": primary_result['tables'],
                        "metadata": metadata,
                        "ocr_used": True,
                        "fallback_used": False,
                        "errors": []
                    }
                primary_quality_poor = True
                errors.append("Image OCR quality poor")
            except Exception as e:
                self.logger.error(f"[PARSER] Image processing failed for {filename}: {e}")
                errors.append(f"Image processing failed: {str(e)}")
        
        # Fallback to OCR if primary method failed or produced poor quality
        if self._ocr_available and primary_quality_poor:
            try:
                self.logger.info(f"[PARSER] Starting OCR fallback for {filename}")
                ocr_result = self._extract_with_ocr(file_path, file_type)
                ocr_used = True
                fallback_used = True

                # Check OCR text quality
                if self._check_text_quality(ocr_result['raw_text']):
                    self.logger.info(f"[PARSER] OCR fallback successful for {filename}")
                    if primary_result:
                        merged_result = self._merge_extraction_results(primary_result, ocr_result)
                        metadata = merged_result.get("metadata", {})
                        metadata.setdefault("warnings", warnings)
                        metadata["ocr_used"] = True
                        metadata["fallback_used"] = True
                        if primary_quality_poor:
                            warnings.append("OCR fallback used after low-quality initial extraction")
                            metadata["warnings"] = warnings
                        return {
                            "success": True,
                            "source_type": file_type,
                            "parser": file_type if file_type == 'image' else "ocr",
                            "raw_text": merged_result['raw_text'],
                            "pages": merged_result['pages'],
                            "blocks": merged_result['blocks'],
                            "tables": merged_result['tables'],
                            "metadata": metadata,
                            "ocr_used": True,
                            "fallback_used": True,
                            "errors": errors
                        }

                    metadata = ocr_result.get("metadata", {})
                    metadata.setdefault("warnings", warnings)
                    return {
                        "success": True,
                        "source_type": file_type,
                        "parser": "ocr",
                        "raw_text": ocr_result['raw_text'],
                        "pages": ocr_result['pages'],
                        "blocks": ocr_result['blocks'],
                        "tables": ocr_result['tables'],
                        "metadata": metadata,
                        "ocr_used": True,
                        "fallback_used": True,
                        "errors": errors
                    }
                else:
                    self.logger.error(f"[PARSER] OCR text quality poor for {filename}")
                    errors.append("OCR extraction quality poor")
                    
            except Exception as e:
                self.logger.error(f"[PARSER] OCR fallback failed for {filename}: {e}")
                errors.append(f"OCR failed: {str(e)}")
                if primary_result:
                    return self._build_ocr_failure_response(file_type, errors, warnings, primary_result)
        else:
            if self._ocr_available:
                errors.append("OCR not needed - primary extraction succeeded")
            else:
                errors.append("OCR not available")
                if primary_result:
                    return self._build_ocr_failure_response(file_type, errors, warnings, primary_result)
        
        # Both methods failed
        self.logger.error(f"[PARSER] All extraction methods failed for {filename}")
        return {
            "success": False,
            "source_type": file_type,
            "parser": "none",
            "raw_text": "",
            "pages": [],
            "blocks": [],
            "tables": [],
            "metadata": {
                "file_type": file_type,
                "processing_method": "none",
                "text_length": 0,
                "page_count": 0,
                "has_tables": False,
                "has_blocks": False,
                "warnings": warnings,
            },
            "ocr_used": ocr_used,
            "fallback_used": fallback_used,
            "errors": errors
        }
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats"""
        formats = ['pdf', 'image']
        
        if self._ocr_available:
            formats.extend(['pdf', 'image'])
        
        return list(set(formats))

    def get_service_info(self) -> Dict[str, Any]:
        """Get service information"""
        return {
            "service_name": "GraniteDoclingService",
            "ocr_available": self._ocr_available,
            "supported_formats": self.get_supported_formats(),
            "source_types": ["pdf", "image"],
            "ocr_languages_available": self._get_available_ocr_languages(),
            "ocr_languages_preferred": ["eng+hin+mar", "eng"],
            "parse_contract": {
                "success": True,
                "source_type": "pdf|image",
                "parser": "pymupdf|ocr|none",
                "raw_text": "...",
                "pages": [],
                "blocks": [],
                "tables": [],
                "metadata": {},
                "ocr_used": False,
                "fallback_used": False,
                "errors": []
            }
        }
    
    def is_format_supported(self, filename: str) -> bool:
        """Check if file format is supported"""
        file_type = self._detect_file_type(filename)
        return file_type in self.get_supported_formats()
