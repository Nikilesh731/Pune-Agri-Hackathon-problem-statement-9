"""
Runtime Health Check Module
Purpose: Ensure all required dependencies are available at startup
"""
import logging
import sys
import subprocess
import os
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
        
        # Check pytesseract
        try:
            import pytesseract
            checks['pytesseract'] = True
            logger.info("[HEALTH] pytesseract available: v" + getattr(pytesseract, '__version__', 'unknown'))
        except ImportError as e:
            checks['pytesseract'] = False
            self.missing_critical.append('pytesseract Python package')
            logger.error(f"[HEALTH] pytesseract not available: {e}")
        
        # Check python-docx
        try:
            import docx
            checks['python-docx'] = True
            logger.info("[HEALTH] python-docx available: v" + getattr(docx, '__version__', 'unknown'))
        except ImportError as e:
            checks['python-docx'] = False
            self.missing_critical.append('python-docx package')
            logger.error(f"[HEALTH] python-docx not available: {e}")
        
        # Check textract
        try:
            import textract
            checks['textract'] = True
            logger.info("[HEALTH] textract available")
        except ImportError as e:
            checks['textract'] = False
            self.missing_critical.append('textract package')
            logger.error(f"[HEALTH] textract not available: {e}")
        
        # Check Pillow (for image processing)
        try:
            from PIL import Image
            checks['pillow'] = True
            logger.info("[HEALTH] Pillow available: v" + getattr(Image, '__version__', 'unknown'))
        except ImportError as e:
            checks['pillow'] = False
            self.missing_critical.append('Pillow package')
            logger.error(f"[HEALTH] Pillow not available: {e}")
        
        # Check OpenCV
        try:
            import cv2
            checks['opencv'] = True
            logger.info("[HEALTH] OpenCV available: v" + cv2.__version__)
        except ImportError as e:
            checks['opencv'] = False
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
        
        # Check Tesseract binary with enhanced Railway detection
        tesseract_found = False
        
        # Method 1: Check PATH directly
        try:
            result = subprocess.run(['which', 'tesseract'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                tesseract_path = result.stdout.strip()
                checks['tesseract_binary'] = True
                tesseract_found = True
                logger.info(f"[HEALTH] Tesseract binary found via which: {tesseract_path}")
                
                # Get version info
                version_result = subprocess.run([tesseract_path, '--version'], 
                                              capture_output=True, text=True, timeout=10)
                if version_result.returncode == 0:
                    version_line = version_result.stdout.split('\n')[0] if version_result.stdout else ''
                    logger.info(f"[HEALTH] Tesseract version: {version_line}")
                else:
                    logger.warning("[HEALTH] Could not get Tesseract version")
            else:
                logger.warning("[HEALTH] 'which tesseract' failed, trying direct check")
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError) as e:
            logger.debug(f"[HEALTH] which tesseract failed: {e}")
        
        # Method 2: Direct PATH check (fallback)
        if not tesseract_found:
            try:
                result = subprocess.run(['tesseract', '--version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    checks['tesseract_binary'] = True
                    tesseract_found = True
                    version_line = result.stdout.split('\n')[0] if result.stdout else ''
                    logger.info(f"[HEALTH] Tesseract binary found in PATH: {version_line}")
                else:
                    checks['tesseract_binary'] = False
                    self.missing_critical.append('Tesseract system binary')
                    logger.error("[HEALTH] Tesseract binary not found or not working")
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError) as e:
                checks['tesseract_binary'] = False
                self.missing_critical.append('Tesseract system binary')
                logger.error(f"[HEALTH] Tesseract binary check failed: {e}")
        
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
            # PART 1: Allow PDF/DOC/DOCX to work without Tesseract, but fail clearly for images
            critical_for_images = [dep for dep in self.missing_critical if 'Tesseract' in dep]
            if critical_for_images:
                error_msg = f"CRITICAL: Missing required dependencies for image OCR: {', '.join(critical_for_images)}. Image processing will fail."
                logger.error(error_msg)
                # Don't fail the entire service - just log clearly that images won't work
                logger.warning("[HEALTH] Service will continue but image OCR will not work without Tesseract")
            else:
                error_msg = f"CRITICAL: Missing required dependencies: {', '.join(self.missing_critical)}"
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

# Auto-run health check when module is imported
if __name__ != "__main__":
    try:
        ensure_runtime_ready()
    except Exception as e:
        logger.error(f"[HEALTH] Runtime health check failed at import: {e}")
        # Don't raise at import time, let the service handle it gracefully
