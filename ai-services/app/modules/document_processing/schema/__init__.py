"""
Document Processing Schemas
Purpose: Schema definitions for document processing
"""

from .extraction import (
    FieldConfidence,
    ExtractedField,
    ExtractionResult,
    DocumentExtractionRequest,
    DocumentExtractionResponse,
    BatchExtractionRequest,
    BatchExtractionResponse
)

from .document_classification import (
    DocumentType,
    ClassificationReasoning,
    DocumentClassificationRequest,
    DocumentClassificationResponse
)

__all__ = [
    "FieldConfidence",
    "ExtractedField",
    "ExtractionResult",
    "DocumentExtractionRequest",
    "DocumentExtractionResponse",
    "BatchExtractionRequest",
    "BatchExtractionResponse",
    "DocumentType",
    "ClassificationReasoning",
    "DocumentClassificationRequest",
    "DocumentClassificationResponse"
]
