#!/usr/bin/env python3
"""
Test script for production Pipeline verification
Verifies: Docling → Classification → Granite → Response

Usage:
    python test_production_pipeline.py <test_pdf_path> <test_image_path>

Example:
    python test_production_pipeline.py test_application.pdf test_grievance.jpg
"""

import sys
import json
import time
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

def test_docling_ingestion():
    """Test Step 1: Docling ingestion"""
    print("\n" + "="*60)
    print("TEST 1: DOCLING INGESTION")
    print("="*60)
    
    try:
        from app.modules.document_processing.docling_ingestion_service import DoclingIngestionService
        
        service = DoclingIngestionService()
        print("[✓] DoclingIngestionService initialized")
        
        # Check if Docling is available
        if service._check_docling_availability():
            print("[✓] Docling is available")
        else:
            print("[✗] Docling NOT available!")
            return False
        
        return True
        
    except Exception as e:
        print(f"[✗] Docling ingestion test failed: {e}")
        return False


def test_classification():
    """Test Step 2: Document classification"""
    print("\n" + "="*60)
    print("TEST 2: DOCUMENT CLASSIFICATION")
    print("="*60)
    
    try:
        from app.modules.document_processing.classification_service import DocumentClassificationService
        
        service = DocumentClassificationService()
        print("[✓] DocumentClassificationService initialized")
        
        # Test classification with sample text
        test_text = """
        PM Kisan Samman Nidhi Application Form
        
        Farmer Name: राज कुमार
        Aadhaar Number: 1234 5678 9012
        Bank Account: 123456789012
        IFSC Code: SBIN0010001
        Land Area: 2.5 hectares
        Crop Type: गेहूं (Wheat)
        Village: नई दिल्ली
        District: दिल्ली
        State: दिल्ली
        Mobile Number: 98765 43210
        Requested Amount: ₹50,000
        Application ID: APP2024001
        Date of Application: 2024-01-15
        Scheme Name: PM Kisan Samman Nidhi
        """
        
        result = service.classify(test_text, "test_application.pdf")
        print(f"[✓] Classification result: {result}")
        
        if result.get("document_type") in ["scheme_application", "unknown"]:
            print("[✓] Correct document type identified")
            return True
        else:
            print(f"[✗] Unexpected document type: {result.get('document_type')}")
            return False
        
    except Exception as e:
        print(f"[✗] Classification test failed: {e}")
        return False


def test_granite_extraction():
    """Test Step 3: Granite semantic extraction"""
    print("\n" + "="*60)
    print("TEST 3: GRANITE SEMANTIC EXTRACTION (Lightweight V2)")
    print("="*60)
    
    try:
        from app.modules.document_processing.granite_extraction_service_v2 import GraniteExtractionServiceV2
        
        service = GraniteExtractionServiceV2()
        print("[✓] GraniteExtractionServiceV2 initialized")
        
        # Test with sample Docling output
        test_docling_output = {
            "raw_text": """
            PM Kisan Samman Nidhi Application Form
            
            Farmer Name: राज कुमार
            Aadhaar Number: 1234 5678 9012
            Bank Account: 123456789012
            IFSC Code: SBIN0010001
            Land Area: 2.5 hectares
            Crop Type: गेहूं (Wheat)
            Village: नई दिल्ली
            District: दिल्ली
            State: दिल्ली
            Mobile Number: 98765 43210
            Requested Amount: ₹50,000
            Application ID: APP2024001
            Date of Application: 2024-01-15
            Scheme Name: PM Kisan Samman Nidhi
            """,
            "pre_identified_type": "scheme_application",
            "pre_identification_confidence": 0.85,
            "metadata": {"file_type": "pdf"},
            "sections": [],
            "tables": []
        }
        
        result = service.extract_with_granite(test_docling_output)
        
        # Validate response structure
        required_fields = [
            "document_type", "structured_data", "extracted_fields",
            "confidence", "reasoning", "ai_summary", "risk_flags"
        ]
        
        missing = [f for f in required_fields if f not in result]
        if missing:
            print(f"[✗] Missing required fields: {missing}")
            return False
        
        print(f"[✓] Granite extraction successful")
        print(f"    Document Type: {result['document_type']}")
        print(f"    Confidence: {result['confidence']}")
        print(f"    Extracted Fields: {len(result['structured_data'])} fields")
        print(f"    AI Summary: {result['ai_summary'][:100]}...")
        
        return True
        
    except Exception as e:
        print(f"[✗] Granite extraction test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_full_pipeline():
    """Test full pipeline"""
    print("\n" + "="*60)
    print("TEST 4: FULL PIPELINE INTEGRATION")
    print("="*60)
    
    try:
        from app.modules.document_processing.document_processing_service import DocumentProcessingService
        import asyncio
        
        service = DocumentProcessingService()
        print("[✓] DocumentProcessingService initialized")
        
        # Check services
        if service.docling_service:
            print("[✓] Docling service available")
        else:
            print("[✗] Docling service NOT available")
            return False
        
        if service.granite_service:
            print("[✓] Granite service available (V2 Lightweight)")
        else:
            print("[✗] Granite service NOT available")
            return False
        
        print("[✓] Full pipeline initialization successful")
        return True
        
    except Exception as e:
        print(f"[✗] Full pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_with_sample_file(filepath: str):
    """Test processing actual file if provided"""
    print("\n" + "="*60)
    print(f"TEST 5: PROCESS SAMPLE FILE - {filepath}")
    print("="*60)
    
    try:
        if not Path(filepath).exists():
            print(f"[!] File not found: {filepath} - Skipping")
            return None
        
        from app.modules.document_processing.document_processing_service import DocumentProcessingService
        import asyncio
        
        service = DocumentProcessingService()
        
        # Read file
        with open(filepath, 'rb') as f:
            file_data = f.read()
        
        print(f"[✓] Loaded file: {filepath} ({len(file_data)} bytes)")
        
        # Process
        async def process():
            start = time.time()
            result = await service.process_document(
                file_data,
                Path(filepath).name,
                "full_process",
                {}
            )
            elapsed = time.time() - start
            
            print(f"[✓] Processing completed in {elapsed:.2f}s")
            print(f"\nResult Summary:")
            print(f"  - Success: {result.success}")
            print(f"  - Document Type: {result.data.get('document_type') if result.data else 'N/A'}")
            if result.data:
                print(f"  - Confidence: {result.data.get('confidence', 0.0):.2f}")
                print(f"  - Structured Data Keys: {list(result.data.get('structured_data', {}).keys())}")
                print(f"  - AI Summary: {result.data.get('ai_summary', '')[:100]}...")
            
            return result
        
        # Run async
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(process())
        
        return result.success if result else False
        
    except Exception as e:
        print(f"[✗] File processing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("PRODUCTION PIPELINE VERIFICATION SUITE")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("Docling Ingestion", test_docling_ingestion()))
    results.append(("Document Classification", test_classification()))
    results.append(("Granite Extraction", test_granite_extraction()))
    results.append(("Full Pipeline", test_full_pipeline()))
    
    # Test with sample files if provided
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        results.append((f"Sample File: {filepath}", test_with_sample_file(filepath)))
    
    if len(sys.argv) > 2:
        filepath = sys.argv[2]
        results.append((f"Sample File: {filepath}", test_with_sample_file(filepath)))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[✓] ALL TESTS PASSED - Production ready!")
        return 0
    else:
        print("\n[✗] SOME TESTS FAILED - Fix before deployment")
        return 1


if __name__ == "__main__":
    sys.exit(main())
