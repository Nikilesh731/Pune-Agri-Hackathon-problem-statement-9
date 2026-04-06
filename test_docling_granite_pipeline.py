"""
Test Suite for Docling + Granite Architecture Migration
Purpose: Verify the new pipeline works correctly and handles failures gracefully
"""
import os
import sys
import pytest
import json
import asyncio
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add the ai-services module to the path
sys.path.append(os.path.join(os.path.dirname(__file__), "ai-services"))

# Mock the imports that might not be available in test environment
sys.modules['docling'] = Mock()
sys.modules['docling.document_converter'] = Mock()
sys.modules['docling.datamodel.base_models'] = Mock()
sys.modules['docling.datamodel.pipeline_options'] = Mock()

# Import the services to test
try:
    from app.modules.document_processing.docling_ingestion_service import DoclingIngestionService
    from app.modules.document_processing.granite_extraction_service import GraniteExtractionService
    from app.modules.document_processing.document_processing_service import DocumentProcessingService

    SERVICES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import services for testing: {e}")
    SERVICES_AVAILABLE = False


class TestDoclingIngestionService:
    """Test cases for Docling Ingestion Service"""
    
    @pytest.fixture
    def docling_service(self):
        """Create Docling service instance"""
        if not SERVICES_AVAILABLE:
            pytest.skip("Services not available for testing")
        
        return DoclingIngestionService()
    
    def test_init(self, docling_service):
        """Test service initialization"""
        assert docling_service is not None
        assert docling_service.logger is not None
        assert docling_service._docling_available is None  # Lazy initialization
    
    def test_detect_file_type(self, docling_service):
        """Test file type detection"""
        # Test PDF
        assert docling_service._detect_file_type("test.pdf") == "pdf"
        assert docling_service._detect_file_type("TEST.PDF") == "pdf"
        
        # Test DOCX
        assert docling_service._detect_file_type("test.docx") == "docx"
        assert docling_service._detect_file_type("document.DOCX") == "docx"
        
        # Test images
        assert docling_service._detect_file_type("image.jpg") == "image"
        assert docling_service._detect_file_type("photo.jpeg") == "image"
        assert docling_service._detect_file_type("scan.png") == "image"
        assert docling_service._detect_file_type("document.tiff") == "image"
        assert docling_service._detect_file_type("picture.bmp") == "image"
        
        # Test text
        assert docling_service._detect_file_type("notes.txt") == "txt"
        assert docling_service._detect_file_type("readme.TEXT") == "txt"
        
        # Test unknown
        assert docling_service._detect_file_type("unknown.xyz") == "unknown"
        assert docling_service._detect_file_type("no_extension") == "unknown"
    
    @patch('docling.document_converter.DocumentConverter')
    @patch('docling.datamodel.base_models.InputFormat')
    @patch('docling.datamodel.pipeline_options.PdfPipelineOptions')
    def test_check_docling_availability_success(self, mock_pipeline_options, mock_input_format, mock_converter):
        """Test successful Docling availability check"""
        if not SERVICES_AVAILABLE:
            pytest.skip("Services not available for testing")
        
        service = DoclingIngestionService()
        
        # Mock successful import
        with patch.dict('sys.modules', {'docling': Mock(), 'docling.document_converter': Mock(), 'docling.datamodel.base_models': Mock(), 'docling.datamodel.pipeline_options': Mock()}):
            result = service._check_docling_availability()
            assert result is True
            assert service._docling_available is True
    
    def test_check_docling_availability_failure(self, docling_service):
        """Test Docling availability check failure"""
        # Force failure by setting import error
        docling_service._docling_import_error = "Mock import failure"
        docling_service._docling_available = False
        
        result = docling_service._check_docling_availability()
        assert result is False
    
    def test_ingest_document_no_data(self, docling_service):
        """Test ingestion with no file data"""
        with pytest.raises(ValueError, match="No file data provided"):
            docling_service.ingest_document(b"", "test.pdf")
        
        with pytest.raises(ValueError, match="No file data provided"):
            docling_service.ingest_document(None, "test.pdf")
    
    def test_ingest_document_no_filename(self, docling_service):
        """Test ingestion with no filename"""
        with pytest.raises(ValueError, match="No filename provided"):
            docling_service.ingest_document(b"test data", "")
        
        with pytest.raises(ValueError, match="No filename provided"):
            docling_service.ingest_document(b"test data", None)
    
    def test_ingest_document_unsupported_type(self, docling_service):
        """Test ingestion with unsupported file type"""
        with pytest.raises(ValueError, match="Unsupported file type"):
            docling_service.ingest_document(b"test data", "test.xyz")
    
    def test_ingest_document_docling_unavailable(self, docling_service):
        """Test ingestion when Docling is not available"""
        # Force Docling to be unavailable
        docling_service._docling_available = False
        docling_service._docling_import_error = "Docling not installed"
        
        with pytest.raises(ValueError, match="Docling not available"):
            docling_service.ingest_document(b"test data", "test.pdf")
    
    @patch.object(DoclingIngestionService, '_check_docling_availability', return_value=True)
    @patch.object(DoclingIngestionService, '_get_docling_converter')
    @patch.object(DoclingIngestionService, '_create_temp_file')
    @patch.object(DoclingIngestionService, '_cleanup_temp_file')
    @patch.object(DoclingIngestionService, '_convert_docling_result_to_schema')
    def test_ingest_document_success(self, mock_convert, mock_cleanup, mock_temp_file, mock_converter, mock_availability, docling_service):
        """Test successful document ingestion"""
        # Setup mocks
        mock_temp_file.return_value = "/tmp/test_docling_test.pdf"
        mock_converter_instance = Mock()
        mock_converter.return_value = mock_converter_instance
        
        # Mock Docling result
        mock_docling_result = Mock()
        mock_docling_result.text = "Sample document text"
        mock_converter_instance.convert.return_value = mock_docling_result
        
        # Mock schema conversion
        expected_schema = {
            'raw_text': 'Sample document text',
            'sections': [],
            'tables': [],
            'metadata': {'file_type': 'pdf', 'processing_method': 'docling'},
            'docling_document': {}
        }
        mock_convert.return_value = expected_schema
        
        # Test ingestion
        result = docling_service.ingest_document(b"test pdf content", "test.pdf")
        
        assert result == expected_schema
        mock_temp_file.assert_called_once()
        mock_converter_instance.convert.assert_called_once()
        mock_convert.assert_called_once()
        mock_cleanup.assert_called_once()
    
    def test_convert_docling_result_to_schema(self, docling_service):
        """Test Docling result to schema conversion"""
        # Create mock Docling result
        mock_result = Mock()
        mock_result.text = "Sample document text"
        
        # Mock document structure
        mock_document = Mock()
        mock_document.body = []
        mock_document.tables = []
        mock_document.meta = Mock()
        mock_document.meta.creation_date = None
        mock_document.meta.author = None
        mock_document.meta.title = None
        mock_result.document = mock_document
        
        # Test conversion
        schema = docling_service._convert_docling_result_to_schema(mock_result, "pdf")
        
        assert schema['raw_text'] == "Sample document text"
        assert schema['sections'] == []
        assert schema['tables'] == []
        assert schema['metadata']['file_type'] == "pdf"
        assert schema['metadata']['processing_method'] == "docling"
        assert schema['docling_document'] == {}
    
    def test_get_supported_formats(self, docling_service):
        """Test getting supported formats"""
        # When not available
        docling_service._docling_available = False
        formats = docling_service.get_supported_formats()
        assert formats == []
        
        # When available
        docling_service._docling_available = True
        formats = docling_service.get_supported_formats()
        assert 'pdf' in formats
        assert 'docx' in formats
        assert 'image' in formats
        assert 'txt' in formats
    
    def test_is_format_supported(self, docling_service):
        """Test format support checking"""
        # Mock availability
        docling_service._docling_available = True
        
        # Supported formats
        assert docling_service.is_format_supported("test.pdf") is True
        assert docling_service.is_format_supported("test.docx") is True
        assert docling_service.is_format_supported("test.jpg") is True
        assert docling_service.is_format_supported("test.txt") is True
        
        # Unsupported formats
        assert docling_service.is_format_supported("test.xyz") is False
        
        # When not available
        docling_service._docling_available = False
        assert docling_service.is_format_supported("test.pdf") is False


