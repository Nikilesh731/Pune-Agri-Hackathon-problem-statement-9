#!/usr/bin/env python3
"""
Test script for OCR functionality in document processing
"""
import sys
import os

# Add the app path to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai-services', 'app'))

def test_ocr_imports():
    """Test that all required OCR libraries can be imported"""
    print("Testing OCR library imports...")
    
    try:
        import pdfplumber
        print("✓ pdfplumber imported successfully")
    except ImportError as e:
        print(f"✗ pdfplumber import failed: {e}")
        return False
    
    try:
        import fitz  # PyMuPDF
        print("✓ PyMuPDF imported successfully")
    except ImportError as e:
        print(f"✗ PyMuPDF import failed: {e}")
        return False
    
    try:
        import PIL.Image
        print("✓ PIL.Image imported successfully")
    except ImportError as e:
        print(f"✗ PIL.Image import failed: {e}")
        return False
    
    try:
        import pytesseract
        print("✓ pytesseract imported successfully")
    except ImportError as e:
        print(f"✗ pytesseract import failed: {e}")
        return False
    
    return True

def test_document_processing_service():
    """Test the DocumentProcessingService OCR methods"""
    print("\nTesting DocumentProcessingService OCR methods...")
    
    try:
        from modules.document_processing.document_processing_service import DocumentProcessingService
        service = DocumentProcessingService()
        print("✓ DocumentProcessingService instantiated successfully")
        
        # Test the method exists
        if hasattr(service, '_extract_text_from_file'):
            print("✓ _extract_text_from_file method exists")
        else:
            print("✗ _extract_text_from_file method missing")
            return False
            
        if hasattr(service, '_extract_text_from_pdf'):
            print("✓ _extract_text_from_pdf method exists")
        else:
            print("✗ _extract_text_from_pdf method missing")
            return False
            
        if hasattr(service, '_extract_text_from_image'):
            print("✓ _extract_text_from_image method exists")
        else:
            print("✗ _extract_text_from_image method missing")
            return False
            
        if hasattr(service, '_extract_text_from_text_file'):
            print("✓ _extract_text_from_text_file method exists")
        else:
            print("✗ _extract_text_from_text_file method missing")
            return False
        
        return True
        
    except ImportError as e:
        print(f"✗ Failed to import DocumentProcessingService: {e}")
        return False
    except Exception as e:
        print(f"✗ Error testing DocumentProcessingService: {e}")
        return False

def test_simple_text_extraction():
    """Test basic text extraction from a simple text file"""
    print("\nTesting basic text file extraction...")
    
    try:
        from modules.document_processing.document_processing_service import DocumentProcessingService
        service = DocumentProcessingService()
        
        # Create a simple text content
        test_content = b"This is a test document for OCR processing.\nIt contains multiple lines.\nFarmer Name: Test Farmer\nScheme: PM Kisan"
        
        # Test extraction
        extracted_text = service._extract_text_from_text_file(test_content)
        
        if extracted_text and len(extracted_text) > 0:
            print(f"✓ Text extraction successful: {len(extracted_text)} characters")
            print(f"Sample text: {extracted_text[:100]}...")
            return True
        else:
            print("✗ Text extraction returned empty result")
            return False
            
    except Exception as e:
        print(f"✗ Text extraction test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("OCR FUNCTIONALITY TEST")
    print("=" * 60)
    
    all_passed = True
    
    # Test library imports
    if not test_ocr_imports():
        all_passed = False
    
    # Test service methods
    if not test_document_processing_service():
        all_passed = False
    
    # Test basic extraction
    if not test_simple_text_extraction():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL TESTS PASSED - OCR functionality is ready")
    else:
        print("✗ SOME TESTS FAILED - Check the errors above")
    print("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
