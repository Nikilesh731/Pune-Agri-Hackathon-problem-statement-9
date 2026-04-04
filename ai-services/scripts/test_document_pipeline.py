#!/usr/bin/env python3
"""
End-to-End OCR Text Validation Pack for Agricultural Document Processing Pipeline

Tests all 6 supported document types using realistic OCR-like text samples.
Uses the existing rebuilt pipeline through DocumentProcessor with classification_service 
and extraction_service.

Document Types Tested:
- scheme_application
- farmer_record  
- grievance
- insurance_claim
- subsidy_claim
"""

import sys
import os
import asyncio
from pathlib import Path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

app_path = Path(__file__).parent.parent / "app"
sys.path.insert(0, str(app_path))

from modules.document_processing.processors import DocumentProcessor
from modules.document_processing.classification_service import DocumentClassificationService
from modules.document_processing.extraction_service import DocumentExtractionService


def create_realistic_ocr_samples():
    """Create realistic OCR-like text samples for each document type"""
    
    return {
        "scheme_application": """
PRADHAN MANTRI KISAN SAMMAN NIDHI SCHEME APPLICATION FORM

Applicant Details:
Name: Rajesh Kumar Sharma
Father/Husband Name: Suresh Chand Sharma
Age: 45 years
Gender: Male
Category: OBC

Address:
Village: Rampur
Post: Badi
District: Jalaun
State: Uttar Pradesh
Pin Code: 285204

Contact Information:
Mobile Number: 9876543210
Email ID: rajesh.sharma@email.com
Aadhaar Number: 234567890123

Land Details:
Khasra Number: 456/789
Total Land Area: 2.5 hectares
Irrigation Source: Tube well

Bank Details:
Bank Name: State Bank of India
Branch: Jalaun
Account Number: 1234567890123456
IFSC Code: SBIN0001234

Declaration:
I hereby declare that the information provided is true and correct to the best of my knowledge.
I understand that any false information may lead to rejection of my application.

Applicant Signature: ________________
Date: 15/03/2024

Application ID: PMKISAN-UP-2024-001234
Scheme Name: Pradhan Mantri Kisan Samman Nidhi
Benefit Type: Financial assistance of Rs. 6000 per year
""",

        "farmer_record": """
FARMER REGISTRATION RECORD

Personal Information:
Farmer ID: FR-UP-2024-04567
Name: Ram Singh Yadav
Father Name: Gopal Singh Yadav
Date of Birth: 15/08/1975
Age: 48 years
Gender: Male
Marital Status: Married

Contact Details:
Mobile: 9123456789
Email: ram.yadav@farmmail.com
Aadhaar: 345678901234

Residential Address:
Village: Chandpur
Tehsil: Konch
District: Auraiya
State: Uttar Pradesh
Pin Code: 206122

Family Details:
Spouse Name: Smt. Geeta Devi
Number of Children: 3 (2 sons, 1 daughter)

Land Holdings:
Khasra No. 123 - Area: 1.2 hectares - Crop: Wheat
Khasra No. 124 - Area: 0.8 hectares - Crop: Pulses
Khasra No. 125 - Area: 0.5 hectares - Crop: Vegetables
Total Land Area: 2.5 hectares

Land Ownership Type: Self-owned
Irrigation Facilities: Canal and Tube well

Registration Date: 01/01/2024
Registration Valid Until: 31/12/2029
""",

        "grievance": """
GRIEVANCE PETITION

To,
The District Agriculture Officer
Auraiya District
Uttar Pradesh

Subject: COMPLAINT REGARDING DELAY IN SUBSIDY PAYMENT

Respected Sir/Madam,

I am Ram Singh Yadav, a resident of village Chandpur, tehsil Konch, district Auraiya. 
I am writing to bring to your kind attention the issue of delayed subsidy payment.

I had applied for the Crop Insurance Scheme on 15th June 2023 for the Kharif season. 
My application number is INS-UP-2023-789012. The premium amount of Rs. 2,500 was paid 
through my bank account (SBI, Account No. 1234567890123456).

As per the scheme guidelines, the subsidy amount was to be credited within 30 days 
of application processing. However, it has been more than 8 months now, and I have 
not received any payment. I have made repeated inquiries at the local agriculture 
office, but no satisfactory response has been provided.

Due to this delay, I am facing financial difficulties in arranging resources for 
the current Rabi season. The delayed payment is causing significant hardship 
for my family.

I request your kind intervention to resolve this matter urgently and ensure 
that the pending subsidy payment is released at the earliest.

Thank you for your attention to this important matter.

Sincerely,
Ram Singh Yadav
Mobile: 9123456789
Aadhaar: 345678901234
Date: 20/02/2024

URGENT ATTENTION REQUIRED - PENDING FOR 8 MONTHS
""",

        "insurance_claim": """
CROP INSURANCE CLAIM FORM

Policy Information:
Policy Number: CROP-INS-2023-456789
Insurance Company: Pradhan Mantri Fasal Bima Yojana
Policy Period: 01/04/2023 to 31/03/2024
Premium Paid: Rs. 3,500

Insured Farmer Details:
Name: Suresh Kumar Patel
Father Name: Ramesh Patel
Address: Village Pipri, District Banda, UP
Mobile: 8765432109
Aadhaar: 456789012345

Crop Information:
Crop Type: Wheat
Season: Rabi 2023-24
Area Insured: 3.0 hectares
Expected Yield: 25 quintals per hectare

Loss Information:
Date of Loss: 15/01/2024
Cause of Loss: Untimely rainfall and hailstorm
Percentage of Damage: 70%
Actual Yield: 7.5 quintals per hectare

Claim Details:
Claim Amount Requested: Rs. 75,000
Claim Date: 05/02/2024
Claim Reference: CLAIM-2024-001234

Supporting Documents:
1. Crop cutting experiment report
2. Weather department report
3. Land ownership documents
4. Bank account details

Bank Information:
Bank Name: Punjab National Bank
Branch: Banda
Account Number: 9876543210987654
IFSC: PUNB0009876

Declaration:
I hereby declare that the information provided is true and accurate. 
I understand that false claims may lead to legal action.

Applicant Signature: ________________
Date: 05/02/2024
""",

        "subsidy_claim": """
AGRICULTURAL EQUIPMENT SUBSIDY CLAIM

Applicant Information:
Name: Mahendra Singh Tomar
Father Name: Late Thakur Singh Tomar
Village: Karari, District Kaushambi, UP
Mobile: 7654321098
Aadhaar: 567890123456

Subsidy Details:
Subsidy Type: Agricultural Machinery Subsidy Scheme
Equipment Purchased: Tractor with implements
Purchase Date: 10/12/2023
Invoice Number: INV-2023-456789
Dealer Name: Greenfield Equipment Pvt Ltd
Dealer Address: Kanpur, UP

Financial Details:
Total Equipment Cost: Rs. 6,50,000
Subsidy Percentage: 40%
Subsidy Amount Requested: Rs. 2,60,000
Farmer Contribution: Rs. 3,90,000

Payment Details:
Payment Mode: Bank Transfer
Bank Account: 5678901234567890
Bank Name: Bank of Baroda
Branch: Kaushambi
IFSC Code: BARB0KAUSHAMBI

Land Details:
Khasra Number: 789/1011
Total Land Area: 4.5 hectares
Land Use: Agricultural purpose only

Supporting Documents Attached:
1. Original purchase invoice
2. Land ownership certificate
3. Bank account details
4. Aadhaar card copy
5. Equipment delivery receipt

Declaration:
I confirm that I have not received any subsidy for this equipment under any other scheme. 
All documents submitted are genuine and correct.

Applicant Signature: ________________
Date: 25/12/2023

Application Status: Under Process
Reference Number: SUBSIDY-UP-2023-001234
""",

        "supporting_document": """
BANK PASSBOOK CERTIFICATE

State Bank of India
Branch: Civil Lines, Kanpur
Account Holder: Raj Kumar Gupta
Account Number: 123456789012
Account Type: Savings Account
IFSC Code: SBIN0005678

Account Statement Summary:
Opening Balance: Rs. 25,000
Total Credits: Rs. 1,25,000
Total Debits: Rs. 75,000
Closing Balance: Rs. 75,000

Account Holder Details:
Name as per Bank Records: Raj Kumar Gupta
Father Name: Shiv Kumar Gupta
Address: 123, Civil Lines, Kanpur - 208001
Mobile Number: 9876543210
PAN Number: ABCDE1234F
Aadhaar Linked: Yes

This is to certify that the above information is correct as per our records.
The account is active and in good standing.

Certified by: _______________
Bank Manager
State Bank of India
Date: 15/03/2024
Bank Seal: [OFFICIAL SEAL]

Document Type: Bank Passbook Copy
Purpose: Agricultural Loan Application
Verification Status: Verified
""",

        # NOISY TEST CASES FOR ROBUSTNESS VALIDATION
        "noisy_grievance": """
GRIEVANCE PETITION

To,
The District Agriculture Officer
Auraiya District
Uttar Pradesh

Subject: COMPLAINT REGARDING DELAY IN SUBSIDY PAYMENT

From: District Agriculture Officer
Office: Main Branch
Mobile: UP Mobile
Village: Civil Lines

Applicant Information
Claimant Name: Office
Complainant: Branch Manager
Applicant Name: Main Branch

Dear Sir/Madam,

I am writing to file a grievance regarding the non-payment of my agricultural subsidy for the year 2023-24. 

Name: Ramesh Kumar
Village: Chandpur, District: Auraiya
Mobile: 9876543210
Aadhaar: 234567890123

Issue Type: Delay in PMKISAN payment
Description: I have not received my PMKISAN subsidy installment for the Kharif season 2023. The payment was supposed to be credited to my bank account in December 2023 but till date I have not received any amount.

Requested Amount: Rs. 6000
Bank Account: 1234567890123456
Bank: State Bank of India

Please look into this matter and expedite the payment.

Yours sincerely,
Ramesh Kumar
Village: Chandpur
District: Auraiya
Date: 15/02/2024
""",

        "noisy_subsidy_claim": """
AGRICULTURAL EQUIPMENT SUBSIDY CLAIM

Applicant Information
Personal Information
Policy Information
Scheme Details

Name: Satyendra Singh
Village: Karari
District: Kaushambi
Location: UP
Mobile

From: UP Mobile
To: District Agriculture Officer

Subsidy Details:
Subsidy Type: Agricultural Machinery Subsidy Scheme
Equipment Purchased: Tractor with implements
Purchase Date: 10/12/2023
Invoice Number: INV-2023-456789

Financial Details:
Total Equipment Cost: Rs. 6,50,000
Subsidy Percentage: 40%
Subsidy Amount Requested: Rs. 2,60,000
Farmer Contribution: Rs. 3,90,000

Address Details:
Village: Karari
District: Kaushambi
State: Uttar Pradesh
Mobile: 7654321098
Location: UP Mobile

Bank Information:
Bank Name: Bank of Baroda
Branch: Main Branch
Account Number: 5678901234567890
IFSC Code: BARB0KAUSHAMBI

Declaration:
I confirm that I have not received any subsidy for this equipment under any other scheme.

Applicant: Satyendra Singh
Date: 25/12/2023
Reference Number: SUBSIDY-UP-2023-001234
""",

        "noisy_supporting_document": """
BANK PASSBOOK CERTIFICATE

State Bank of India
Main Branch
Branch Manager
Office: Civil Lines, Kanpur

Account Holder Information
Personal Information
Policy Information
Claimant Name

Name as per Bank Records: Civil Lines
From: Main Branch
To: Bank Manager
Applicant Information: Office

Account Number: 123456789012
Account Type: Savings Account
IFSC Code: SBIN0005678

Address Details:
Village: Civil Lines
District: Kanpur
Location: Main Branch
Office: State Bank of India

Account Holder Details:
Name: Amit Kumar Gupta
Father Name: Shiv Kumar Gupta
Address: 123, Civil Lines, Kanpur - 208001
Mobile Number: 9876543210
Aadhaar Number: 456789012345

This is to certify that the above information is correct as per our records.
The account is active and in good standing.

Certified by: Branch Manager
Bank: State Bank of India
Branch: Main Branch
Date: 15/03/2024

Document Type: Bank Passbook Copy
Purpose: Agricultural Loan Application
Verification Status: Verified
"""
    }


