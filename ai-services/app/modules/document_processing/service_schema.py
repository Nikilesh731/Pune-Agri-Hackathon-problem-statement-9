from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class DocumentProcessingRequest(BaseModel):
    """Document processing request"""
    processing_type: str = "full_process"
    options: Dict[str, Any] = Field(default_factory=dict)
    extract_metadata: bool = True


class ExtractedFieldData(BaseModel):
    """Individual extracted field with metadata"""
    value: Optional[Any] = None
    confidence: float = 0.0
    source: Optional[str] = None


class RiskFlag(BaseModel):
    """Risk flag for document processing"""
    code: str
    severity: str
    message: str


class DecisionSupport(BaseModel):
    """Decision support information"""
    decision: str
    confidence: float
    reasoning: List[str] = Field(default_factory=list)


class ProcessedDocumentData(BaseModel):
    """Canonical processed document data structure"""
    document_type: str = "unknown"
    classification_confidence: float = 0.0
    classification_reasoning: Dict[str, Any] = Field(default_factory=dict)
    structured_data: Dict[str, Any] = Field(default_factory=dict)
    extracted_fields: Dict[str, ExtractedFieldData] = Field(default_factory=dict)
    missing_fields: List[str] = Field(default_factory=list)
    risk_flags: List[RiskFlag] = Field(default_factory=list)
    extraction_confidence: float = 0.0
    reasoning: List[str] = Field(default_factory=list)
    decision_support: Optional[DecisionSupport] = None
    validation_summary: Dict[str, Any] = Field(default_factory=dict)
    ai_summary: Optional[str] = None  # Added AI summary field
    
    # Intelligence layer fields
    summary: Optional[str] = None
    case_insight: List[str] = Field(default_factory=list)
    predictions: Dict[str, Any] = Field(default_factory=dict)
    ml_insights: Dict[str, Any] = Field(default_factory=dict)
    decision: Optional[str] = None  # Top-level decision field


class DocumentProcessingResult(BaseModel):
    """Canonical document processing result"""
    request_id: str
    success: bool
    processing_time_ms: float
    processing_type: Optional[str] = None
    filename: Optional[str] = None
    data: Optional[ProcessedDocumentData] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None