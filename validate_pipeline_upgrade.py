#!/usr/bin/env python3
"""
Pipeline Upgrade Validation Script
Quick check that all new components are syntactically correct and can be imported
"""

import sys
import os

def validate_imports():
    """Test that all new modules can be imported"""
    print("=" * 60)
    print("VALIDATING NEW PIPELINE COMPONENTS")
    print("=" * 60)
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Document Schemas
    try:
        from app.modules.document_processing.document_schemas import (
            DOCUMENT_SCHEMAS, get_schema, SCHEME_APPLICATION_SCHEMA,
            SUBSIDY_CLAIM_SCHEMA, INSURANCE_CLAIM_SCHEMA, GRIEVANCE_SCHEMA,
            FARMER_RECORD_SCHEMA, SUPPORTING_DOCUMENT_SCHEMA
        )
        print("✅ Test 1: Document Schemas - PASS")
        print(f"   Loaded {len(DOCUMENT_SCHEMAS)} schemas")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 1: Document Schemas - FAIL: {e}")
        tests_failed += 1
    
    # Test 2: Candidate Extraction Engine
    try:
        from app.modules.document_processing.candidate_extraction_engine import (
            CandidateExtractionEngine, ExtractionCandidate, CandidateSource
        )
        engine = CandidateExtractionEngine()
        print("✅ Test 2: Candidate Extraction Engine - PASS")
        print(f"   Engine initialized with {len(engine.semantic_rejections)} rejection rules")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 2: Candidate Extraction Engine - FAIL: {e}")
        tests_failed += 1
    
    # Test 3: Unified Extraction Orchestrator
    try:
        from app.modules.document_processing.unified_extraction_orchestrator import (
           UnifiedExtractionOrchestrator
        )
        # Don't instantiate (requires dependencies), just verify import
        print("✅ Test 3: Unified Extraction Orchestrator - PASS")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 3: Unified Extraction Orchestrator - FAIL: {e}")
        tests_failed += 1
    
    # Test 4: Money Extraction Validator
    try:
        from app.modules.document_processing.money_extraction_validator import (
            MoneyExtractionValidator
        )
        validator = MoneyExtractionValidator()
        print("✅ Test 4: Money Extraction Validator - PASS")
        print(f"   Validator has {len(validator.ALLOWED_AMOUNT_CONTEXTS)} context rules")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 4: Money Extraction Validator - FAIL: {e}")
        tests_failed += 1
    
    # Test 5: Extraction Integration Helper
    try:
        from app.modules.document_processing.extraction_integration_helper import (
            ExtractionIntegrationHelper
        )
        helper = ExtractionIntegrationHelper()
        print("✅ Test 5: Extraction Integration Helper - PASS")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 5: Extraction Integration Helper - FAIL: {e}")
        tests_failed += 1
    
    # Test 6: Enhanced Intelligence Service
    try:
        from app.modules.intelligence.intelligence_service import IntelligenceService
        intelligence = IntelligenceService()
        print("✅ Test 6: Intelligence Service (Enhanced) - PASS")
        # Check for new method
        if hasattr(intelligence, 'generate_officer_summary'):
            print("   ✓ generate_officer_summary() method present")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 6: Intelligence Service - FAIL: {e}")
        tests_failed += 1
    
    # Test 7: Enhanced ML Service
    try:
        from app.ml.ml_service import MLService
        ml = MLService()
        print("✅ Test 7: ML Service (Enhanced) - PASS")  
        # Check for new method
        if hasattr(ml, '_extract_ml_features'):
            print("   ✓ _extract_ml_features() method present")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 7: ML Service - FAIL: {e}")
        tests_failed += 1
    
    print("\n" + "=" * 60)
    print(f"VALIDATION RESULTS: {tests_passed} passed, {tests_failed} failed")
    print("=" * 60)
    
    return tests_failed == 0

def validate_basic_pipeline():
    """Test basic pipeline operations"""
    print("\n" + "=" * 60)
    print("VALIDATING BASIC PIPELINE OPERATIONS")
    print("=" * 60)
    
    tests_passed = 0
    tests_failed = 0
    
    try:
        # Test: Can create a candidate extraction engine and add candidates
        from app.modules.document_processing.candidate_extraction_engine import (
            CandidateExtractionEngine, ExtractionCandidate, CandidateSource
        )
        
        engine = CandidateExtractionEngine()
        
        # Add test candidates
        engine.add_candidate(
            field_name="farmer_name",
            value="Rajesh Kumar",
            source=CandidateSource.SEMANTIC_EXTRACTOR,
            confidence=0.95,
            semantic_type="person_name"
        )
        
        # Select best
        selected = engine.select_all_best_candidates()
        
        if "farmer_name" in selected and selected["farmer_name"].value == "Rajesh Kumar":
            print("✅ Test 1: Candidate Selection - PASS")
            tests_passed += 1
        else:
            print("❌ Test 1: Candidate Selection - FAIL")
            tests_failed += 1
            
    except Exception as e:
        print(f"❌ Test 1: Candidate Selection - FAIL: {e}")
        tests_failed += 1
    
    try:
        # Test: Money validator basic functionality
        from app.modules.document_processing.money_extraction_validator import (
            MoneyExtractionValidator
        )
        
        validator = MoneyExtractionValidator()
        
        # Should reject year
        is_valid, conf, reason = validator.validate_money_extraction(
            value="2024",
            field_name="requested_amount",
            surrounding_text="",
            document_type="scheme_application"
        )
        
        if not is_valid:
            print("✅ Test 2: Money Validator (Year Rejection) - PASS")
            tests_passed += 1
        else:
            print("❌ Test 2: Money Validator (Year Rejection) - FAIL")
            tests_failed += 1
            
    except Exception as e:
        print(f"❌ Test 2: Money Validator - FAIL: {e}")
        tests_failed += 1
    
    try:
        # Test: Schema validation
        from app.modules.document_processing.document_schemas import get_schema
        
        schema = get_schema("scheme_application")
        
        if schema and "farmer_name" in schema.get_required_field_names():
            print("✅ Test 3: Schema Validation - PASS")
            tests_passed += 1
        else:
            print("❌ Test 3: Schema Validation - FAIL")
            tests_failed += 1
            
    except Exception as e:
        print(f"❌ Test 3: Schema Validation - FAIL: {e}")
        tests_failed += 1
    
    print("\n" + "=" * 60)
    print(f"PIPELINE TESTS: {tests_passed} passed, {tests_failed} failed")
    print("=" * 60)
    
    return tests_failed == 0

if __name__ == "__main__":
    print("\n")
    print("*" * 60)
    print("* AGRICULTURAL OFFICE PIPELINE UPGRADE VALIDATION")
    print("* Date: April 4, 2026")
    print("*" * 60)
    print("\n")
    
    imports_ok = validate_imports()
    pipeline_ok = validate_basic_pipeline()
    
    print("\n" + "=" * 60)
    if imports_ok and pipeline_ok:
        print("✅ VALIDATION COMPLETE - ALL SYSTEMS READY")
        print("\nThe upgraded pipeline is ready for integration and testing.")
        print("\nNext steps:")
        print("1. Review PIPELINE_UPGRADE_COMPLETE.py for full overview")
        print("2. Check INTEGRATION_GUIDE.md for activation instructions")
        print("3. Run standard test suites")
        print("4. Deploy to test environment")
    else:
        print("⚠️  VALIDATION INCOMPLETE - REVIEW FAILURES ABOVE")
        print("\nFix the above issues before deployment.")
    print("=" * 60)
    print("\n")
    
    sys.exit(0 if (imports_ok and pipeline_ok) else 1)