async def run_single_test(service, test_name, ocr_text, expected_type, filename):
    """Run a single test case and return results"""
    
    print(f"\n{'='*60}")
    print(f"TEST: {test_name}")
    print(f"Expected Type: {expected_type}")
    print(f"{'='*60}")
    
    try:
        # Run full service workflow
        result = await service.process_document(
            file_data=b"",  # Empty file data since we're providing OCR text
            filename=filename,
            processing_type="full_process",
            options={"ocr_text": ocr_text}
        )
        
        # Extract key information
        success = result.success
        data = result.data.model_dump() if result.data else {}
        classified_type = data.get('document_type', 'unknown')
        classification_confidence = data.get('classification_confidence', 0.0)
        structured_data = data.get('structured_data', {})
        missing_fields = data.get('missing_fields', [])
        confidence = data.get('extraction_confidence', 0.0)
        reasoning = data.get('reasoning', [])
        risk_flags = data.get('risk_flags', [])
        decision_support = data.get('decision_support', {})
        
        # Print results
        print(f"✅ Success: {success}")
        print(f"📋 Classified Type: {classified_type}")
        print(f"📊 Classification Confidence: {classification_confidence:.3f}")
        print(f"🎯 Extraction Confidence: {confidence:.3f}")
        print(f"📝 Structured Data Fields: {len(structured_data)}")
        print(f"⚠️  Missing Fields: {missing_fields}")
        print(f"🚨 Risk Flags: {len(risk_flags)}")
        print(f"💡 Decision Support: {decision_support.get('decision', 'unknown')}")
        
        # Show AI fields if available
        ai_summary = data.get('ai_summary')
        if ai_summary:
            print(f"🤖 AI Summary: {ai_summary}")
        
        if structured_data:
            print(f"\n📋 Extracted Key Fields:")
            for key, value in list(structured_data.items())[:8]:  # Show first 8 fields
                print(f"  • {key}: {str(value)[:50]}{'...' if len(str(value)) > 50 else ''}")
        
        if reasoning:
            print(f"\n🧠 Reasoning (first 3 items):")
            for reason in reasoning[:3]:
                print(f"  • {reason}")
        
        if risk_flags:
            print(f"\n🚨 Risk Flags:")
            for flag in risk_flags[:3]:  # Show first 3 flags
                print(f"  • {flag.get('severity', 'unknown')}: {flag.get('message', 'no message')}")
        
        # Determine if test passed with strict validation criteria
        has_reasoning_missing = any(
            isinstance(r, str) and r.startswith("Missing required fields:")
            for r in reasoning
        )
        
        # Adjust validation based on document type requirements
        # Some handlers (like supporting_document) have no required fields
        no_required_fields_types = ['supporting_document']
        
        # For types with no required fields, don't check missing_fields
        if classified_type in no_required_fields_types:
            test_passed = (
                success and
                classified_type == expected_type and
                structured_data and
                classification_confidence > 0.0
            )
        else:
            # For types with required fields, check missing_fields
            test_passed = (
                success and
                classified_type == expected_type and
                structured_data and
                classification_confidence > 0.0 and
                len(missing_fields) == 0 and
                not has_reasoning_missing
            )
        
        print(f"\n🏁 TEST RESULT: {'✅ PASSED' if test_passed else '❌ FAILED'}")
        
        return {
            'test_name': test_name,
            'expected_type': expected_type,
            'actual_type': classified_type,
            'success': success,
            'test_passed': test_passed,
            'classification_confidence': classification_confidence,
            'extraction_confidence': confidence,
            'structured_data_count': len(structured_data),
            'missing_fields_count': len(missing_fields),
            'risk_flags_count': len(risk_flags),
            'validation_errors': [],
            'error': getattr(result, 'error_message', None)
        }
        
    except Exception as e:
        print(f"❌ CRASH: {str(e)}")
        return {
            'test_name': test_name,
            'expected_type': expected_type,
            'actual_type': 'crash',
            'success': False,
            'test_passed': False,
            'classification_confidence': 0.0,
            'extraction_confidence': 0.0,
            'structured_data_count': 0,
            'missing_fields_count': 0,
            'risk_flags_count': 0,
            'validation_errors': [f"Test execution error: {e}"],
            'error': str(e)
        }