class TestGraniteExtractionService:
    """Test cases for Granite Extraction Service"""
    
    @pytest.fixture
    def granite_service(self):
        """Create Granite service instance"""
        if not SERVICES_AVAILABLE:
            pytest.skip("Services not available for testing")
        
        return GraniteExtractionService("http://test-endpoint.com")
    
    def test_init(self, granite_service):
        """Test service initialization"""
        assert granite_service is not None
        assert granite_service.logger is not None
        assert granite_service.granite_endpoint == "http://test-endpoint.com"
        assert granite_service.model_name == "granite"
        assert granite_service._granite_available is None  # Lazy initialization
    
    def test_prepare_granite_prompt(self, granite_service):
        """Test Granite prompt preparation"""
        # Sample Docling output
        docling_output = {
            'raw_text': 'This is a sample document about PM Kisan scheme. Farmer: Ram Kumar. Aadhaar: 123456789012.',
            'sections': [
                {'type': 'paragraph', 'text': 'PM Kisan scheme application', 'confidence': 0.9}
            ],
            'tables': [],
            'metadata': {
                'file_type': 'pdf',
                'processing_method': 'docling'
            }
        }
        
        prompt = granite_service._prepare_granite_prompt(docling_output)
        
        assert 'DOCUMENT TEXT:' in prompt
        assert 'PM Kisan scheme' in prompt
        assert 'Ram Kumar' in prompt
        assert '123456789012' in prompt
        assert 'DOCUMENT STRUCTURE:' in prompt
        assert 'FILE TYPE: pdf' in prompt
        assert 'document_type' in prompt
        assert 'structured_data' in prompt
        assert 'STRICT JSON ONLY' in prompt
    
    def test_prepare_granite_prompt_empty_text(self, granite_service):
        """Test prompt preparation with empty text"""
        docling_output = {
            'raw_text': '',
            'sections': [],
            'tables': [],
            'metadata': {'file_type': 'pdf'}
        }
        
        prompt = granite_service._prepare_granite_prompt(docling_output)
        
        assert 'DOCUMENT TEXT:' in prompt
        assert 'FILE TYPE: pdf' in prompt
    
    def test_parse_granite_response_valid_json(self, granite_service):
        """Test parsing valid JSON response"""
        valid_response = '''
        {
            "document_type": "pm_kisan_scheme",
            "structured_data": {
                "farmer_name": "Ram Kumar",
                "aadhaar_number": "123456789012"
            },
            "extracted_fields": {
                "farmer_name": "Ram Kumar",
                "aadhaar_number": "123456789012"
            },
            "missing_fields": ["bank_account_number"],
            "confidence": 0.85,
            "reasoning": ["Found farmer name and Aadhaar"],
            "classification_confidence": 0.90,
            "classification_reasoning": {
                "keywords_found": ["PM Kisan"],
                "structural_indicators": ["application form"],
                "confidence_factors": ["clear keywords"]
            },
            "risk_flags": [],
            "decision_support": {
                "decision": "approve",
                "confidence": 0.80,
                "reasoning": ["Complete information"]
            },
            "canonical": {},
            "summary": "PM Kisan scheme application for Ram Kumar"
        }
        '''
        
        result = granite_service._parse_granite_response(valid_response)
        
        assert result['document_type'] == "pm_kisan_scheme"
        assert result['structured_data']['farmer_name'] == "Ram Kumar"
        assert result['confidence'] == 0.85
        assert result['classification_confidence'] == 0.90
        assert isinstance(result['missing_fields'], list)
        assert isinstance(result['reasoning'], list)
        assert isinstance(result['risk_flags'], list)
    
    def test_parse_granite_response_with_markdown(self, granite_service):
        """Test parsing JSON response wrapped in markdown"""
        markdown_response = '''```json
        {
            "document_type": "pm_kisan_scheme",
            "structured_data": {"farmer_name": "Ram Kumar"},
            "extracted_fields": {"farmer_name": "Ram Kumar"},
            "missing_fields": [],
            "confidence": 0.85,
            "reasoning": ["Found name"],
            "classification_confidence": 0.90,
            "classification_reasoning": {
                "keywords_found": ["PM Kisan"],
                "structural_indicators": [],
                "confidence_factors": []
            },
            "risk_flags": [],
            "decision_support": {
                "decision": "approve",
                "confidence": 0.80,
                "reasoning": ["Complete info"]
            },
            "canonical": {},
            "summary": "PM Kisan application"
        }
        ```'''
        
        result = granite_service._parse_granite_response(markdown_response)
        
        assert result['document_type'] == "pm_kisan_scheme"
        assert result['structured_data']['farmer_name'] == "Ram Kumar"
    
    def test_parse_granite_response_invalid_json(self, granite_service):
        """Test parsing invalid JSON response"""
        invalid_response = 'This is not valid JSON at all'
        
        with pytest.raises(ValueError, match="Granite response is not valid JSON"):
            granite_service._parse_granite_response(invalid_response)
    
    def test_parse_granite_response_missing_fields(self, granite_service):
        """Test parsing response with missing required fields"""
        incomplete_response = '''
        {
            "document_type": "pm_kisan_scheme",
            "structured_data": {"farmer_name": "Ram Kumar"}
        }
        '''
        
        result = granite_service._parse_granite_response(incomplete_response)
        
        # Should add missing fields with defaults
        assert result['document_type'] == "pm_kisan_scheme"
        assert result['extracted_fields'] == {}
        assert result['missing_fields'] == []
        assert result['confidence'] == 0.0
        assert result['reasoning'] == []
        assert result['classification_confidence'] == 0.0
        assert result['risk_flags'] == []
        assert result['decision_support']['decision'] == 'manual_review'
    
    def test_parse_granite_response_confidence_validation(self, granite_service):
        """Test confidence value validation and normalization"""
        response_with_bad_confidence = '''
        {
            "document_type": "pm_kisan_scheme",
            "structured_data": {},
            "extracted_fields": {},
            "missing_fields": [],
            "confidence": 1.5,
            "reasoning": [],
            "classification_confidence": -0.5,
            "classification_reasoning": {
                "keywords_found": [],
                "structural_indicators": [],
                "confidence_factors": []
            },
            "risk_flags": [],
            "decision_support": {
                "decision": "manual_review",
                "confidence": 2.0,
                "reasoning": []
            },
            "canonical": {},
            "summary": "Test"
        }
        '''
        
        result = granite_service._parse_granite_response(response_with_bad_confidence)
        
        # Confidence values should be normalized to 0.0-1.0 range
        assert result['confidence'] == 1.0  # 1.5 -> 1.0
        assert result['classification_confidence'] == 0.0  # -0.5 -> 0.0
    
    def test_extract_with_granite_no_input(self, granite_service):
        """Test extraction with no Docling input"""
        with pytest.raises(ValueError, match="No Docling output provided"):
            granite_service.extract_with_granite(None)
        
        with pytest.raises(ValueError, match="No Docling output provided"):
            granite_service.extract_with_granite({})
    
    def test_extract_with_granite_no_text(self, granite_service):
        """Test extraction with no text content"""
        docling_output = {
            'raw_text': '',
            'sections': [],
            'tables': [],
            'metadata': {'file_type': 'pdf'}
        }
        
        with pytest.raises(ValueError, match="No text content available"):
            granite_service.extract_with_granite(docling_output)
    
    @patch.object(GraniteExtractionService, '_check_granite_availability', return_value=True)
    @patch.object(GraniteExtractionService, '_call_granite_api')
    @patch.object(GraniteExtractionService, '_parse_granite_response')
    def test_extract_with_granite_success(self, mock_parse, mock_call, mock_availability, granite_service):
        """Test successful extraction with Granite"""
        # Setup mocks
        docling_output = {
            'raw_text': 'PM Kisan scheme application for Ram Kumar',
            'sections': [],
            'tables': [],
            'metadata': {'file_type': 'pdf'}
        }
        
        mock_call.return_value = '{"document_type": "pm_kisan_scheme", "structured_data": {}}'
        
        expected_result = {
            'document_type': 'pm_kisan_scheme',
            'structured_data': {'farmer_name': 'Ram Kumar'},
            'extracted_fields': {},
            'missing_fields': [],
            'confidence': 0.85,
            'reasoning': ['Extracted successfully'],
            'classification_confidence': 0.90,
            'classification_reasoning': {
                'keywords_found': ['PM Kisan'],
                'structural_indicators': [],
                'confidence_factors': []
            },
            'risk_flags': [],
            'decision_support': {
                'decision': 'approve',
                'confidence': 0.80,
                'reasoning': ['Complete information']
            },
            'canonical': {},
            'summary': 'PM Kisan application'
        }
        mock_parse.return_value = expected_result
        
        # Test extraction
        result = granite_service.extract_with_granite(docling_output)
        
        assert result == expected_result
        assert 'processing_metadata' in result
        assert result['processing_metadata']['processing_method'] == 'granite'
        mock_call.assert_called_once()
        mock_parse.assert_called_once()
    
    def test_is_available(self, granite_service):
        """Test service availability check"""
        # Mock availability
        granite_service._granite_available = True
        assert granite_service.is_available() is True
        
        granite_service._granite_available = False
        assert granite_service.is_available() is False
    
    def test_get_service_info(self, granite_service):
        """Test getting service information"""
        # Mock availability
        granite_service._granite_available = True
        granite_service._granite_import_error = None
        
        info = granite_service.get_service_info()
        
        assert info['service_name'] == 'GraniteExtractionService'
        assert info['endpoint'] == "http://test-endpoint.com"
        assert info['model_name'] == 'granite'
        assert info['available'] is True
        assert info['error'] is None


