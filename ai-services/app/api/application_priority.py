"""
Application Priority Scoring API
Provides priority scoring for agricultural applications
"""
from fastapi import APIRouter
from typing import Dict, Any
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/score")
def score_application(application_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Score application priority based on extracted data
    
    Args:
        application_data: Application data including extracted fields
        
    Returns:
        Priority score and level
    """
    try:
        # Simple priority scoring logic for demo
        priority_score = 0.7  # Default medium priority
        
        # Check for critical fields
        critical_fields = ['farmer_name', 'aadhaar_number', 'scheme_name']
        missing_critical = [field for field in critical_fields if not application_data.get(field)]
        
        if missing_critical:
            priority_score = 0.3  # Low priority if missing critical fields
        else:
            priority_score = 0.85  # High priority if all critical fields present
            
        # Determine priority level
        if priority_score >= 0.8:
            priority_level = "high"
        elif priority_score >= 0.5:
            priority_level = "medium"
        else:
            priority_level = "low"
        
        logger.info(f"Application scored: {priority_score} ({priority_level})")
        
        return {
            "priority_score": priority_score,
            "priority_level": priority_level,
            "missing_critical_fields": missing_critical,
            "scoring_factors": {
                "completeness": 0.8 if not missing_critical else 0.3,
                "urgency": 0.7,  # Default urgency for demo
                "eligibility": 0.9  # Default eligibility for demo
            }
        }
        
    except Exception as e:
        logger.error(f"Error scoring application: {str(e)}")
        return {
            "priority_score": 0.1,
            "priority_level": "low",
            "error": "Scoring failed"
        }
