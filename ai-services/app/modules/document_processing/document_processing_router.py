"""
Document Processing Router
Purpose: FastAPI router for document processing functionality
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Optional, List, Dict, Any
from pathlib import Path

from app.modules.document_processing.service_schema import DocumentProcessingRequest, DocumentProcessingResult
from app.modules.document_processing.document_processing_service import DocumentProcessingService

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
        if file.content_type and not file.content_type.startswith(('image/', 'application/pdf', 'text/', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')):
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
        import logging
        logger = logging.getLogger(__name__)
        
        # Add required debug log
        print("[DOC] process-from-metadata endpoint hit")
        logger.info("[DOC] metadata request received")
        
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
            if file.content_type and not file.content_type.startswith(('image/', 'application/pdf', 'text/', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')):
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


@router.post("/parse")
async def parse_document(file: UploadFile = File(...)):
    """
    Parse document using Docling/Granite-Docling with OCR fallback
    
    Args:
        file: Document file to parse
        
    Returns:
        Structured JSON response with document content
    """
    try:
        import tempfile
        import os
        import logging
        from .granite_docling_service import GraniteDoclingService
        
        # Initialize service
        service = GraniteDoclingService()
        logger = logging.getLogger(__name__)
        
        # Validate file format
        if not service.is_format_supported(file.filename):
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file format: {file.filename}"
            )
        
        # Read file content
        file_content = await file.read()
        logger.info(f"[PARSER] parse started for {file.filename}")
        
        # Create temporary file
        temp_path = None
        try:
            suffix = Path(file.filename).suffix if file.filename else ""
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                temp_file.write(file_content)
                temp_path = temp_file.name
            
            # Parse document
            result = service.parse_document(temp_path)

            if result.get("parser") == "docling":
                logger.info(f"[PARSER] docling success for {file.filename}")
            elif result.get("parser") == "ocr":
                logger.info(f"[PARSER] ocr fallback success for {file.filename}")
            else:
                logger.warning(f"[PARSER] final failure for {file.filename}")
            
            return result
            
        finally:
            # Cleanup temporary file
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document parsing failed: {str(e)}")


@router.get("/parse-info")
async def get_parse_info():
    """Get parsing service information"""
    try:
        from .granite_docling_service import GraniteDoclingService
        service = GraniteDoclingService()
        return service.get_service_info()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get service info: {str(e)}")