class TestDocumentProcessingServiceIntegration:
    """Test cases for integrated Document Processing Service"""
    
    @pytest.fixture
    def processing_service(self):
        """Create document processing service instance"""
        if not SERVICES_AVAILABLE:
            pytest.skip("Services not available for testing")
        
        # Mock runtime health to avoid actual checks
        with patch('app.modules.document_processing.runtime_health.ensure_runtime_ready'):
            with patch('app.modules.document_processing.runtime_health.get_runtime_health', return_value={'overall_status': 'healthy'}):
                return DocumentProcessingService()
    
    def test_init_with_docling_granite(self, processing_service):
        """Test service initialization with Docling and Granite"""
        assert processing_service is not None
        # Services should be initialized (may be None due to import issues)
        assert hasattr(processing_service, 'docling_service')
        assert hasattr(processing_service, 'granite_service')
    
    def test_should_use_docling_granite(self, processing_service):
        """Test routing logic for Docling+Granite"""
        # When services are not available
        processing_service.docling_service = None
        processing_service.granite_service = None
        assert processing_service._should_use_docling_granite("test.pdf") is False
        
        # When only one service is available
        processing_service.docling_service = Mock()
        processing_service.granite_service = None
        assert processing_service._should_use_docling_granite("test.pdf") is False
        
        processing_service.docling_service = None
        processing_service.granite_service = Mock()
        assert processing_service._should_use_docling_granite("test.pdf") is False
        
        # When both services are available
        processing_service.docling_service = Mock()
        processing_service.granite_service = Mock()
        
        # Supported file types
        assert processing_service._should_use_docling_granite("test.pdf") is True
        assert processing_service._should_use_docling_granite("test.docx") is True
        assert processing_service._should_use_docling_granite("test.jpg") is True
        assert processing_service._should_use_docling_granite("test.jpeg") is True
        assert processing_service._should_use_docling_granite("test.png") is True
        assert processing_service._should_use_docling_granite("test.tiff") is True
        assert processing_service._should_use_docling_granite("test.bmp") is True
        
        # TXT files use traditional path (as per requirements)
        assert processing_service._should_use_docling_granite("test.txt") is False
        
        # Unsupported types
        assert processing_service._should_use_docling_granite("test.xyz") is False
    
    def test_create_processing_failure_payload(self, processing_service):
        """Test creation of processing failure payload"""
        payload = processing_service._create_processing_failure_payload(
            "test.pdf", "Test error message", "TEST_FAILURE"
        )
        
        assert payload['document_type'] == "unknown"
        assert payload['structured_data'] == {}
        assert payload['extracted_fields'] == {}
        assert payload['missing_fields'] == []
        assert payload['confidence'] == 0.0
        assert payload['classification_confidence'] == 0.0
        assert payload['risk_flags'][0]['code'] == "TEST_FAILURE"
        assert payload['risk_flags'][0]['severity'] == "high"
        assert payload['decision_support']['decision'] == "manual_review_required"
        assert payload['processing_metadata']['pipeline'] == "docling_granite"
        assert payload['processing_metadata']['processing_failure'] is True
    
    @patch.object(DocumentProcessingService, '_should_use_docling_granite', return_value=True)
    @patch.object(DocumentProcessingService, '_extract_with_docling_granite')
    async def test_process_document_uses_docling_granite(self, mock_extract, mock_routing, processing_service):
        """Test that process_document uses Docling+Granite when appropriate"""
        # Setup mocks
        expected_result = {
            'document_type': 'pm_kisan_scheme',
            'structured_data': {'farmer_name': 'Ram Kumar'},
            'extracted_fields': {},
            'missing_fields': [],
            'confidence': 0.85,
            'reasoning': ['Extracted successfully'],
            'classification_confidence': 0.90,
            'classification_reasoning': {
                'keywords_found': [],
                'structural_indicators': [],
                'confidence_factors': []
            },
            'risk_flags': [],
            'decision_support': {
                'decision': 'approve',
                'confidence': 0.80,
                'reasoning': ['Complete information']
            },
            'canonical': {},
            'summary': 'PM Kisan application'
        }
        mock_extract.return_value = expected_result
        
        # Test processing
        result = await processing_service.process_document(
            b"test pdf content", "test.pdf", "full_process"
        )
        
        assert result.success is True
        assert result.data == expected_result
        assert result.metadata['pipeline'] == "docling_granite"
        mock_extract.assert_called_once()
    
    @patch.object(DocumentProcessingService, '_should_use_docling_granite', return_value=True)
    @patch.object(DocumentProcessingService, '_extract_with_docling_granite')
    @patch.object(DocumentProcessingService, '_create_processing_failure_payload')
    async def test_process_document_docling_granite_failure(self, mock_failure, mock_extract, mock_routing, processing_service):
        """Test process_document handling of Docling+Granite failure"""
        # Setup mocks
        mock_extract.side_effect = ValueError("Docling+Granite failed")
        
        failure_payload = {
            'document_type': 'unknown',
            'structured_data': {},
            'extracted_fields': {},
            'missing_fields': [],
            'confidence': 0.0,
            'reasoning': ['DOCLING_GRANITE_FAILURE: Docling+Granite failed'],
            'classification_confidence': 0.0,
            'classification_reasoning': {
                'keywords_found': [],
                'structural_indicators': [],
                'confidence_factors': ['DOCLING_GRANITE_FAILURE: Docling+Granite failed']
            },
            'risk_flags': [
                {
                    'code': 'DOCLING_GRANITE_FAILURE',
                    'severity': 'high',
                    'message': 'DOCLING_GRANITE_FAILURE: Docling+Granite failed'
                }
            ],
            'decision_support': {
                'decision': 'manual_review_required',
                'confidence': 0.0,
                'reasoning': ['DOCLING_GRANITE_FAILURE: Docling+Granite failed']
            },
            'canonical': {},
            'processing_metadata': {
                'pipeline': 'docling_granite',
                'processing_failure': True,
                'failure_type': 'DOCLING_GRANITE_FAILURE',
                'error_message': 'Docling+Granite failed'
            }
        }
        mock_failure.return_value = failure_payload
        
        # Test processing
        result = await processing_service.process_document(
            b"test pdf content", "test.pdf", "full_process"
        )
        
        assert result.success is True  # Success but with failure flags
        assert result.data == failure_payload
        assert result.metadata['pipeline'] == "docling_granite"
        assert result.metadata['processing_failure'] is True
        mock_failure.assert_called_once()


