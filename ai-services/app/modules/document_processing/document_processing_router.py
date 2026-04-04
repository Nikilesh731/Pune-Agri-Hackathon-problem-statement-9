"""
Document Processing Router
Purpose: FastAPI router for document processing functionality
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Optional, List, Dict, Any

from .service_schema import DocumentProcessingRequest, DocumentProcessingResult
from .document_processing_service import DocumentProcessingService

router = APIRouter()
doc_service = DocumentProcessingService()


@router.post("/process", response_model=DocumentProcessingResult)
async def process_document(
    file: UploadFile = File(...),
    processing_type: str = "full_process",
    options: Optional[Dict[str, Any]] = None
):
    """
    Process uploaded document
    
    Args:
        file: Document file to process
        processing_type: Type of processing to apply
        options: Additional processing options
    
    Returns:
        DocumentProcessingResult: Processing results
    """
    try:
        # Validate file content type
        if file.content_type and not file.content_type.startswith(('image/', 'application/pdf', 'text/')):
            raise HTTPException(status_code=400, detail="Unsupported file type")
        
        file_content = await file.read()
        
        result = await doc_service.process_document(
            file_content,
            file.filename,
            processing_type,
            options or {}
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")


@router.post("/process-from-metadata", response_model=DocumentProcessingResult)
async def process_document_from_metadata(
    request: DocumentProcessingRequest
):
    """
    Process document from metadata
    
    Args:
        request: Document processing request with file metadata
    
    Returns:
        DocumentProcessingResult: Processing results
    """
    try:
        # Ensure options exists
        updated_options = request.options or {}
        
        # Normalize filename source
        filename = updated_options.get("filename") or updated_options.get("fileName") or "uploaded_document"
        updated_options["filename"] = filename
        
        # Create new request with updated options
        updated_request = DocumentProcessingRequest(
            processing_type=request.processing_type,
            options=updated_options,
            extract_metadata=request.extract_metadata
        )
        
        result = await doc_service.process_request(updated_request)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Metadata processing failed: {str(e)}")


@router.post("/process-batch", response_model=List[DocumentProcessingResult])
async def process_documents_batch(
    files: List[UploadFile] = File(...),
    processing_type: str = "full_process",
    options: Optional[Dict[str, Any]] = None
):
    """
    Process multiple documents in batch
    
    Args:
        files: List of document files to process
        processing_type: Type of processing to apply
        options: Additional processing options
    
    Returns:
        List of DocumentProcessingResult objects
    """
    results = []
    
    for file in files:
        try:
            # Validate file content type
            if file.content_type and not file.content_type.startswith(('image/', 'application/pdf', 'text/')):
                results.append(DocumentProcessingResult(
                    request_id="",
                    success=False,
                    processing_time_ms=0,
                    processing_type=processing_type,
                    filename=file.filename,
                    data=None,
                    metadata={},
                    error_message=f"Unsupported file type: {file.content_type}"
                ))
                continue
            
            file_content = await file.read()
            result = await doc_service.process_document(
                file_content,
                file.filename,
                processing_type,
                options or {}
            )
            results.append(result)
            
        except Exception as e:
            results.append(DocumentProcessingResult(
                request_id="",
                success=False,
                processing_time_ms=0,
                processing_type=processing_type,
                filename=file.filename,
                data=None,
                metadata={},
                error_message=f"Processing failed for {file.filename}: {str(e)}"
            ))
    
    return results


@router.get("/processing-types")
async def get_processing_types():
    """Get available document processing types"""
    return doc_service.get_supported_processing_types()


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "document_processing"
    }
