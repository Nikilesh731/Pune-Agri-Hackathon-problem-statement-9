"""
Runtime Health Check Module
Purpose: Ensure document processing runtime is available without treating OCR or Granite as hard failures.
"""
import logging
import os
import shutil
import sys
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

DEFAULT_WINDOWS_TESSERACT = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


class RuntimeHealthChecker:
    """Check availability of document-processing runtime dependencies."""

    def __init__(self):
        self.health_status: Dict[str, Any] = {}
        self.missing_critical = []

    def _check_docling_available(self) -> bool:
        try:
            import docling  # noqa: F401
            from docling.document_converter import DocumentConverter  # noqa: F401
            from docling.datamodel.base_models import InputFormat  # noqa: F401
            from docling.datamodel.pipeline_options import PdfPipelineOptions  # noqa: F401
            return True
        except Exception:
            return False

    def _check_granite_available(self) -> bool:
        granite_endpoint = os.getenv("GRANITE_ENDPOINT", "").strip()
        use_granite = os.getenv("USE_GRANITE", "true").lower() == "true"
        return bool(use_granite and granite_endpoint)

    def _resolve_tesseract_binary(self) -> Optional[str]:
        try:
            import pytesseract

            current_cmd = getattr(pytesseract.pytesseract, "tesseract_cmd", "") or shutil.which("tesseract")
            if current_cmd:
                pytesseract.pytesseract.tesseract_cmd = current_cmd
                pytesseract.get_tesseract_version()
                return current_cmd
        except Exception:
            pass

        if os.path.exists(DEFAULT_WINDOWS_TESSERACT):
            try:
                import pytesseract

                pytesseract.pytesseract.tesseract_cmd = DEFAULT_WINDOWS_TESSERACT
                pytesseract.get_tesseract_version()
                return DEFAULT_WINDOWS_TESSERACT
            except Exception:
                return None

        return None

    def check_python_dependencies(self) -> Dict[str, bool]:
        """Check if Python packages are importable."""
        checks: Dict[str, bool] = {}

        checks["docling"] = self._check_docling_available()

        try:
            import pytesseract

            checks["pytesseract"] = True
        except Exception as exc:
            checks["pytesseract"] = False

        try:
            import docx

            checks["python-docx"] = True
        except ImportError as exc:
            checks["python-docx"] = False

        try:
            from PIL import Image

            checks["pillow"] = True
        except ImportError as exc:
            checks["pillow"] = False

        try:
            import cv2

            checks["opencv"] = True
        except Exception as exc:
            checks["opencv"] = False

        try:
            import pdfplumber

            checks["pdfplumber"] = True
        except ImportError as exc:
            checks["pdfplumber"] = False

        try:
            import fitz  # PyMuPDF

            checks["pymupdf"] = True
        except ImportError as exc:
            checks["pymupdf"] = False

        return checks

    def check_system_binaries(self) -> Dict[str, bool]:
        """Check if required system binaries are available."""
        checks: Dict[str, bool] = {}
        tesseract_path = self._resolve_tesseract_binary()

        if tesseract_path:
            checks["tesseract_binary"] = True
        else:
            checks["tesseract_binary"] = False

        return checks

    def check_runtime_environment(self) -> Dict[str, Any]:
        """Check overall runtime environment."""
        env_info = {
            "python_version": sys.version,
            "platform": sys.platform,
            "working_directory": os.getcwd(),
            "path_env": os.environ.get("PATH", ""),
        }

        return env_info

    def run_full_health_check(self) -> Dict[str, Any]:
        """Run a production-safe runtime health check."""
        python_dependencies = self.check_python_dependencies()
        system_binaries = self.check_system_binaries()
        environment = self.check_runtime_environment()

        docling_available = bool(python_dependencies.get("docling", False))
        ocr_available = bool(python_dependencies.get("pytesseract", False) and system_binaries.get("tesseract_binary", False))
        granite_available = self._check_granite_available()

        if docling_available and ocr_available and granite_available:
            overall_status = "healthy"
        elif not docling_available and not ocr_available:
            overall_status = "failed"
        else:
            overall_status = "degraded"

        self.health_status = {
            "python_dependencies": python_dependencies,
            "system_binaries": system_binaries,
            "environment": environment,
            "docling_available": docling_available,
            "ocr_available": ocr_available,
            "granite_available": granite_available,
            "overall_status": overall_status,
            "missing_critical": self.missing_critical,
        }

        logger.info(f"[HEALTH] Docling: {'available' if docling_available else 'unavailable'}")
        logger.info(f"[HEALTH] OCR: {'available' if ocr_available else 'unavailable'}")
        logger.info(f"[HEALTH] Granite: {'available' if granite_available else 'disabled'}")
        logger.info(f"[HEALTH] Status: {overall_status}")

        return self.health_status

    def fail_if_missing_critical(self) -> None:
        """Keep startup non-fatal; runtime health is reported through structured status."""
        return

# Singleton instance for import
_runtime_checker = None

def get_runtime_health() -> Dict[str, Any]:
    """Get runtime health status (cached)"""
    global _runtime_checker
    if _runtime_checker is None:
        _runtime_checker = RuntimeHealthChecker()
    return _runtime_checker.run_full_health_check()

def ensure_runtime_ready() -> None:
    """Ensure runtime is ready for document processing"""
    global _runtime_checker
    if _runtime_checker is None:
        _runtime_checker = RuntimeHealthChecker()
    
    _runtime_checker.run_full_health_check()

