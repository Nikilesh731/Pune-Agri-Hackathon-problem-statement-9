"""
Runtime Health Check Module
Purpose: Ensure all required dependencies are available at startup
"""
import logging
import sys
import subprocess
import os
import shutil
from typing import Dict, Any

logger = logging.getLogger(__name__)

class RuntimeHealthChecker:
    """Check availability of critical runtime dependencies"""
    
    def __init__(self):
        self.health_status = {}
        self.missing_critical = []
        
    def check_python_dependencies(self) -> Dict[str, bool]:
        """Check if Python packages are importable"""
        checks = {}
        
        # Check PaddleOCR stack (primary image OCR engine) - GRACEFUL FAILURE HANDLING
        try:
            import paddleocr
            checks['paddleocr'] = True
            logger.info("[HEALTH] PaddleOCR available: v" + getattr(paddleocr, '__version__', 'unknown'))
        except Exception as e:
            checks['paddleocr'] = False
            # Check if this is a system library issue or PDX initialization issue
            error_str = str(e).lower()
            if any(lib in error_str for lib in ['libgl.so.1', 'libgomp.so.1', 'libpaddle.so', 'pdx has already been initialized']):
                logger.warning(f"[HEALTH] PaddleOCR not available due to system libraries or initialization issue: {e}")
                logger.warning("[HEALTH] This is expected in containerized environments without GUI libraries")
            else:
                logger.warning(f"[HEALTH] PaddleOCR not available: {e}")
        
        try:
            import paddle
            checks['paddlepaddle'] = True
            logger.info("[HEALTH] PaddlePaddle available: v" + getattr(paddle, '__version__', 'unknown'))
        except Exception as e:
            checks['paddlepaddle'] = False
            # Check if this is a system library issue
            error_str = str(e).lower()
            if any(lib in error_str for lib in ['libgl.so.1', 'libgomp.so.1', 'libpaddle.so']):
                logger.warning(f"[HEALTH] PaddlePaddle not available due to system libraries: {e}")
                logger.warning("[HEALTH] This is expected in containerized environments without GUI libraries")
            else:
                logger.warning(f"[HEALTH] PaddlePaddle not available: {e}")
        
        # Check pytesseract (legacy fallback)
        try:
            import pytesseract
            checks['pytesseract'] = True
            logger.info("[HEALTH] pytesseract available: v" + getattr(pytesseract, '__version__', 'unknown'))
        except ImportError as e:
            checks['pytesseract'] = False
            logger.warning(f"[HEALTH] pytesseract not available: {e}")
        
        # Check python-docx
        try:
            import docx
            checks['python-docx'] = True
            logger.info("[HEALTH] python-docx available: v" + getattr(docx, '__version__', 'unknown'))
        except ImportError as e:
            checks['python-docx'] = False
            self.missing_critical.append('python-docx package')
            logger.error(f"[HEALTH] python-docx not available: {e}")
        
        # REMOVED: textract is no longer required - legacy .doc support intentionally removed
        
        # Check Pillow (for image processing)
        try:
            from PIL import Image
            checks['pillow'] = True
            logger.info("[HEALTH] Pillow available: v" + getattr(Image, '__version__', 'unknown'))
        except ImportError as e:
            checks['pillow'] = False
            self.missing_critical.append('Pillow package')
            logger.error(f"[HEALTH] Pillow not available: {e}")
        
        # Check OpenCV - GRACEFUL FAILURE HANDLING
        try:
            import cv2
            checks['opencv'] = True
            logger.info("[HEALTH] OpenCV available: v" + cv2.__version__)
        except Exception as e:
            checks['opencv'] = False
            # Check if this is a system library issue
            error_str = str(e).lower()
            if 'libgl.so.1' in error_str:
                logger.warning(f"[HEALTH] OpenCV not available due to system libraries: {e}")
                logger.warning("[HEALTH] This is expected in containerized environments without GUI libraries")
                # Don't mark as critical for containerized environments
            else:
                self.missing_critical.append('OpenCV package')
                logger.error(f"[HEALTH] OpenCV not available: {e}")
        
        # Check PDF libraries
        try:
            import pdfplumber
            checks['pdfplumber'] = True
            logger.info("[HEALTH] pdfplumber available")
        except ImportError as e:
            checks['pdfplumber'] = False
            self.missing_critical.append('pdfplumber package')
            logger.error(f"[HEALTH] pdfplumber not available: {e}")
        
        try:
            import fitz  # PyMuPDF
            checks['pymupdf'] = True
            logger.info("[HEALTH] PyMuPDF available: v" + fitz.version[0])
        except ImportError as e:
            checks['pymupdf'] = False
            self.missing_critical.append('PyMuPDF package')
            logger.error(f"[HEALTH] PyMuPDF not available: {e}")
        
        return checks
    
    def check_system_binaries(self) -> Dict[str, bool]:
        """Check if system binaries are available"""
        checks = {}
        
        # SOFT CHECK: Allow system to start even if OCR engines are missing
        # PaddleOCR is the primary OCR engine and doesn't require system binaries
        # Tesseract is only a legacy fallback
        tesseract_path = shutil.which("tesseract")
        
        if tesseract_path:
            logger.info(f"[HEALTH] Tesseract found at: {tesseract_path}")
            checks['tesseract_binary'] = True
            
            # Additional verification - try to get version
            try:
                version_result = subprocess.run([tesseract_path, '--version'], 
                                              capture_output=True, text=True, timeout=10)
                if version_result.returncode == 0:
                    version_line = version_result.stdout.split('\n')[0] if version_result.stdout else ''
                    logger.info(f"[HEALTH] Tesseract version: {version_line}")
                else:
                    logger.warning("[HEALTH] Could not get Tesseract version")
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError) as e:
                logger.warning(f"[HEALTH] Tesseract version check failed: {e}")
            
            logger.info("[HEALTH] Legacy Tesseract OCR: AVAILABLE")
        else:
            logger.warning("[HEALTH] Tesseract binary not found - legacy OCR fallback unavailable")
            checks['tesseract_binary'] = False
        
        return checks
    
    def check_runtime_environment(self) -> Dict[str, Any]:
        """Check overall runtime environment"""
        env_info = {
            'python_version': sys.version,
            'platform': sys.platform,
            'working_directory': os.getcwd(),
            'path_env': os.environ.get('PATH', ''),
        }
        
        logger.info(f"[HEALTH] Python version: {sys.version.split()[0]}")
        logger.info(f"[HEALTH] Platform: {sys.platform}")
        
        return env_info
    
    def run_full_health_check(self) -> Dict[str, Any]:
        """Run comprehensive health check"""
        logger.info("[HEALTH] Starting runtime health check...")
        
        self.health_status = {
            'python_dependencies': self.check_python_dependencies(),
            'system_binaries': self.check_system_binaries(),
            'environment': self.check_runtime_environment(),
            'overall_status': 'healthy',
            'missing_critical': self.missing_critical
        }
        
        # Determine overall status
        failed_checks = []
        
        # Check Python dependencies
        for dep, status in self.health_status['python_dependencies'].items():
            if not status:
                failed_checks.append(f"Python package: {dep}")
        
        # Check system binaries
        for binary, status in self.health_status['system_binaries'].items():
            if not status:
                failed_checks.append(f"System binary: {binary}")
        
        if failed_checks:
            self.health_status['overall_status'] = 'degraded'
            logger.error(f"[HEALTH] Runtime health check FAILED: {', '.join(failed_checks)}")
            logger.error(f"[HEALTH] Missing critical dependencies: {', '.join(self.missing_critical)}")
        else:
            logger.info("[HEALTH] Runtime health check PASSED: All dependencies available")
        
        return self.health_status
    
    def fail_if_missing_critical(self) -> None:
        """Fail fast if critical dependencies are missing"""
        if self.missing_critical:
            # PART 1: Allow PDF/DOCX to work without OCR engines, but fail clearly for images
            # PaddleOCR is primary, Tesseract is legacy fallback
            paddle_missing = [dep for dep in self.missing_critical if 'paddle' in dep.lower() or 'PaddleOCR' in dep]
            tesseract_missing = [dep for dep in self.missing_critical if 'Tesseract' in dep]
            opencv_missing = [dep for dep in self.missing_critical if 'OpenCV' in dep and 'package' in dep]
            critical_for_docs = [dep for dep in self.missing_critical if 'paddle' not in dep.lower() and 'PaddleOCR' not in dep and 'tesseract' not in dep.lower() and 'Tesseract' not in dep and 'OpenCV' not in dep]
            
            # GRACEFUL: Don't fail for OCR engines in containerized environments
            if paddle_missing:
                logger.warning(f"WARNING: Missing primary OCR dependencies: {', '.join(paddle_missing)}. Image processing will fall back to Tesseract if available.")
                logger.warning("[HEALTH] Image OCR quality will be degraded without PaddleOCR")
                # Remove from critical to allow service to start
                self.missing_critical = [dep for dep in self.missing_critical if dep not in paddle_missing]
            
            if opencv_missing:
                logger.warning(f"WARNING: Missing OpenCV package: {', '.join(opencv_missing)}. This may affect image processing.")
                # Remove from critical to allow service to start in containerized environments
                self.missing_critical = [dep for dep in self.missing_critical if dep not in opencv_missing]
            
            if tesseract_missing and not paddle_missing:
                logger.warning("[HEALTH] Legacy Tesseract OCR unavailable - only PaddleOCR will be used for images")
            elif tesseract_missing and paddle_missing:
                logger.warning(f"WARNING: Missing all OCR dependencies: {', '.join(paddle_missing + tesseract_missing)}. Image processing will fail.")
                logger.warning("[HEALTH] Service will continue but image OCR will not work without PaddleOCR or Tesseract")
            
            if critical_for_docs:
                error_msg = f"CRITICAL: Missing required dependencies: {', '.join(critical_for_docs)}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
        else:
            logger.info("[HEALTH] All critical dependencies available")

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
    
    health = _runtime_checker.run_full_health_check()
    if health['overall_status'] != 'healthy':
        _runtime_checker.fail_if_missing_critical()
    
    # SOFT WARNING: Allow system to start without OCR engines, but warn appropriately
    paddleocr_available = health['python_dependencies'].get('paddleocr', False)
    paddlepaddle_available = health['python_dependencies'].get('paddlepaddle', False)
    ocr_available = paddleocr_available and paddlepaddle_available
    tesseract_available = health['system_binaries'].get('tesseract_binary', False)
    
    if not ocr_available and not tesseract_available:
        logger.warning("[HEALTH] System starting without any OCR engines - image processing will fail")
    elif not ocr_available and tesseract_available:
        logger.warning("[HEALTH] System starting without complete PaddleOCR stack (both paddleocr and paddlepaddle required) - image OCR will use legacy Tesseract fallback")
    elif ocr_available and not tesseract_available:
        logger.info("[HEALTH] System starting with complete PaddleOCR stack - Tesseract legacy fallback unavailable")

# Auto-run health check when module is imported
if __name__ != "__main__":
    try:
        ensure_runtime_ready()
    except Exception as e:
        logger.error(f"[HEALTH] Runtime health check failed at import: {e}")
        # Don't raise at import time, let the service handle it gracefully
