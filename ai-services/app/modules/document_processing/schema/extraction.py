"""
Document Extraction Schemas
Purpose: Pydantic models for document extraction results
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from enum import Enum

from app.modules.document_processing.schema.document_classification import DocumentType


class FieldConfidence(str, Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class ExtractedField(BaseModel):
    """Represents an extracted field with confidence"""
    name: str = Field(..., description="Field name")
    value: Any = Field(..., description="Extracted value")
    confidence: FieldConfidence = Field(..., description="Confidence level")
    source_text: Optional[str] = Field(None, description="Source text snippet")
    extraction_method: str = Field(default="keyword_matching", description="Method used for extraction")


class ExtractionResult(BaseModel):
    """Result of document extraction"""
    document_type: DocumentType = Field(..., description="Type of document processed")
    extracted_fields: Dict[str, ExtractedField] = Field(..., description="Extracted fields")
    missing_fields: List[str] = Field(default_factory=list, description="Missing required fields")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence score")
    extraction_status: str = Field(..., description="Status of extraction")
    field_confidences: Dict[str, float] = Field(default_factory=dict, description="Confidence per field")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    warnings: List[str] = Field(default_factory=list, description="Processing warnings")


class DocumentExtractionRequest(BaseModel):
    """Request for document extraction"""
    text_content: str = Field(..., description="Extracted text content from OCR")
    document_type: DocumentType = Field(..., description="Type of document to process")
    file_name: Optional[str] = Field(None, description="Original file name")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class DocumentExtractionResponse(BaseModel):
    """Response from document extraction"""
    success: bool = Field(..., description="Whether extraction was successful")
    result: Optional[ExtractionResult] = Field(None, description="Extraction result if successful")
    error: Optional[str] = Field(None, description="Error message if failed")
    processing_time_ms: float = Field(..., description="Total processing time")


class BatchExtractionRequest(BaseModel):
    """Request for batch document extraction"""
    documents: List[DocumentExtractionRequest] = Field(..., description="Documents to extract from")


class BatchExtractionResponse(BaseModel):
    """Response from batch document extraction"""
    results: List[DocumentExtractionResponse] = Field(..., description="Extraction results")
    total_processed: int = Field(..., description="Total number of documents processed")
    successful_extractions: int = Field(..., description="Number of successful extractions")
    average_confidence: float = Field(..., description="Average confidence across all extractions")
