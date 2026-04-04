#!/usr/bin/env python3
"""Debug script to understand the data structure"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from modules.document_processing.processors import DocumentProcessor
from modules.document_processing.classification_service import DocumentClassificationService
from modules.document_processing.extraction_service import DocumentExtractionService

def debug_structure():
    """Debug the data structure"""
    
    processor = DocumentProcessor(DocumentClassificationService(), DocumentExtractionService())
    
    # Simple OCR text for testing
    ocr_text = """
    Name: Test Farmer
    Aadhaar: 1234 5678 9012
    Application ID: APP-2024-001
    Date: 15/03/2024
    Scheme: Pradhan Mantri Kisan Samman Nidhi
    Amount: 6000
    Village: Test Village
    District: Test District
    """
    
    result = processor.process_document_workflow(
        file_data=b'', 
        filename='test.txt', 
        processing_type='full_process', 
        options={'ocr_text': ocr_text}
    )
    
    print("=== Full Result Structure ===")
    print("Keys in result:", list(result.keys()))
    
    data = result.get('data', {})
    print("\nKeys in data:", list(data.keys()))
    
    print("\n=== Extracted Data Structure ===")
    extracted_data = data.get('extracted_data', {})
    print("Keys in extracted_data:", list(extracted_data.keys()))
    print("Type of extracted_data:", type(extracted_data))
    
    # Check if it's the right structure for LLM analysis
    print("\n=== Checking for LLM Analysis ===")
    if isinstance(extracted_data, dict) and extracted_data:
        print("extracted_data is a non-empty dict - should trigger LLM analysis")
    else:
        print("extracted_data is empty or not a dict - no LLM analysis")
    
    # Print some sample data
    if extracted_data:
        print("\nSample extracted_data content:")
        for key, value in list(extracted_data.items())[:5]:
            print(f"  {key}: {value}")

if __name__ == "__main__":
    debug_structure()