def main():
    """Main test execution function"""
    
    print("🌾 Agricultural Document Processing Pipeline - End-to-End Validation")
    print("="*80)
    print("Testing all 6 document types with realistic OCR samples")
    print("Using: DocumentProcessor with classification_service and extraction_service")
    print("="*80)
    
    # Initialize the pipeline services
    try:
        from modules.document_processing.document_processing_service import DocumentProcessingService
        service = DocumentProcessingService()
        
        print("✅ Pipeline services initialized successfully")
        
    except Exception as e:
        print(f"❌ Failed to initialize pipeline services: {e}")
        return
    
    # Get OCR samples
    samples = create_realistic_ocr_samples()
    
    # Run all tests
    results = []
    
    test_cases = [
        ("scheme_application", "scheme_application_test.txt"),
        ("farmer_record", "farmer_record_test.txt"),
        ("grievance", "grievance_test.txt"),
        ("insurance_claim", "insurance_claim_test.txt"),
        ("subsidy_claim", "subsidy_claim_test.txt"),
        ("supporting_document", "supporting_document_test.txt")
    ]
    
    for doc_type, filename in test_cases:
        ocr_text = samples[doc_type]
        test_name = f"{doc_type.upper()} Document Test"
        
        result = asyncio.run(run_single_test(service, test_name, ocr_text, doc_type, filename))
        results.append(result)
    
    # NOISY TEST CASES - Specific robustness validation
    print(f"\n{'='*80}")
    print("🔧 ROBUSTNESS VALIDATION - NOISY DOCUMENT TESTS")
    print(f"{'='*80}")
    
    noisy_test_cases = [
        ("noisy_grievance", "grievance", "noisy_grievance_test.txt"),
        ("noisy_subsidy_claim", "subsidy_claim", "noisy_subsidy_claim_test.txt"),
        ("noisy_supporting_document", "supporting_document", "noisy_supporting_document_test.txt")
    ]
    
    for noisy_type, expected_type, filename in noisy_test_cases:
        ocr_text = samples[noisy_type]
        test_name = f"NOISY {expected_type.upper()} Robustness Test"
        
        result = asyncio.run(run_noisy_test(service, test_name, ocr_text, expected_type, filename))
        results.append(result)
    
    # Print summary
    print(f"\n{'='*80}")
    print("📊 FINAL TEST SUMMARY")
    print(f"{'='*80}")
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r['test_passed'])
    failed_tests = total_tests - passed_tests
    
    print(f"📈 Total Tests: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    print(f"📊 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if failed_tests > 0:
        print(f"\n❌ FAILED TESTS:")
        for result in results:
            if not result['test_passed']:
                print(f"  • {result['test_name']}")
                print(f"    Expected: {result['expected_type']}, Got: {result['actual_type']}")
                if result['error']:
                    print(f"    Error: {result['error']}")
    
    print(f"\n🎯 Pipeline Validation Complete!")
    print(f"{'='*80}")
    
    return passed_tests == total_tests


async def run_noisy_test(service, test_name, ocr_text, expected_type, filename):
    """Run noisy test case with specific robustness validation"""
    
    print(f"\n{'='*60}")
    print(f"NOISY TEST: {test_name}")
    print(f"Expected Type: {expected_type}")
    print(f"{'='*60}")
    
    try:
        # Run full service workflow
        result = await service.process_document(
            file_data=b"",  # Empty file data since we're providing OCR text
            filename=filename,
            processing_type="full_process",
            options={"ocr_text": ocr_text}
        )
        
        # Extract key information
        success = result.success
        data = result.data.model_dump() if result.data else {}
        classified_type = data.get('document_type', 'unknown')
        classification_confidence = data.get('classification_confidence', 0.0)
        structured_data = data.get('structured_data', {})
        missing_fields = data.get('missing_fields', [])
        confidence = data.get('extraction_confidence', 0.0)
        reasoning = data.get('reasoning', [])
        risk_flags = data.get('risk_flags', [])
        decision_support = data.get('decision_support', {})
        
        # Print results
        print(f"✅ Success: {success}")
        print(f"📋 Classified Type: {classified_type}")
        print(f"📊 Classification Confidence: {classification_confidence:.3f}")
        print(f"🎯 Extraction Confidence: {confidence:.3f}")
        print(f"📝 Structured Data Fields: {len(structured_data)}")
        print(f"⚠️  Missing Fields: {missing_fields}")
        print(f"🚨 Risk Flags: {len(risk_flags)}")
        print(f"💡 Decision Support: {decision_support.get('decision', 'unknown')}")
        
        # Show AI fields if available
        summary = data.get('summary', '')
        case_insight = data.get('case_insight', [])
        predictions = data.get('predictions', {})
        
        if summary:
            print(f"📄 Summary: {summary}")
        if case_insight:
            print(f"💭 Case Insight: {case_insight}")
        if predictions:
            print(f"🔮 Predictions: {predictions}")
        
        # Print structured data
        print(f"\n📋 Extracted Fields:")
        for field, value in structured_data.items():
            print(f"  • {field}: {value}")
        
        # NOISY TEST SPECIFIC VALIDATION
        print(f"\n🔍 ROBUSTNESS VALIDATION:")
        validation_errors = []
        
        # Check for obvious junk in protected fields
        farmer_name = structured_data.get('farmer_name', '')
        location = structured_data.get('location', '')
        
        # Reject obvious junk in farmer_name
        junk_names = ['civil lines', 'main branch', 'office', 'branch manager', 'district agriculture officer', 
                     'applicant information', 'claimant', 'complainant', 'from', 'to']
        
        if farmer_name and farmer_name.lower() in junk_names:
            validation_errors.append(f"Junk farmer_name detected: '{farmer_name}'")
            print(f"❌ JUNK farmer_name: '{farmer_name}'")
        elif farmer_name:
            print(f"✅ Clean farmer_name: '{farmer_name}'")
        else:
            print(f"✅ No farmer_name (better than wrong)")
        
        # Reject obvious junk in location
        junk_locations = ['up mobile', 'from', 'to', 'office', 'main branch', 'district agriculture officer']
        
        if location and location.lower() in junk_locations:
            validation_errors.append(f"Junk location detected: '{location}'")
            print(f"❌ JUNK location: '{location}'")
        elif location:
            print(f"✅ Clean location: '{location}'")
        else:
            print(f"✅ No location (better than wrong)")
        
        # Document-type specific validation
        if expected_type == 'grievance':
            # Check that applicant_name/complainant junk doesn't survive
            for junk_field in ['applicant_name', 'complainant', 'claimant']:
                junk_value = structured_data.get(junk_field, '')
                if junk_value and junk_value.lower() in junk_names:
                    validation_errors.append(f"Junk {junk_field} detected: '{junk_value}'")
                    print(f"❌ JUNK {junk_field}: '{junk_value}'")
            
            # Check that description doesn't contain header fragments
            description = structured_data.get('description', '')
            if description:
                grievance_junk_patterns = [
                    'applicant information', 'claimant name', 'office', 'district agriculture officer',
                    'subject', 'from', 'to', 'main branch', 'branch manager'
                ]
                description_lower = description.lower()
                for junk_pattern in grievance_junk_patterns:
                    if junk_pattern in description_lower:
                        validation_errors.append(f"Grievance description contains header junk: '{junk_pattern}'")
                        print(f"❌ GRIEVANCE DESCRIPTION JUNK: '{junk_pattern}' in description")
                        break
            
            # Check that address doesn't contain officer junk
            address = structured_data.get('address', '')
            if address:
                address_junk_patterns = ['district agriculture officer', 'subject', 'main branch', 'office']
                address_lower = address.lower()
                for junk_pattern in address_junk_patterns:
                    if junk_pattern in address_lower:
                        validation_errors.append(f"Grievance address contains officer junk: '{junk_pattern}'")
                        print(f"❌ GRIEVANCE ADDRESS JUNK: '{junk_pattern}' in address")
                        break
        
        elif expected_type == 'supporting_document':
            # For supporting documents, missing farmer_name is acceptable
            if not farmer_name:
                print(f"✅ No farmer_name in supporting document (acceptable)")
            
            # Check that amount fields don't contain 10+ digit identifier-style numbers
            amount_fields = ['requested_amount', 'claim_amount', 'subsidy_amount', 'amount']
            for amount_field in amount_fields:
                amount_value = structured_data.get(amount_field, '')
                if amount_value:
                    # Clean amount and check if it's a 10+ digit ID-style number
                    clean_amount = str(amount_value).replace(',', '').replace('₹', '').replace('$', '').strip()
                    if clean_amount.isdigit() and len(clean_amount) >= 10:
                        validation_errors.append(f"Supporting document {amount_field} contains ID-style number: '{amount_value}'")
                        print(f"❌ SUPPORTING DOC AMOUNT JUNK: {amount_field} = '{amount_value}' (looks like ID)")
        
        elif expected_type == 'subsidy_claim':
            subsidy_amount = structured_data.get("requested_amount", "")
            print(f"💰 Subsidy Requested Amount: '{subsidy_amount}'")
            if subsidy_amount != "260000":
                validation_errors.append(f"Subsidy amount parsing failed: expected '260000', got '{subsidy_amount}'")
        
        # Check reasoning for missing required fields indicators
        has_reasoning_missing = False
        if reasoning:
            for r in reasoning:
                if isinstance(r, str):
                    # Clean the reasoning string for comparison
                    r_clean = str(r).strip().lower()
                    print(f"DEBUG: Checking reasoning item: {repr(r_clean)}")
                    # Look for "missing required fields:" that indicates actual missing fields (not "none")
                    if "missing required fields:" in r_clean and not "missing required fields: none" in r_clean:
                        print(f"DEBUG: FOUND 'missing required fields:' (actual missing) in reasoning")
                        has_reasoning_missing = True
                        break
                    else:
                        print(f"DEBUG: No 'missing required fields:' (actual missing) found in reasoning")
        
        # PRODUCTION HARDENING VALIDATION
        # 1. Amount parsing validation for baseline tests
        if expected_type == "scheme_application" and not test_name.startswith("NOISY"):
            requested_amount = structured_data.get("requested_amount", "")
            print(f"💰 Scheme Requested Amount: '{requested_amount}'")
            if requested_amount != "6000":
                validation_errors.append(f"Scheme amount parsing failed: expected '6000', got '{requested_amount}'")
        
        elif expected_type == "insurance_claim" and not test_name.startswith("NOISY"):
            claim_amount = structured_data.get("claim_amount", "")
            print(f"💰 Insurance Claim Amount: '{claim_amount}'")
            if claim_amount != "75000":
                validation_errors.append(f"Insurance amount parsing failed: expected '75000', got '{claim_amount}'")
        
        # 2. Location junk validation for noisy subsidy
        if test_name == "NOISY_SUBSIDY_CLAIM":
            location = structured_data.get("location", "")
            village = structured_data.get("village", "")
            district = structured_data.get("district", "")
            print(f"📍 Location fields - Location: '{location}', Village: '{village}', District: '{district}'")
            
            # Check for header junk in location fields
            junk_fragments = ["Applicant Information", "Personal Information", "Policy Information", "Scheme Details"]
            for field_name, field_value in [("location", location), ("village", village), ("district", district)]:
                if any(junk in field_value for junk in junk_fragments):
                    validation_errors.append(f"Location junk detected in {field_name}: '{field_value}'")
        
        # 3. ML model validation
        prediction_method = predictions.get("prediction_method", "")
        print(f"🤖 Prediction Method: {prediction_method}")
        
        # Check if model claims to be trained but no artifact exists
        if prediction_method == "trained_random_forest":
            model_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'modules', 'document_processing', 'priority_model.pkl')
            if not os.path.exists(model_path):
                validation_errors.append("Prediction method claims 'trained_random_forest' but no model artifact found")
        
        # NEW: Check if model exists but prediction_method is still fallback
        model_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'modules', 'document_processing', 'priority_model.pkl')
        if os.path.exists(model_path) and prediction_method == "rule_based_fallback":
            validation_errors.append("Model artifact exists but prediction_method is still 'rule_based_fallback' instead of 'trained_random_forest'")
            print(f"❌ ML MODEL NOT USED: Model exists but got '{prediction_method}'")
        
        # Determine test passed with stricter validation criteria
        print(f"DEBUG: missing_fields = {missing_fields}")
        print(f"DEBUG: len(missing_fields) = {len(missing_fields)}")
        print(f"DEBUG: has_reasoning_missing = {has_reasoning_missing}")
        
        test_passed = (
            success and
            classified_type == expected_type and
            structured_data and
            classification_confidence > 0.0 and
            len(missing_fields) == 0 and
            not has_reasoning_missing and
            len(validation_errors) == 0  # No production hardening errors
        )
        
        print(f"DEBUG: validation_errors = {validation_errors}")
        print(f"DEBUG: test_passed = {test_passed}")
        
        # Report validation errors
        if validation_errors:
            print(f"\n❌ PRODUCTION HARDENING ERRORS:")
            for error in validation_errors:
                print(f"   - {error}")
        
        print(f"\n🎯 NOISY TEST RESULT: {'✅ PASSED' if test_passed else '❌ FAILED'}")
        if validation_errors:
            print(f"   Issues found: {len(validation_errors)}")
        
        return {
            'test_name': test_name,
            'expected_type': expected_type,
            'actual_type': classified_type,
            'success': success,
            'test_passed': test_passed,
            'classification_confidence': classification_confidence,
            'extraction_confidence': confidence,
            'structured_data_count': len(structured_data),
            'missing_fields_count': len(missing_fields),
            'risk_flags_count': len(risk_flags),
            'validation_errors': validation_errors,
            'error': None
        }
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return {
            'test_name': test_name,
            'expected_type': expected_type,
            'actual_type': 'error',
            'success': False,
            'test_passed': False,
            'classification_confidence': 0.0,
            'extraction_confidence': 0.0,
            'structured_data_count': 0,
            'missing_fields_count': 0,
            'risk_flags_count': 0,
            'validation_errors': [f"Test execution error: {e}"],
            'error': str(e)
        }


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
