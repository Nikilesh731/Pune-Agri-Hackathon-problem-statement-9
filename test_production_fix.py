#!/usr/bin/env python3
"""
Production Deployment Fix Test
Tests the runtime health check fixes for PaddleOCR initialization issues
"""
import sys
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the AI services path to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai-services', 'app'))

def test_runtime_health_check():
    """Test the runtime health check with graceful PaddleOCR handling"""
    logger.info("=== Testing Runtime Health Check Fix ===")
    
    try:
        # Import the fixed runtime health module
        from modules.document_processing.runtime_health import RuntimeHealthChecker, ensure_runtime_ready, get_runtime_health
        
        logger.info("✅ Runtime health module imported successfully")
        
        # Test health checker initialization
        health_checker = RuntimeHealthChecker()
        logger.info("✅ RuntimeHealthChecker initialized successfully")
        
        # Test Python dependencies check
        logger.info("🔍 Testing Python dependencies check...")
        python_deps = health_checker.check_python_dependencies()
        
        logger.info("📊 Python Dependencies Status:")
        for dep, status in python_deps.items():
            status_icon = "✅" if status else "⚠️"
            logger.info(f"  {status_icon} {dep}: {status}")
        
        # Test full health check
        logger.info("🔍 Running full health check...")
        health_status = health_checker.run_full_health_check()
        
        logger.info(f"📊 Overall Health Status: {health_status['overall_status']}")
        logger.info(f"📊 Missing Critical Dependencies: {health_status['missing_critical']}")
        
        # Test ensure_runtime_ready function
        logger.info("🔍 Testing ensure_runtime_ready...")
        try:
            ensure_runtime_ready()
            logger.info("✅ ensure_runtime_ready() completed successfully")
        except Exception as e:
            logger.error(f"❌ ensure_runtime_ready() failed: {e}")
            return False
        
        # Test get_runtime_health function
        logger.info("🔍 Testing get_runtime_health...")
        try:
            health = get_runtime_health()
            logger.info("✅ get_runtime_health() completed successfully")
            logger.info(f"📊 Health status: {health['overall_status']}")
        except Exception as e:
            logger.error(f"❌ get_runtime_health() failed: {e}")
            return False
        
        logger.info("🎉 Runtime health check test PASSED")
        return True
        
    except Exception as e:
        logger.error(f"❌ Runtime health check test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_document_processing_service():
    """Test DocumentProcessingService initialization with the fixes"""
    logger.info("=== Testing Document Processing Service ===")
    
    try:
        # Import the DocumentProcessingService
        from modules.document_processing.document_processing_service import DocumentProcessingService
        
        logger.info("✅ DocumentProcessingService imported successfully")
        
        # Test service initialization
        logger.info("🔍 Initializing DocumentProcessingService...")
        service = DocumentProcessingService()
        
        logger.info("✅ DocumentProcessingService initialized successfully")
        logger.info(f"📊 PaddleOCR Service Status: {'Available' if service.paddle_ocr_service else 'Not Available (Graceful Degradation)'}")
        
        # Test that the service can handle basic operations
        logger.info("🔍 Testing service methods...")
        
        # Test supported processing types
        processing_types = service.get_supported_processing_types()
        logger.info(f"✅ Supported processing types: {len(processing_types)} types available")
        
        logger.info("🎉 Document processing service test PASSED")
        return True
        
    except Exception as e:
        logger.error(f"❌ Document processing service test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    logger.info("🚀 Starting Production Deployment Fix Test")
    
    # Test runtime health check
    health_test_passed = test_runtime_health_check()
    
    # Test document processing service
    service_test_passed = test_document_processing_service()
    
    # Overall result
    logger.info("=== Test Results ===")
    logger.info(f"Runtime Health Check: {'✅ PASSED' if health_test_passed else '❌ FAILED'}")
    logger.info(f"Document Processing Service: {'✅ PASSED' if service_test_passed else '❌ FAILED'}")
    
    if health_test_passed and service_test_passed:
        logger.info("🎉 All tests PASSED - Ready for production deployment!")
        return 0
    else:
        logger.error("❌ Some tests FAILED - Fix issues before deployment")
        return 1

if __name__ == "__main__":
    sys.exit(main())
