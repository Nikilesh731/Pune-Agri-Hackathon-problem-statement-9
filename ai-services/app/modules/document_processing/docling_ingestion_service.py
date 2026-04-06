"""
Docling Ingestion Service
Purpose: Primary document conversion layer using Docling for structured extraction
"""
import logging
import os
import tempfile
from typing import Dict, Any, Optional, List
import uuid
from pathlib import Path


class DoclingIngestionService:
    """
    Docling-based document ingestion service
    
    Responsibilities:
    - Accept file bytes + filename
    - Detect input type (pdf, docx, image, txt)
    - Run Docling conversion
    - Return normalized structured output
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._docling_available = None
        self._docling_import_error = None
        
    def _check_docling_availability(self) -> bool:
        """
        Check if Docling is available with lazy initialization
        """
        if self._docling_available is None:
            try:
                import docling
                from docling.document_converter import DocumentConverter
                from docling.datamodel.base_models import InputFormat
                from docling.datamodel.pipeline_options import PdfPipelineOptions
                
                self._docling_available = True
                self.logger.info("[DOCLING] Docling is available")
                
                # Store classes for later use
                self._DocumentConverter = DocumentConverter
                self._InputFormat = InputFormat
                self._PdfPipelineOptions = PdfPipelineOptions
                
            except ImportError as e:
                self._docling_available = False
                self._docling_import_error = str(e)
                self.logger.warning(f"[DOCLING] Docling not available: {e}")
                
        return self._docling_available
    
    def _get_docling_converter(self):
        """
        Get Docling converter with lazy initialization
        """
        if not self._check_docling_availability():
            raise ValueError(f"Docling not available: {self._docling_import_error}")
        
        # Configure pipeline options for production safety
        pipeline_options = self._PdfPipelineOptions()
        pipeline_options.do_ocr = True  # Enable OCR for scanned documents
        pipeline_options.do_table_structure = True  # Extract table structure
        pipeline_options.images_scale = 2.0  # Higher resolution for better OCR
        
        # Create converter with a fallback for Docling versions that do not
        # accept the same configuration keyword shape.
        try:
            converter = self._DocumentConverter(
                format_config={
                    self._InputFormat.PDF: pipeline_options,
                    self._InputFormat.DOCX: {},
                    self._InputFormat.IMAGE: pipeline_options,
                    self._InputFormat.TXT: {},
                }
            )
        except TypeError:
            self.logger.warning("[DOCLING] format_config unsupported, using default converter")
            converter = self._DocumentConverter()
        
        return converter
    
    def _detect_file_type(self, filename: str) -> str:
        """
        Detect file type from filename
        """
        file_extension = Path(filename).suffix.lower()
        
        type_mapping = {
            '.pdf': 'pdf',
            '.docx': 'docx',
            '.doc': 'doc',
            '.jpg': 'image',
            '.jpeg': 'image',
            '.png': 'image',
            '.tiff': 'image',
            '.bmp': 'image',
            '.txt': 'txt',
        }
        
        return type_mapping.get(file_extension, 'unknown')
    
    def _create_temp_file(self, file_data: bytes, filename: str) -> str:
        """
        Create temporary file for Docling processing
        """
        temp_dir = tempfile.gettempdir()
        temp_filename = f"docling_{uuid.uuid4().hex}_{filename}"
        temp_path = os.path.join(temp_dir, temp_filename)
        
        try:
            with open(temp_path, 'wb') as f:
                f.write(file_data)
            return temp_path
        except Exception as e:
            self.logger.error(f"[DOCLING] Failed to create temp file: {e}")
            raise ValueError(f"Failed to create temporary file: {e}")
    
    def _cleanup_temp_file(self, temp_path: str):
        """
        Clean up temporary file
        """
        try:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        except Exception as e:
            self.logger.warning(f"[DOCLING] Failed to cleanup temp file {temp_path}: {e}")
    
    def _convert_docling_result_to_schema(self, docling_result, file_type: str) -> Dict[str, Any]:
        """
        Convert Docling result to normalized schema
        """
        try:
            # Extract raw text
            raw_text = ""
            if hasattr(docling_result, 'text') and docling_result.text:
                raw_text = docling_result.text
            elif hasattr(docling_result, 'document') and hasattr(docling_result.document, 'text'):
                raw_text = docling_result.document.text

            pages = []
            if hasattr(docling_result, 'document') and hasattr(docling_result.document, 'pages'):
                for index, page in enumerate(docling_result.document.pages):
                    pages.append({
                        'page_number': getattr(page, 'page_number', None) or getattr(page, 'page_no', None) or index + 1,
                        'text': getattr(page, 'text', ''),
                        'size': getattr(page, 'size', None)
                    })
            
            # Extract sections
            sections = []
            if hasattr(docling_result, 'document') and hasattr(docling_result.document, 'body'):
                for element in docling_result.document.body:
                    if hasattr(element, 'text') and element.text:
                        sections.append({
                            'type': getattr(element, 'type', 'unknown'),
                            'text': element.text,
                            'confidence': getattr(element, 'confidence', 1.0)
                        })
            
            # Extract tables
            tables = []
            if hasattr(docling_result, 'document') and hasattr(docling_result.document, 'tables'):
                for table in docling_result.document.tables:
                    table_data = {
                        'rows': [],
                        'confidence': getattr(table, 'confidence', 1.0)
                    }
                    
                    # Extract table rows
                    if hasattr(table, 'grid') and hasattr(table.grid, 'rows'):
                        for row in table.grid.rows:
                            row_data = []
                            for cell in row.cells:
                                cell_text = getattr(cell, 'text', '') or ''
                                row_data.append(cell_text)
                            table_data['rows'].append(row_data)
                    
                    tables.append(table_data)
            
            # Extract metadata
            metadata = {
                'file_type': file_type,
                'processing_method': 'docling',
                'has_tables': len(tables) > 0,
                'has_sections': len(sections) > 0,
                'text_length': len(raw_text),
                'page_count': len(pages)
            }
            
            # Add document-specific metadata if available
            if hasattr(docling_result, 'document') and hasattr(docling_result.document, 'meta'):
                doc_meta = docling_result.document.meta
                if hasattr(doc_meta, 'creation_date') and doc_meta.creation_date:
                    metadata['creation_date'] = str(doc_meta.creation_date)
                if hasattr(doc_meta, 'author') and doc_meta.author:
                    metadata['author'] = doc_meta.author
                if hasattr(doc_meta, 'title') and doc_meta.title:
                    metadata['title'] = doc_meta.title
            
            # Convert docling document to serializable format
            docling_document = {}
            if hasattr(docling_result, 'document'):
                docling_document = {
                    'page_count': getattr(docling_result.document, 'page_count', 0),
                    'language': getattr(docling_result.document, 'language', 'unknown'),
                    'text_quality': getattr(docling_result.document, 'text_quality', 'unknown')
                }
            
            return {
                'raw_text': raw_text,
                'pages': pages,
                'blocks': sections,
                'sections': sections,
                'tables': tables,
                'metadata': metadata,
                'docling_document': docling_document
            }
            
        except Exception as e:
            self.logger.error(f"[DOCLING] Failed to convert result to schema: {e}")
            raise ValueError(f"Failed to convert Docling result: {e}")
    
    def ingest_document(self, file_data: bytes, filename: str) -> Dict[str, Any]:
        """
        Ingest document using Docling
        
        Args:
            file_data: Raw file bytes
            filename: Original filename
            
        Returns:
            Normalized structured output with schema:
            {
                "raw_text": str,
                "sections": list,
                "tables": list,
                "metadata": dict,
                "docling_document": dict
            }
            
        Raises:
            ValueError: If Docling conversion fails
        """
        if not file_data:
            raise ValueError("No file data provided")
        
        if not filename:
            raise ValueError("No filename provided")
        
        # Detect file type
        file_type = self._detect_file_type(filename)
        if file_type == 'unknown':
            raise ValueError(f"Unsupported file type: {filename}")
        
        # Check if Docling is available
        if not self._check_docling_availability():
            raise ValueError(f"Docling not available: {self._docling_import_error}")
        
        temp_path = None
        try:
            # Create temporary file
            temp_path = self._create_temp_file(file_data, filename)
            
            # Get Docling converter
            converter = self._get_docling_converter()
            
            # Convert document with safety wrapper
            self.logger.info(f"[DOCLING] Processing {file_type} file: {filename}")
            try:
                docling_result = converter.convert(temp_path)
            except Exception as conversion_error:
                self.logger.error(f"[DOCLING] Conversion failed for {filename}: {conversion_error}")
                raise ValueError(f"Docling failed: {conversion_error}")
            
            # Convert to normalized schema
            result = self._convert_docling_result_to_schema(docling_result, file_type)
            
            self.logger.info(f"[DOCLING] Successfully processed {filename}: {len(result['raw_text'])} chars")
            return result
            
        except Exception as e:
            self.logger.error(f"[DOCLING] Document conversion failed for {filename}: {e}")
            raise ValueError(f"Docling conversion failed: {e}")
            
        finally:
            # Cleanup temporary file
            if temp_path:
                self._cleanup_temp_file(temp_path)
    
    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported file formats
        """
        if not self._check_docling_availability():
            return []
        
        return ['pdf', 'docx', 'image', 'txt']
    
    def is_format_supported(self, filename: str) -> bool:
        """
        Check if file format is supported
        """
        file_type = self._detect_file_type(filename)
        return file_type in self.get_supported_formats()
