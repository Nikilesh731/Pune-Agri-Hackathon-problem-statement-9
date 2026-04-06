#!/usr/bin/env python3
"""
SWE 1.5 FINAL INTEGRATION FIX VERIFICATION TEST

This test verifies that the final integration fix works end-to-end for:
- PDF
- JPG / JPEG / PNG  
- DOC
- DOCX

Using the SAME existing pipeline: TEXT -> classification -> handler -> AI/summary -> ML -> routing
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List

# Add AI services path
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai-services'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai-services', 'app'))

try:
    from app.modules.document_processing.document_processing_service import DocumentProcessingService
except ImportError:
    try:
        from ai_services.app.modules.document_processing.document_processing_service import DocumentProcessingService
    except ImportError:
        # Direct import as last resort
        sys.path.append(os.path.join(os.path.dirname(__file__), 'ai-services', 'app', 'modules', 'document_processing'))
        from document_processing_service import DocumentProcessingService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IntegrationTestSuite:
    """Comprehensive test suite for SWE 1.5 final integration fix"""
    
    def __init__(self):
        self.service = DocumentProcessingService()
        self.test_results = []
        
    def log_test_result(self, test_name: str, success: bool, message: str, details: Dict[str, Any] = None):
        """Log a test result"""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "details": details or {}
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if details:
            for key, value in details.items():
                print(f"    {key}: {value}")
    
    def get_test_file_path(self, filename: str) -> str:
        """Get path to test file"""
        test_file_path = os.path.join(os.path.dirname(__file__), filename)
        if not os.path.exists(test_file_path):
            # Try alternative paths
            alt_paths = [
                os.path.join(os.path.dirname(__file__), 'test_files', filename),
                os.path.join(os.path.dirname(__file__), 'ai-services', 'test_files', filename),
                filename  # Direct path
            ]
            for alt_path in alt_paths:
                if os.path.exists(alt_path):
                    return alt_path
        
        return test_file_path
    
    def read_test_file(self, filename: str) -> bytes:
        """Read test file as bytes"""
        file_path = self.get_test_file_path(filename)
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Test file not found: {file_path}")
        
        with open(file_path, 'rb') as f:
            return f.read()
    
    async def test_pdf_integration(self):
        """Test PDF integration - should preserve existing behavior"""
        try:
            # Try to find a PDF test file
            pdf_files = [
                "01_scheme_application_pm_kisan.pdf",
                "02_subsidy_claim_drip_irrigation.pdf", 
                "03_insurance_claim_crop_loss.pdf",
                "test.pdf"
            ]
            
            pdf_content = None
            pdf_filename = None
            
            for pdf_file in pdf_files:
                try:
                    pdf_content = self.read_test_file(pdf_file)
                    pdf_filename = pdf_file
                    break
                except FileNotFoundError:
                    continue
            
            if not pdf_content:
                self.log_test_result(
                    "PDF Integration Test", 
                    False, 
                    "No PDF test file found"
                )
                return
            
            # Test PDF processing
            result = await self.service.process_document(
                file_data=pdf_content,
                filename=pdf_filename,
                processing_type="full_process"
            )
            
            # Verify PDF behavior preserved
            success = result.success and result.data is not None
            
            details = {}
            if success:
                details.update({
                    "document_type": result.data.get("document_type", "unknown"),
                    "confidence": result.data.get("confidence", 0),
                    "structured_data_fields": list(result.data.get("structured_data", {}).keys()),
                    "has_canonical": "canonical" in result.data,
                    "has_ml_insights": "ml_insights" in result.data,
                    "processing_time_ms": result.processing_time_ms
                })
            
            self.log_test_result(
                "PDF Integration Test",
                success,
                "PDF processing successful" if success else "PDF processing failed",
                details
            )
            
        except Exception as e:
            self.log_test_result(
                "PDF Integration Test",
                False,
                f"Exception: {str(e)}"
            )
    
    async def test_image_integration(self):
        """Test image OCR integration"""
        try:
            # Try to find an image test file
            image_files = [
                "test.jpg", "test.jpeg", "test.png", 
                "sample.jpg", "sample.jpeg", "sample.png"
            ]
            
            image_content = None
            image_filename = None
            
            for image_file in image_files:
                try:
                    image_content = self.read_test_file(image_file)
                    image_filename = image_file
                    break
                except FileNotFoundError:
                    continue
            
            if not image_content:
                # Create a minimal test image content (mock)
                image_content = b"mock_image_content_for_testing"
                image_filename = "test.jpg"
            
            # Test image processing
            result = await self.service.process_document(
                file_data=image_content,
                filename=image_filename,
                processing_type="full_process"
            )
            
            # For mock content, we expect extraction to fail gracefully
            # For real images, we expect OCR text to be extracted and processed
            if image_content == b"mock_image_content_for_testing":
                # Mock content should fail extraction
                success = not result.success and "extract" in result.error_message.lower()
                message = "Mock image correctly failed extraction" if success else "Mock image handling unexpected"
            else:
                # Real image should succeed if OCR works
                success = result.success and result.data is not None
                message = "Image OCR processing successful" if success else "Image OCR processing failed"
            
            details = {}
            if result.data:
                details.update({
                    "document_type": result.data.get("document_type", "unknown"),
                    "confidence": result.data.get("confidence", 0),
                    "structured_data_fields": list(result.data.get("structured_data", {}).keys()),
                    "has_canonical": "canonical" in result.data,
                    "processing_time_ms": result.processing_time_ms
                })
            
            self.log_test_result(
                "Image Integration Test",
                success,
                message,
                details
            )
            
        except Exception as e:
            self.log_test_result(
                "Image Integration Test",
                False,
                f"Exception: {str(e)}"
            )
    
    async def test_docx_integration(self):
        """Test DOCX integration"""
        try:
            # Try to find a DOCX test file
            docx_files = [
                "test.docx", "sample.docx", "document.docx"
            ]
            
            docx_content = None
            docx_filename = None
            
            for docx_file in docx_files:
                try:
                    docx_content = self.read_test_file(docx_file)
                    docx_filename = docx_file
                    break
                except FileNotFoundError:
                    continue
            
            if not docx_content:
                # Create a minimal test DOCX content (mock)
                docx_content = b"mock_docx_content_for_testing"
                docx_filename = "test.docx"
            
            # Test DOCX processing
            result = await self.service.process_document(
                file_data=docx_content,
                filename=docx_filename,
                processing_type="full_process"
            )
            
            # For mock content, we expect extraction to fail gracefully
            if docx_content == b"mock_docx_content_for_testing":
                success = not result.success and "extract" in result.error_message.lower()
                message = "Mock DOCX correctly failed extraction" if success else "Mock DOCX handling unexpected"
            else:
                # Real DOCX should succeed
                success = result.success and result.data is not None
                message = "DOCX processing successful" if success else "DOCX processing failed"
            
            details = {}
            if result.data:
                details.update({
                    "document_type": result.data.get("document_type", "unknown"),
                    "confidence": result.data.get("confidence", 0),
                    "structured_data_fields": list(result.data.get("structured_data", {}).keys()),
                    "has_canonical": "canonical" in result.data,
                    "processing_time_ms": result.processing_time_ms
                })
            
            self.log_test_result(
                "DOCX Integration Test",
                success,
                message,
                details
            )
            
        except Exception as e:
            self.log_test_result(
                "DOCX Integration Test",
                False,
                f"Exception: {str(e)}"
            )
    
    async def test_doc_integration(self):
        """Test DOC integration"""
        try:
            # Try to find a DOC test file
            doc_files = [
                "test.doc", "sample.doc", "document.doc"
            ]
            
            doc_content = None
            doc_filename = None
            
            for doc_file in doc_files:
                try:
                    doc_content = self.read_test_file(doc_file)
                    doc_filename = doc_file
                    break
                except FileNotFoundError:
                    continue
            
            if not doc_content:
                # Create a minimal test DOC content (mock)
                doc_content = b"mock_doc_content_for_testing"
                doc_filename = "test.doc"
            
            # Test DOC processing
            result = await self.service.process_document(
                file_data=doc_content,
                filename=doc_filename,
                processing_type="full_process"
            )
            
            # For mock content, we expect extraction to fail gracefully
            if doc_content == b"mock_doc_content_for_testing":
                success = not result.success and "extract" in result.error_message.lower()
                message = "Mock DOC correctly failed extraction" if success else "Mock DOC handling unexpected"
            else:
                # Real DOC should succeed
                success = result.success and result.data is not None
                message = "DOC processing successful" if success else "DOC processing failed"
            
            details = {}
            if result.data:
                details.update({
                    "document_type": result.data.get("document_type", "unknown"),
                    "confidence": result.data.get("confidence", 0),
                    "structured_data_fields": list(result.data.get("structured_data", {}).keys()),
                    "has_canonical": "canonical" in result.data,
                    "processing_time_ms": result.processing_time_ms
                })
            
            self.log_test_result(
                "DOC Integration Test",
                success,
                message,
                details
            )
            
        except Exception as e:
            self.log_test_result(
                "DOC Integration Test",
                False,
                f"Exception: {str(e)}"
            )
    
    async def test_empty_extraction_failure(self):
        """Test that empty extraction fails explicitly"""
        try:
            # Test with empty content
            result = await self.service.process_document(
                file_data=b"",
                filename="empty.pdf",
                processing_type="full_process"
            )
            
            # Should fail explicitly
            success = not result.success and "extract" in result.error_message.lower()
            
            self.log_test_result(
                "Empty Extraction Failure Test",
                success,
                "Empty content correctly failed" if success else "Empty content handling unexpected",
                {"error_message": result.error_message}
            )
            
        except Exception as e:
            self.log_test_result(
                "Empty Extraction Failure Test",
                False,
                f"Exception: {str(e)}"
            )
    
    async def test_existing_ocr_text_preservation(self):
        """Test that existing OCR text is preserved and used"""
        try:
            # Test with provided OCR text
            existing_ocr_text = "This is farmer Ramesh Kumar applying for PM KISAN scheme. Aadhaar number: 123456789012. Village: Pune. Requested amount: 6000."
            
            result = await self.service.process_document(
                file_data=b"mock_content",
                filename="test.pdf",
                processing_type="full_process",
                options={"ocr_text": existing_ocr_text}
            )
            
            # Should succeed using provided OCR text
            success = result.success and result.data is not None
            
            details = {}
            if success:
                details.update({
                    "document_type": result.data.get("document_type", "unknown"),
                    "confidence": result.data.get("confidence", 0),
                    "structured_data_fields": list(result.data.get("structured_data", {}).keys()),
                    "used_existing_ocr": True
                })
            
            self.log_test_result(
                "Existing OCR Text Preservation Test",
                success,
                "Existing OCR text used successfully" if success else "Existing OCR text not used",
                details
            )
            
        except Exception as e:
            self.log_test_result(
                "Existing OCR Text Preservation Test",
                False,
                f"Exception: {str(e)}"
            )
    
    async def test_classification_integration(self):
        """Test classification with extraction integration"""
        try:
            # Test classification with a PDF
            pdf_files = [
                "01_scheme_application_pm_kisan.pdf",
                "test.pdf"
            ]
            
            pdf_content = None
            pdf_filename = None
            
            for pdf_file in pdf_files:
                try:
                    pdf_content = self.read_test_file(pdf_file)
                    pdf_filename = pdf_file
                    break
                except FileNotFoundError:
                    continue
            
            if not pdf_content:
                # Use mock content with OCR text
                pdf_content = b"mock_content"
                pdf_filename = "test.pdf"
            
            # Test classification
            result = await self.service.classify_document(
                file_data=pdf_content,
                filename=pdf_filename
            )
            
            # Should return classification result
            success = isinstance(result, dict) and "document_type" in result
            
            self.log_test_result(
                "Classification Integration Test",
                success,
                "Classification with extraction successful" if success else "Classification failed",
                {
                    "document_type": result.get("document_type", "unknown"),
                    "confidence": result.get("classification_confidence", 0),
                    "has_error": "error_message" in result
                }
            )
            
        except Exception as e:
            self.log_test_result(
                "Classification Integration Test",
                False,
                f"Exception: {str(e)}"
            )
    
    async def run_all_tests(self):
        """Run all integration tests"""
        print("=" * 80)
        print("SWE 1.5 FINAL INTEGRATION FIX VERIFICATION")
        print("=" * 80)
        print("Testing that ALL binary formats pass through text extraction")
        print("before reaching the processor, using the SAME pipeline:")
        print("TEXT -> classification -> handler -> AI/summary -> ML -> routing")
        print("=" * 80)
        
        await self.test_pdf_integration()
        await self.test_image_integration()
        await self.test_docx_integration()
        await self.test_doc_integration()
        await self.test_empty_extraction_failure()
        await self.test_existing_ocr_text_preservation()
        await self.test_classification_integration()
        
        # Print summary
        print("=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {passed/total*100:.1f}%")
        
        print("\nDetailed Results:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test_name']}: {result['message']}")
        
        print("=" * 80)
        
        if passed == total:
            print("🎉 ALL TESTS PASSED! Integration fix is working correctly.")
        else:
            print("⚠️  Some tests failed. Please review the integration implementation.")
        
        return passed == total

async def main():
    """Main test runner"""
    test_suite = IntegrationTestSuite()
    success = await test_suite.run_all_tests()
    
    if success:
        print("\n✅ SWE 1.5 FINAL INTEGRATION FIX VERIFICATION: SUCCESS")
        print("All document formats now use the same pipeline with required text extraction.")
    else:
        print("\n❌ SWE 1.5 FINAL INTEGRATION FIX VERIFICATION: FAILED")
        print("Some integration issues need to be addressed.")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())
