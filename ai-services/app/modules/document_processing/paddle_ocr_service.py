"""
PaddleOCR Service for Image OCR
Purpose: Dedicated service for PaddleOCR-based image text extraction
"""
import logging
import io
from typing import Optional

logger = logging.getLogger(__name__)

class PaddleOCRService:
    """Dedicated PaddleOCR service for image text extraction"""
    
    def __init__(self):
        """Initialize PaddleOCR service with lazy loading"""
        self._ocr_engine = None
        self._initialization_error = None
        logger.info("[PADDLE OCR] Service initialized (lazy loading enabled)")
    
    def _get_engine(self):
        """Lazy-load PaddleOCR engine only when needed"""
        if self._ocr_engine is not None:
            return self._ocr_engine
        
        if self._initialization_error:
            # Return previously cached initialization error
            raise self._initialization_error
        
        try:
            import paddleocr
            logger.info("[PADDLE OCR] Initializing PaddleOCR engine...")
            
            # Initialize PaddleOCR with CPU mode and English language
            # Use angle classification for better document recognition
            self._ocr_engine = paddleocr.PaddleOCR(
                use_angle_cls=True,  # Enable angle classification
                lang='en',          # English as baseline language
                use_gpu=False,       # CPU mode for compatibility
                show_log=False      # Suppress PaddleOCR internal logs
            )
            
            logger.info("[PADDLE OCR] Engine initialized successfully")
            return self._ocr_engine
            
        except ImportError as import_error:
            self._initialization_error = ValueError(
                f"PaddleOCR failed: PaddleOCR package not available - {str(import_error)}"
            )
            logger.error(f"[PADDLE OCR] Import failed: {import_error}")
            raise self._initialization_error
            
        except Exception as init_error:
            self._initialization_error = ValueError(
                f"PaddleOCR failed: Engine initialization failed - {str(init_error)}"
            )
            logger.error(f"[PADDLE OCR] Initialization failed: {init_error}")
            raise self._initialization_error
    
    def extract_text_from_image_bytes(self, file_content: bytes, filename: str) -> str:
        """
        Extract text from image bytes using PaddleOCR
        
        Args:
            file_content: Raw image bytes
            filename: Original filename for logging
            
        Returns:
            Extracted text string
            
        Raises:
            ValueError: If OCR fails or no text is extracted
        """
        logger.info(f"[PADDLE OCR] Extraction started for {filename}")
        
        try:
            import PIL.Image
            
            # Open image from bytes
            image = PIL.Image.open(io.BytesIO(file_content))
            
            # Convert to RGB if necessary (PaddleOCR works best with RGB)
            if image.mode != 'RGB':
                image = image.convert('RGB')
                logger.debug(f"[PADDLE OCR] Converted {filename} to RGB mode")
            
            # Get PaddleOCR engine (lazy-loaded)
            ocr_engine = self._get_engine()
            
            # Run PaddleOCR on the image
            logger.debug(f"[PADDLE OCR] Processing {filename} with PaddleOCR...")
            ocr_results = ocr_engine.ocr(image, cls=True)
            
            # Check if OCR returned any results
            if not ocr_results or not ocr_results[0]:
                logger.error(f"[PADDLE OCR] No text extracted from {filename}")
                raise ValueError("OCR failed: no text extracted by PaddleOCR")
            
            # Flatten OCR results into plain text string
            extracted_lines = []
            for page in ocr_results:
                if page:
                    for line in page:
                        if line and len(line) >= 2:
                            # line[1] contains (text, confidence)
                            text_info = line[1]
                            if text_info and len(text_info) >= 1:
                                text = text_info[0]
                                if text and text.strip():
                                    extracted_lines.append(text.strip())
            
            if not extracted_lines:
                logger.error(f"[PADDLE OCR] No readable text found in {filename}")
                raise ValueError("OCR failed: no text extracted by PaddleOCR")
            
            # Join lines with newline separation
            extracted_text = '\n'.join(extracted_lines)
            
            # Log extraction results
            logger.info(f"[PADDLE OCR] Extraction complete: {len(extracted_text)} chars from {filename}")
            
            return extracted_text
            
        except Exception as ocr_error:
            error_msg = f"PaddleOCR extraction failed - {str(ocr_error)}"
            logger.error(f"[PADDLE OCR] Extraction failed: {error_msg}")
            raise ValueError(f"OCR failed: {error_msg}")
