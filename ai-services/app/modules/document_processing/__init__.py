"""
Document Processing Module
Purpose: Document processing and analysis services
"""

from .document_processing_router import router
from .document_processing_service import DocumentProcessingService

__all__ = ["router", "DocumentProcessingService"]
