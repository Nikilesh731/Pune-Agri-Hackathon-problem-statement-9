"""
Common Schemas
Purpose: Shared Pydantic models used across AI services
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class BaseResponse(BaseModel):
    """Base response schema"""
    success: bool = True
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseResponse):
    """Error response schema"""
    success: bool = False
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ProcessingRequest(BaseModel):
    """Base processing request schema"""
    request_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ProcessingResult(BaseModel):
    """Base processing result schema"""
    request_id: str
    success: bool
    confidence: Optional[float] = None
    processing_time_ms: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class FileProcessingRequest(ProcessingRequest):
    """File processing request schema"""
    file_content: bytes = Field(..., description="File content as bytes")
    file_name: str = Field(..., description="Original file name")
    file_type: str = Field(..., description="File MIME type")
    file_size: int = Field(..., description="File size in bytes")


class ClassificationResult(ProcessingResult):
    """Classification result schema"""
    predicted_class: str
    class_probabilities: Dict[str, float]
    threshold_met: bool


class OCRResult(ProcessingResult):
    """OCR result schema"""
    extracted_text: str
    confidence_score: float
    language_detected: Optional[str] = None


class ScoringResult(ProcessingResult):
    """Scoring result schema"""
    score: float = Field(..., ge=0, le=1, description="Score between 0 and 1")
    risk_level: str = Field(..., description="Risk level: low, medium, high")
    factors: Dict[str, float] = Field(..., description="Contributing factors")


class FraudDetectionResult(ProcessingResult):
    """Fraud detection result schema"""
    is_fraud: bool
    fraud_probability: float = Field(..., ge=0, le=1)
    risk_indicators: List[str]
    explanation: Optional[str] = None


class SummarizationResult(ProcessingResult):
    """Summarization result schema"""
    summary: str
    original_length: int
    summary_length: int
    compression_ratio: float
