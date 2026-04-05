#!/usr/bin/env python3
"""
Test the complete end-to-end flow: file URL download -> OCR extraction -> processing workflow
This simulates the exact scenario that was failing before the fix
"""
import sys
import os
import base64
import tempfile
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler

# Add the app path to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai-services', 'app'))

class SimpleFileHandler(BaseHTTPRequestHandler):
    """Simple HTTP server to serve a PDF file for testing"""
    
    def do_GET(self):
        if self.path == '/test.pdf':
            try:
                with open('01_scheme_application_pm_kisan.pdf', 'rb') as f:
                    pdf_content = f.read()
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/pdf')
                self.send_header('Content-Length', str(len(pdf_content)))
                self.end_headers()
                self.wfile.write(pdf_content)
            except Exception as e:
                self.send_error(500, str(e))
        else:
            self.send_error(404, 'File not found')
    
    def log_message(self, format, *args):
        # Suppress server logs
        pass

def start_test_server():
    """Start a simple HTTP server for testing"""
    import threading
    
    # Try to find an available port
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('localhost', 0))
    port = sock.getsockname()[1]
    sock.close()
    
    server = HTTPServer(('localhost', port), SimpleFileHandler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    
    # Give server time to start
    import time
    time.sleep(1)
    
    return server, port

def test_end_to_end_processing():
    """Test the complete end-to-end flow that was failing before"""
    print("Testing end-to-end processing with file URL...")
    
    try:
        # Start test server
        print("Starting test HTTP server...")
        server, port = start_test_server()
        print(f"✓ Test server started on http://localhost:{port}")
        
        try:
            from modules.document_processing.document_processing_service import DocumentProcessingService, DocumentProcessingRequest
            
            service = DocumentProcessingService()
            
            # Create a request that simulates what the backend sends
            request = DocumentProcessingRequest(
                processing_type="extract_structured",
                options={
                    "filename": "test.pdf",
                    "fileUrl": f"http://localhost:{port}/test.pdf"
                }
            )
            
            print("✓ Created document processing request")
            print(f"✓ File URL: http://localhost:{port}/test.pdf")
            
            # Process the request - this should:
            # 1. Download the file from URL
            # 2. Extract OCR text from PDF
            # 3. Pass OCR text to workflow
            # 4. Return structured data
            
            print("\n--- Processing Document Request ---")
            result = asyncio.run(service.process_request(request))
            
            if result and result.success:
                print("✓ Document processing request successful!")
                
                if result.data:
                    print(f"✓ Document type: {result.data.document_type}")
                    # Access confidence through the correct attribute
                    confidence = getattr(result.data, 'extraction_confidence', None) or getattr(result.data, 'confidence', 0)
                    print(f"✓ Confidence: {confidence:.3f}")
                    print(f"✓ Processing time: {result.processing_time_ms:.0f}ms")
                    
                    structured_data = result.data.structured_data or {}
                    if structured_data:
                        print(f"✓ Structured data fields: {list(structured_data.keys())}")
                        
                        # Verify key fields are extracted
                        key_fields = ['farmer_name', 'scheme_name', 'mobile_number', 'aadhaar_number']
                        found_fields = [field for field in key_fields if field in structured_data]
                        if found_fields:
                            print(f"✓ Extracted key fields: {found_fields}")
                            
                            # Show some sample values
                            for field in found_fields[:3]:  # Show first 3
                                value = structured_data.get(field, '')
                                if value:
                                    print(f"  - {field}: {value}")
                        else:
                            print("⚠ No key fields found in structured data")
                    
                    # Check that we have meaningful extraction (not empty)
                    if structured_data and len(structured_data) > 2:
                        print("✓ Meaningful data extracted from PDF")
                        return True
                    else:
                        print("✗ Limited data extracted from PDF")
                        return False
                else:
                    print("✗ No data in processing result")
                    return False
            else:
                print(f"✗ Document processing failed: {result.error_message if result else 'No result'}")
                return False
                
        finally:
            # Clean up server
            server.shutdown()
            
    except Exception as e:
        print(f"✗ End-to-end test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_original_failure_scenario():
    """Test the specific scenario that was failing before the fix"""
    print("\nTesting original failure scenario...")
    print("Before fix: 'No OCR text available for processing'")
    print("After fix: Should extract text and process successfully")
    
    try:
        # Start test server
        server, port = start_test_server()
        print(f"✓ Test server started on http://localhost:{port}")
        
        try:
            from modules.document_processing.document_processing_service import DocumentProcessingService, DocumentProcessingRequest
            
            service = DocumentProcessingService()
            
            # Simulate the exact request that was failing
            request = DocumentProcessingRequest(
                processing_type="extract_structured",
                options={
                    "filename": "test.pdf",
                    "fileUrl": f"http://localhost:{port}/test.pdf"
                }
            )
            
            # Process the request
            result = asyncio.run(service.process_request(request))
            
            # Check if we get the original error
            if result and not result.success:
                error_msg = result.error_message or ""
                if "No OCR text available for processing" in error_msg:
                    print("✗ STILL GETTING THE ORIGINAL ERROR")
                    print(f"Error: {error_msg}")
                    return False
                else:
                    print(f"✓ Different error (not the original OCR issue): {error_msg}")
                    return True
            elif result and result.success:
                print("✓ SUCCESS - Original error is fixed!")
                return True
            else:
                print("✗ Unexpected result")
                return False
                
        finally:
            server.shutdown()
            
    except Exception as e:
        print(f"✗ Original failure scenario test failed: {e}")
        return False

def main():
    """Run end-to-end tests"""
    print("=" * 80)
    print("END-TO-END DOCUMENT PROCESSING TEST")
    print("Simulating the exact scenario that was failing before the fix")
    print("=" * 80)
    
    all_passed = True
    
    # Test complete end-to-end flow
    if not test_end_to_end_processing():
        all_passed = False
    
    # Test original failure scenario
    if not test_original_failure_scenario():
        all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✓ ALL END-TO-END TESTS PASSED")
        print("✓ The original bug is FIXED!")
        print("✓ Downloaded PDF files now generate OCR/text before extraction")
        print("✓ No more 'No OCR text available for processing' errors")
        print("✓ Complete pipeline: URL download -> OCR extraction -> workflow -> results")
    else:
        print("✗ SOME END-TO-END TESTS FAILED")
        print("✗ The original issue may not be fully resolved")
    print("=" * 80)
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
