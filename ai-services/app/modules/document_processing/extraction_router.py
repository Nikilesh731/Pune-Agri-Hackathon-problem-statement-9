"""
Document Extraction Router
Purpose: Lightweight internal/testing router for direct extraction operations
"""
from fastapi import APIRouter, HTTPException, Form
from typing import Optional, Dict, Any

from app.modules.document_processing.extraction_service import DocumentExtractionService

# Create router
router = APIRouter()

# Initialize service
extraction_service = DocumentExtractionService()


@router.post("/extract")
async def extract_document(
    text_content: str = Form(...),
    document_type: str = Form(...),
    file_name: Optional[str] = Form(None),
    metadata: Optional[str] = Form(None)
):
    """
    Extract fields from document text based on document type
    """
    try:
        # Parse metadata if provided
        parsed_metadata = {}
        if metadata:
            import json
            try:
                parsed_metadata = json.loads(metadata)
            except json.JSONDecodeError:
                parsed_metadata = {}
        
        # Add file_name to metadata
        if file_name:
            parsed_metadata["file_name"] = file_name
        
        # Call extraction service
        result = extraction_service.extract_document(
            text_content=text_content,
            document_type=document_type,
            metadata=parsed_metadata
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.post("/extract-auto")
async def auto_classify_and_extract(
    text_content: str = Form(...),
    file_name: Optional[str] = Form(None),
    metadata: Optional[str] = Form(None)
):
    """
    Automatically classify document and extract fields
    """
    try:
        # Parse metadata if provided
        parsed_metadata = {}
        if metadata:
            import json
            try:
                parsed_metadata = json.loads(metadata)
            except json.JSONDecodeError:
                parsed_metadata = {}
        
        # Call auto-classification and extraction
        result = extraction_service.auto_classify_and_extract(
            text_content=text_content,
            file_name=file_name,
            metadata=parsed_metadata
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.get("/document-types")
async def get_supported_document_types():
    """
    Get list of supported document types
    """
    try:
        supported_types = extraction_service.get_supported_document_types()
        return {
            "supported_types": supported_types,
            "total_count": len(supported_types)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.get("/health")
async def health_check():
    """
    Health check endpoint for document extraction service
    """
    return {
        "status": "healthy",
        "service": "document-extraction"
    }
