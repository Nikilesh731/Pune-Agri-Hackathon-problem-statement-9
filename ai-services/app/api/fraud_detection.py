"""
Fraud Detection API
Provides fraud detection for agricultural applications
"""
from fastapi import APIRouter
from typing import Dict, Any, List
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/detect")
def detect_fraud(application_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detect fraud indicators in application data
    
    Args:
        application_data: Application data including extracted fields
        
    Returns:
        Fraud score, risk level, and indicators
    """
    try:
        # Simple fraud detection logic for demo
        fraud_score = 0.1  # Default low risk
        risk_indicators = []
        
        # Check for potential fraud indicators - handle both data formats
        # Format 1: Direct fields (new format)
        farmer_name = application_data.get('farmer_name', '')
        aadhaar_number = application_data.get('aadhaar_number', '')
        land_size = application_data.get('land_size', '')
        
        # Format 2: Nested in application_data (old format for compatibility)
        if not farmer_name and 'application_data' in application_data:
            app_data = application_data['application_data']
            if isinstance(app_data, dict):
                farmer_name = app_data.get('farmer_name', '')
                aadhaar_number = app_data.get('aadhaar_number', '')
                land_size = app_data.get('land_size', '')
        
        # Format 3: Nested in applicantInfo (another old format)
        if not aadhaar_number and 'applicantInfo' in application_data:
            applicant_info = application_data['applicantInfo']
            if isinstance(applicant_info, dict):
                aadhaar_number = applicant_info.get('aadhaarNumber', '')
                if not farmer_name:
                    farmer_name = applicant_info.get('name', '')
        
        # Indicator 1: Missing Aadhaar
        if not aadhaar_number:
            fraud_score += 0.3
            risk_indicators.append("Missing Aadhaar number")
        
        # Indicator 2: Suspicious land size patterns
        if land_size:
            try:
                # Extract numeric value from land size
                import re
                land_match = re.search(r'(\d+(?:\.\d+)?)', str(land_size))
                if land_match:
                    land_value = float(land_match.group(1))
                    if land_value > 100:  # Unusually large land holding
                        fraud_score += 0.2
                        risk_indicators.append("Unusually large land holding")
            except:
                pass
        
        # Indicator 3: Generic or suspicious names
        generic_names = ['office', 'department', 'smart agriculture', 'test', 'demo']
        if any(generic in farmer_name.lower() for generic in generic_names):
            fraud_score += 0.4
            risk_indicators.append("Generic or suspicious farmer name")
        
        # Cap the fraud score at 1.0
        fraud_score = min(fraud_score, 1.0)
        
        # Determine risk level
        if fraud_score >= 0.7:
            risk_level = "high"
        elif fraud_score >= 0.4:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        logger.info(f"Fraud detection completed: {fraud_score} ({risk_level})")
        
        return {
            "fraud_score": fraud_score,
            "risk_level": risk_level,
            "indicators": risk_indicators,
            "recommendation": "approve" if risk_level == "low" else "review" if risk_level == "medium" else "investigate",
            "confidence": 0.8  # Detection confidence
        }
        
    except Exception as e:
        logger.error(f"Error in fraud detection: {str(e)}")
        return {
            "fraud_score": 0.5,
            "risk_level": "medium",
            "indicators": ["Detection system error"],
            "error": "Fraud detection failed"
        }