# Integration tests that require actual services
@pytest.mark.integration
class TestDoclingGraniteIntegration:
    """Integration tests for Docling+Granite pipeline (requires actual services)"""
    
    @pytest.mark.skipif(not SERVICES_AVAILABLE, reason="Services not available")
    def test_full_pipeline_text_pdf(self):
        """Test full pipeline with text PDF"""
        # This test requires actual Docling and Granite services
        # It's marked as integration and should be run separately
        pytest.skip("Integration test - requires actual services")
    
    @pytest.mark.skipif(not SERVICES_AVAILABLE, reason="Services not available")
    def test_full_pipeline_scanned_pdf(self):
        """Test full pipeline with scanned PDF"""
        pytest.skip("Integration test - requires actual services")
    
    @pytest.mark.skipif(not SERVICES_AVAILABLE, reason="Services not available")
    def test_full_pipeline_docx(self):
        """Test full pipeline with DOCX"""
        pytest.skip("Integration test - requires actual services")
    
    @pytest.mark.skipif(not SERVICES_AVAILABLE, reason="Services not available")
    def test_full_pipeline_image(self):
        """Test full pipeline with image"""
        pytest.skip("Integration test - requires actual services")


def _find_sample_document() -> Path:
    env_path = os.getenv("PIPELINE_SAMPLE_FILE")
    if env_path:
        candidate = Path(env_path)
        if candidate.exists():
            return candidate

    search_roots = [Path("docs"), Path("data"), Path("tests"), Path(".")]
    for root in search_roots:
        if not root.exists():
            continue
        for pattern in ("*.pdf", "*.png", "*.jpg", "*.jpeg"):
            for candidate in root.rglob(pattern):
                if candidate.is_file():
                    return candidate

    raise FileNotFoundError("No sample PDF or image found for full pipeline validation")


def test_full_pipeline():
    if not SERVICES_AVAILABLE:
        pytest.skip("Services not available for testing")

    sample_path = _find_sample_document()
    service = DocumentProcessingService()

    result = asyncio.run(
        service.process_document(
            sample_path.read_bytes(),
            sample_path.name,
            "full_process",
            {},
        )
    )

    data = result.data or {}
    processing_metadata = data.get("processing_metadata", {}) if isinstance(data, dict) else getattr(data, "processing_metadata", {})
    document_type = data.get("document_type", "unknown") if isinstance(data, dict) else getattr(data, "document_type", "unknown")
    confidence = data.get("confidence", 0.0) if isinstance(data, dict) else getattr(data, "confidence", 0.0)
    extracted_text_length = processing_metadata.get("docling_text_length", 0) if isinstance(processing_metadata, dict) else 0
    pipeline_used = result.metadata.get("pipeline", processing_metadata.get("pipeline", "unknown"))

    print(f"extracted text length: {extracted_text_length}")
    print(f"document_type: {document_type}")
    print(f"confidence: {confidence}")
    print(f"pipeline used: {pipeline_used}")


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])
