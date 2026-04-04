"""
Document Classification Schemas
Purpose: Pydantic models for document classification
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class DocumentType(str, Enum):
    SCHEME_APPLICATION = "scheme_application"
    SUBSIDY_CLAIM = "subsidy_claim"
    INSURANCE_CLAIM = "insurance_claim"
    GRIEVANCE_LETTER = "grievance_letter"
    FARMER_RECORD = "farmer_record"
    SUPPORTING_DOCUMENT = "supporting_document"
    LAND_RECORD = "land_record"
    BANK_PASSBOOK = "bank_passbook"
    ID_PROOF = "id_proof"
    UNKNOWN_DOCUMENT = "unknown_document"
    UNKNOWN = "unknown"


class ClassificationReasoning(BaseModel):
    """Reasoning behind document classification"""
    keywords_found: List[str] = Field(default_factory=list, description="Keywords that influenced classification")
    structural_indicators: List[str] = Field(default_factory=list, description="Document structure indicators")
    confidence_factors: List[str] = Field(default_factory=list, description="Factors affecting confidence")


class DocumentClassificationRequest(BaseModel):
    """Request model for document classification"""
    text_content: str = Field(..., description="Extracted text content from OCR")
    file_name: Optional[str] = Field(None, description="Original file name")
    file_type: Optional[str] = Field(None, description="File MIME type")
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional metadata")


class DocumentClassificationResponse(BaseModel):
    """Response model for document classification"""
    document_type: DocumentType = Field(..., description="Classified document type")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Classification confidence score")
    reasoning: ClassificationReasoning = Field(..., description="Classification reasoning")
    processing_time_ms: Optional[float] = Field(None, description="Processing time in milliseconds")
    suggestions: Optional[List[DocumentType]] = Field(default_factory=list, description="Alternative type suggestions")
