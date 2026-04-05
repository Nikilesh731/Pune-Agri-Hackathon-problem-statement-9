#!/usr/bin/env python3
"""
Test the complete OCR and document processing pipeline with real PDF files
"""
import sys
import os
import base64

# Add the app path to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai-services', 'app'))

def test_real_pdf_processing():
    """Test OCR and processing with a real PDF file"""
    print("Testing real PDF processing...")
    
    try:
        from modules.document_processing.document_processing_service import DocumentProcessingService, DocumentProcessingRequest
        
        service = DocumentProcessingService()
        
        # Test with the PM Kisan scheme application PDF
        pdf_path = "01_scheme_application_pm_kisan.pdf"
        
        if not os.path.exists(pdf_path):
            print(f"✗ PDF file not found: {pdf_path}")
            return False
        
        print(f"✓ Found PDF file: {pdf_path}")
        
        # Read the PDF file
        with open(pdf_path, 'rb') as f:
            pdf_content = f.read()
        
        print(f"✓ PDF file size: {len(pdf_content)} bytes")
        
        # Test OCR extraction
        print("\n--- Testing PDF Text Extraction ---")
        extracted_text = service._extract_text_from_pdf(pdf_content)
        
        if extracted_text and len(extracted_text) > 0:
            print(f"✓ PDF OCR extraction successful: {len(extracted_text)} characters")
            print(f"Sample text: {extracted_text[:200]}...")
            
            # Test the complete workflow
            print("\n--- Testing Complete Workflow ---")
            
            # Create options with OCR text
            options = {
                "filename": pdf_path,
                "ocr_text": extracted_text
            }
            
            # Process the document
            result = service.processor.process_document_workflow(
                pdf_content, pdf_path, "extract_structured", options
            )
            
            if result and result.get("success"):
                print("✓ Document processing workflow successful")
                
                data = result.get("data", {})
                if data:
                    print(f"✓ Document type: {data.get('document_type', 'unknown')}")
                    print(f"✓ Confidence: {data.get('confidence', 0):.3f}")
                    
                    structured_data = data.get('structured_data', {})
                    if structured_data:
                        print(f"✓ Structured data fields: {list(structured_data.keys())}")
                        
                        # Check for key fields
                        key_fields = ['farmer_name', 'scheme_name', 'mobile_number']
                        found_fields = [field for field in key_fields if field in structured_data]
                        if found_fields:
                            print(f"✓ Found key fields: {found_fields}")
                        else:
                            print("⚠ No key fields found")
                    
                    return True
                else:
                    print("✗ No data in processing result")
                    return False
            else:
                print(f"✗ Document processing failed: {result.get('error_message', 'Unknown error')}")
                return False
        else:
            print("✗ PDF OCR extraction returned empty result")
            return False
            
    except Exception as e:
        print(f"✗ Real PDF test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_multiple_pdf_types():
    """Test OCR with different types of PDF documents"""
    print("\nTesting multiple PDF types...")
    
    pdf_files = [
        "01_scheme_application_pm_kisan.pdf",
        "02_subsidy_claim_drip_irrigation.pdf", 
        "03_insurance_claim_crop_loss.pdf",
        "04_grievance_delayed_subsidy_payment.pdf",
        "05_farmer_record_profile.pdf",
        "06_supporting_document_land_receipt.pdf"
    ]
    
    try:
        from modules.document_processing.document_processing_service import DocumentProcessingService
        service = DocumentProcessingService()
        
        results = []
        
        for pdf_file in pdf_files:
            if not os.path.exists(pdf_file):
                print(f"⚠ Skipping {pdf_file} (file not found)")
                continue
                
            try:
                with open(pdf_file, 'rb') as f:
                    pdf_content = f.read()
                
                extracted_text = service._extract_text_from_pdf(pdf_content)
                
                if extracted_text and len(extracted_text) > 0:
                    results.append({
                        'file': pdf_file,
                        'chars': len(extracted_text),
                        'success': True
                    })
                    print(f"✓ {pdf_file}: {len(extracted_text)} chars extracted")
                else:
                    results.append({
                        'file': pdf_file,
                        'chars': 0,
                        'success': False
                    })
                    print(f"✗ {pdf_file}: No text extracted")
                    
            except Exception as e:
                results.append({
                    'file': pdf_file,
                    'chars': 0,
                    'success': False,
                    'error': str(e)
                })
                print(f"✗ {pdf_file}: Error - {e}")
        
        # Summary
        successful = [r for r in results if r['success']]
        print(f"\n--- PDF OCR Summary ---")
        print(f"✓ Successful: {len(successful)}/{len(results)} files")
        print(f"✓ Total characters extracted: {sum(r['chars'] for r in successful)}")
        
        if len(successful) >= len(results) / 2:  # At least 50% success rate
            return True
        else:
            return False
            
    except Exception as e:
        print(f"✗ Multiple PDF test failed: {e}")
        return False

def main():
    """Run real PDF tests"""
    print("=" * 80)
    print("REAL PDF OCR AND PROCESSING TEST")
    print("=" * 80)
    
    all_passed = True
    
    # Test single PDF processing
    if not test_real_pdf_processing():
        all_passed = False
    
    # Test multiple PDF types
    if not test_multiple_pdf_types():
        all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✓ ALL REAL PDF TESTS PASSED")
        print("✓ PDF OCR extraction is working with real documents")
        print("✓ The complete processing pipeline is functional")
        print("✓ Downloaded PDF files should now work correctly")
    else:
        print("✗ SOME REAL PDF TESTS FAILED")
        print("✗ Check the errors above")
    print("=" * 80)
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
