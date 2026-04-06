#!/usr/bin/env python3
"""
ML Service for Agricultural Document Processing
Integrates Random Forest model predictions into the document processing pipeline
"""

import os
import sys
from typing import Dict, Any, Optional
import logging

from app.ml.train_model import get_model, predict_risk

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MLService:
    """Machine Learning Service for risk assessment and decision support"""
    
    def __init__(self):
        self.model = get_model()
        logger.info("ML Service initialized")
    
    def analyze_document(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze extracted document data and provide ML insights
        
        Part 8: Make ML layer meaningful with real feature-based analysis
        
        Args:
            extracted_data: Dictionary containing extraction results
            
        Returns:
            ML analysis results with risk assessment and decision support
        """
        try:
            logger.info("Starting ML document analysis")
            
            # Extract features for meaningful analysis
            features = self._extract_ml_features(extracted_data)
            
            # Get ML prediction (RF model if available, else rule-based)
            ml_prediction = predict_risk(extracted_data)
            
            # Build priority and risk scores based on actual features
            priority_score, queue = self._calculate_meaningful_priority(features, extracted_data)
            risk_level, risk_factors = self._calculate_meaningful_risk(features, extracted_data)
            
            # Build comprehensive ML insights with detailed reasoning
            reasoning = []
            
            # Add reasoning based on analysis
            if risk_level == 'high':
                reasoning.append("High risk due to critical missing fields or low confidence")
            elif risk_level == 'medium':
                reasoning.append("Medium risk due to some missing fields or moderate confidence")
            else:
                reasoning.append("Low risk - complete extraction with good confidence")
            
            # Add queue reasoning
            if queue == 'VERIFICATION_QUEUE':
                reasoning.append("Requires verification due to missing information")
            elif queue == 'HIGH_PRIORITY':
                reasoning.append("High priority - urgent attention required")
            elif queue == 'FINANCIAL_REVIEW':
                reasoning.append("Financial review required due to high value amount")
            else:
                reasoning.append("Normal processing queue")
            
            # Add priority reasoning
            if priority_score >= 80:
                reasoning.append(f"High priority score ({priority_score}) - expedite processing")
            elif priority_score >= 60:
                reasoning.append(f"Medium priority score ({priority_score}) - standard processing")
            else:
                reasoning.append(f"Normal priority score ({priority_score}) - routine processing")
            
            ml_insights = {
                'risk_level': risk_level,
                'auto_decision': ml_prediction.get('auto_decision', 'review'),
                'confidence_score': ml_prediction.get('confidence_score', 0.5),
                'priority_score': priority_score,
                'queue': queue,
                'processing_time_estimate': self._estimate_processing_time_from_features(features),
                'approval_likelihood': self._calculate_approval_likelihood_from_features(features),
                'reasoning': reasoning,  # Add detailed reasoning
                'feature_analysis': {
                    'document_type': extracted_data.get('document_type', 'unknown'),
                    'missing_fields_count': len(extracted_data.get('missing_fields', [])),
                    'extraction_confidence': extracted_data.get('confidence', 0.0),
                    'risk_flags_count': len(extracted_data.get('risk_flags', [])),
                    'has_amount': features.get('amount_present', False),
                    'has_identity': features.get('aadhaar_present', False),
                    'has_mobile': features.get('mobile_present', False),
                    'completeness_ratio': features.get('completeness_ratio', 0.0)
                },
                'risk_factors': risk_factors,
                'model_info': {
                    'fallback_used': ml_prediction.get('fallback_used', False),
                    'prediction_confidence': ml_prediction.get('confidence_score', 0.5),
                    'prediction_method': 'feature_based_scoring'
                }
            }
            
            logger.info(f"ML analysis completed - Risk: {risk_level}, Priority: {priority_score}, Queue: {queue}")
            
            return ml_insights
            
        except Exception as e:
            logger.error(f"ML analysis error: {e}")
            return self._get_fallback_insights(extracted_data)
    
    def _determine_queue(self, risk_level: str) -> str:
        """Determine processing queue based on risk level"""
        queue_mapping = {
            'low': 'NORMAL',
            'medium': 'VERIFICATION_QUEUE',
            'high': 'HIGH_PRIORITY'
        }
        return queue_mapping.get(risk_level, 'NORMAL')
    
    def _extract_ml_features(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract meaningful features from extracted data for ML analysis
        
        Features used:
        - document_type: Type of document
        - extraction_confidence: Confidence of extraction
        - missing_required_count: Number of missing required fields
        - missing_optional_count: Number of missing optional fields
        - high_severity_risk_count: Count of high severity risk flags
        - medium_severity_risk_count: Count of medium severity risk flags
        - amount_present: Whether amount field exists
        - aadhaar_present: Whether Aadhaar field exists
        - mobile_present:  Whether mobile field exists  
        - scheme_name_present: Whether scheme name exists
        - completeness_ratio: Ratio of extracted fields to expected
        """
        
        structured_data = extracted_data.get('structured_data', {})
        missing_fields = extracted_data.get('missing_fields', [])
        risk_flags = extracted_data.get('risk_flags', [])
        
        # Count severity of risk flags
        high_severity_keywords = ['CRITICAL', 'HIGH', 'SEVERE', 'FRAUD']
        medium_severity_keywords = ['WARNING', 'MEDIUM']
        
        high_severity_count = sum(1 for flag in risk_flags if any(kw in flag.upper() for kw in high_severity_keywords))
        medium_severity_count = sum(1 for flag in risk_flags if any(kw in flag.upper() for kw in medium_severity_keywords))
        
        # Calculate completeness
        extracted_count = len(structured_data)
        total_expected = extracted_count + len(missing_fields)
        completeness_ratio = extracted_count / total_expected if total_expected > 0 else 0
        
        features = {
            'document_type': extracted_data.get('document_type', 'unknown'),
            'extraction_confidence': extracted_data.get('confidence', 0.5),
            'classification_confidence': extracted_data.get('classification_confidence', 0.5),
            'missing_required_count': len(missing_fields),
            'missing_optional_count': 0,  # Could be calculated from schema
            'high_severity_risk_count': high_severity_count,
            'medium_severity_risk_count': medium_severity_count,
            'amount_present': 'requested_amount' in structured_data or 'claim_amount' in structured_data or 'subsidy_amount' in structured_data or 'amount' in structured_data,
            'aadhaar_present': 'aadhaar_number' in structured_data,
            'mobile_present': 'mobile_number' in structured_data or 'phone_number' in structured_data,
            'scheme_name_present': 'scheme_name' in structured_data and structured_data['scheme_name'],
            'farmer_name_present': 'farmer_name' in structured_data and structured_data['farmer_name'],
            'location_present': any(k for k in structured_data.keys() if 'location' in k.lower() or 'village' in k.lower() or 'district' in k.lower()),
            'supporting_doc_reference_present': 'document_reference' in structured_data or 'issuing_authority' in structured_data,
            'completeness_ratio': completeness_ratio,
            'total_flags': len(risk_flags)
        }
        
        return features
    
    def _calculate_meaningful_priority(self, features: Dict[str, Any], extracted_data: Dict[str, Any]) -> tuple:
        """
        Calculate meaningful priority score based on actual features
        
        Different document types get different scores:
        - Grievances with urgency keywords -> HIGH (90)
        - High value financial requests -> FINANCIAL_REVIEW (80)
        - Documents with missing fields -> VERIFICATION_QUEUE (60)
        - Low risk complete documents -> NORMAL (40)
        """
        
        base_score = 40
        queue = "LOW"
        
        doc_type = features['document_type']
        missing_count = features['missing_required_count']
        confidence = features['extraction_confidence']
        high_severity_risks = features['high_severity_risk_count']
        
        # Check for high severity risks
        if high_severity_risks > 0:
            base_score = max(base_score, 75)
        
        # Document-type specific scoring
        if doc_type == 'grievance':
            # Grievances are higher priority
            base_score = max(base_score, 70)
            queue = "HIGH_PRIORITY"
            
            # Check for urgency indicators in description
            desc = extracted_data.get('structured_data', {}).get('grievance_description', '').lower()
            if any(word in desc for word in ['delay', 'urgent', 'immediate', 'pending for long']):
                base_score = 90
        
        elif doc_type in ['scheme_application', 'subsidy_claim', 'insurance_claim']:
            # Check if high value
            structured_data = extracted_data.get('structured_data', {})
            amount = None
            for field in ['requested_amount', 'claim_amount', 'subsidy_amount', 'amount']:
                if field in structured_data:
                    try:
                        amount = float(str(structured_data[field]).replace(',', '').replace('₹', ''))
                        break
                    except:
                        pass
            
            if amount and amount > 100000:
                base_score = 80
                queue = "FINANCIAL_REVIEW"
            elif missing_count > 0:
                base_score = 60
                queue = "VERIFICATION_QUEUE"
            else:
                queue = "NORMAL"
        
        elif doc_type == 'supporting_document':
            # Supporting documents have lower priority
            base_score = 30
            queue = "LOW"
        
        else:
            if missing_count > 2:
                base_score = 65
                queue = "VERIFICATION_QUEUE"
            elif missing_count > 0:
                base_score = 50
                queue = "NORMAL"
            else:
                queue = "NORMAL"
        
        return base_score, queue
    
    def _calculate_meaningful_risk(self, features: Dict[str, Any], extracted_data: Dict[str, Any]) -> tuple:
        """
        Calculate meaningful risk level based on features
        
        Risk determination:
        - HIGH: Missing critical fields, low confidence, high severity risks
        - MEDIUM: Missing some fields, medium confidence, medium risks
        - LOW: Complete, high confidence, no critical risks
        """
        
        missing_count = features['missing_required_count']
        confidence = features['extraction_confidence']
        high_severity_risks = features['high_severity_risk_count']
        medium_severity_risks = features['medium_severity_risk_count']
        completeness = features['completeness_ratio']
        
        risk_factors = []
        
        # Determine risk level
        if high_severity_risks > 0 or confidence < 0.3 or missing_count >= 3:
            risk_level = 'high'
            if high_severity_risks > 0:
                risk_factors.append(f"{high_severity_risks} high-severity risk flags")
            if confidence < 0.3:
                risk_factors.append("Very low extraction confidence")
            if missing_count >= 3:
                risk_factors.append(f"Missing {missing_count} required fields")
        
        elif confidence < 0.5 or missing_count >= 1 or medium_severity_risks >= 2:
            risk_level = 'medium'
            if confidence < 0.5:
                risk_factors.append("Low extraction confidence")
            if missing_count >= 1:
                risk_factors.append(f"Missing {missing_count} required field(s)")
            if medium_severity_risks >= 2:
                risk_factors.append(f"{medium_severity_risks} medium-severity risk flags")
        
        else:
            risk_level = 'low'
            if completeness < 0.8:
                risk_factors.append(f"Incomplete fields ({completeness:.0%})")
            else:
                risk_factors.append("Complete extraction, high confidence")
        
        return risk_level, risk_factors
    
    def _estimate_processing_time_from_features(self, features: Dict[str, Any]) -> str:
        """Estimate processing time based on features"""
        
        base_days = 1
        
        # Add time for missing fields
        base_days += features['missing_required_count']
        
        # Add time for high risk factors
        base_days += features['high_severity_risk_count'] * 2
        base_days += features['medium_severity_risk_count']
        
        # Reduce time for complete, high-confidence documents
        if features['completeness_ratio'] > 0.9 and features['extraction_confidence'] > 0.8:
            base_days = max(1, base_days - 1)
        
        return f"{base_days} days"
    
    def _calculate_approval_likelihood_from_features(self, features: Dict[str, Any]) -> str:
        """Calculate approval likelihood based on features"""
        
        likelihood = 50  # Base 50%
        
        # Bonus for complete, confident data
        if features['completeness_ratio'] > 0.9:
            likelihood += 20
        if features['extraction_confidence'] > 0.8:
            likelihood += 15
        
        # Bonus for required fields present
        if features['aadhaar_present']:
            likelihood += 5
        if features['farmer_name_present']:
            likelihood += 5
        if features['scheme_name_present']:
            likelihood += 10
        
        # Penalty for risks
        likelihood -= features['high_severity_risk_count'] * 20
        likelihood -= features['medium_severity_risk_count'] * 5
        likelihood -= features['missing_required_count'] * 10
        
        # Clamp to 0-100
        likelihood = max(0, min(100, likelihood))
        
        return f"{likelihood}%"
    
    def _calculate_priority_score(self, rf_prediction: Dict[str, Any], extracted_data: Dict[str, Any]) -> int:
        """Deprecated - use _calculate_meaningful_priority instead"""
        risk_level = rf_prediction.get('risk_level', 'medium')
        missing_fields = len(extracted_data.get('missing_fields', []))
        
        if risk_level == 'high' or missing_fields > 2:
            return 80
        elif risk_level == 'medium' or missing_fields > 0:
            return 60
        else:
            return 40
    
    def _estimate_processing_time(self, rf_prediction: Dict[str, Any], extracted_data: Dict[str, Any]) -> str:
        """Deprecated - use _estimate_processing_time_from_features instead"""
        return "2 days"
    
    def _calculate_approval_likelihood(self, rf_prediction: Dict[str, Any], extracted_data: Dict[str, Any]) -> str:
        """Deprecated - use _calculate_approval_likelihood_from_features instead"""
        return "50%"
    
    def _calculate_priority_score(self, rf_prediction: Dict[str, Any], extracted_data: Dict[str, Any]) -> float:
        """Calculate priority score (0-100) for queue sorting"""
        base_score = 50.0
        
        # Adjust based on risk level
        risk_adjustment = {
            'low': -20,
            'medium': 0,
            'high': 30
        }
        base_score += risk_adjustment.get(rf_prediction['risk_level'], 0)
        
        # Adjust based on confidence
        confidence = rf_prediction['confidence_score']
        if confidence > 0.8:
            base_score -= 10  # High confidence reduces priority
        elif confidence < 0.5:
            base_score += 15  # Low confidence increases priority
        
        # Adjust based on missing fields
        missing_count = len(extracted_data.get('missing_fields', []))
        if missing_count == 0:
            base_score -= 5
        elif missing_count > 3:
            base_score += 10
        
        # Ensure score is within bounds
        return max(0, min(100, base_score))
    
    def _estimate_processing_time(self, rf_prediction: Dict[str, Any], extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate processing time in days"""
        base_days = 2
        
        # Adjust based on risk level
        risk_adjustment = {
            'low': 0,
            'medium': 1,
            'high': 3
        }
        total_days = base_days + risk_adjustment.get(rf_prediction['risk_level'], 0)
        
        # Add time for missing fields
        missing_count = len(extracted_data.get('missing_fields', []))
        total_days += min(missing_count, 2)  # Max 2 extra days
        
        # Add time for high amounts
        amount = self._extract_amount(extracted_data)
        if amount > 100000:
            total_days += 2
        elif amount > 50000:
            total_days += 1
        
        return {
            'estimated_days': total_days,
            'base_days': base_days,
            'risk_adjustment': risk_adjustment.get(rf_prediction['risk_level'], 0),
            'missing_fields_adjustment': min(missing_count, 2),
            'amount_adjustment': 2 if amount > 100000 else (1 if amount > 50000 else 0)
        }
    
    def _calculate_approval_likelihood(self, rf_prediction: Dict[str, Any], extracted_data: Dict[str, Any]) -> float:
        """Calculate approval likelihood (0-100%)"""
        base_likelihood = 50.0
        
        # Adjust based on risk level
        risk_adjustment = {
            'low': 30,
            'medium': 0,
            'high': -40
        }
        base_likelihood += risk_adjustment.get(rf_prediction['risk_level'], 0)
        
        # Adjust based on confidence
        confidence = rf_prediction['confidence_score']
        base_likelihood += (confidence - 0.5) * 40  # -20 to +20
        
        # Adjust based on missing fields
        missing_count = len(extracted_data.get('missing_fields', []))
        if missing_count == 0:
            base_likelihood += 20
        elif missing_count > 2:
            base_likelihood -= 30
        
        # Adjust based on completeness
        completeness = self._calculate_completeness(extracted_data)
        base_likelihood += (completeness - 0.5) * 30
        
        # Ensure within bounds
        return max(0, min(100, base_likelihood))
    
    def _extract_amount(self, extracted_data: Dict[str, Any]) -> float:
        """Extract monetary amount from extracted data"""
        # Try canonical request
        canonical = extracted_data.get('canonical', {})
        request = canonical.get('request', {})
        amount_str = request.get('requested_amount', '')
        
        if amount_str:
            try:
                # Extract numeric value
                import re
                match = re.search(r'(\d+(?:\.\d+)?)', amount_str.replace(',', ''))
                if match:
                    return float(match.group(1))
            except:
                pass
        
        # Try structured data
        structured_data = extracted_data.get('structured_data', {})
        amount_str_alt = structured_data.get('requested_amount', '')
        
        if amount_str_alt:
            try:
                import re
                match = re.search(r'(\d+(?:\.\d+)?)', amount_str_alt.replace(',', ''))
                if match:
                    return float(match.group(1))
            except:
                pass
        
        return 0.0
    
    def _calculate_completeness(self, extracted_data: Dict[str, Any]) -> float:
        """Calculate data completeness ratio"""
        critical_fields = [
            'document_type',
            'canonical.applicant.name',
            'canonical.applicant.aadhaar_number',
            'canonical.applicant.mobile_number'
        ]
        
        present = 0
        
        if extracted_data.get('document_type'):
            present += 1
        
        canonical = extracted_data.get('canonical', {})
        applicant = canonical.get('applicant', {})
        
        if applicant.get('name'):
            present += 1
        if applicant.get('aadhaar_number'):
            present += 1
        if applicant.get('mobile_number'):
            present += 1
        
        return present / len(critical_fields)
    
    def _get_fallback_insights(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Provide fallback insights when ML service fails"""
        missing_count = len(extracted_data.get('missing_fields', []))
        confidence = extracted_data.get('confidence', 0.5)
        
        # Simple rule-based risk assessment
        if missing_count == 0 and confidence > 0.8:
            risk_level = 'low'
        elif missing_count > 2 or confidence < 0.5:
            risk_level = 'high'
        else:
            risk_level = 'medium'
        
        return {
            'risk_level': risk_level,
            'auto_decision': 'manual_review' if risk_level != 'low' else 'approve',
            'confidence_score': confidence,
            'queue': self._determine_queue(risk_level),
            'priority_score': 50.0,
            'processing_time_estimate': {'estimated_days': 3},
            'approval_likelihood': 50.0,
            'feature_analysis': {
                'missing_fields_count': missing_count,
                'extraction_confidence': confidence,
                'document_type': extracted_data.get('document_type', 'unknown'),
                'risk_flags_count': len(extracted_data.get('risk_flags', []))
            },
            'model_info': {
                'fallback_used': True,
                'prediction_confidence': 0.0
            },
            'error': 'ML service fallback used'
        }
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get current model status and information"""
        return self.model.get_model_info()

# Global ML service instance
_ml_service_instance = None

def get_ml_service() -> MLService:
    """Get or create global ML service instance"""
    global _ml_service_instance
    if _ml_service_instance is None:
        _ml_service_instance = MLService()
    return _ml_service_instance

def analyze_document_risk(extracted_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze document risk (convenience function)"""
    ml_service = get_ml_service()
    return ml_service.analyze_document(extracted_data)

if __name__ == "__main__":
    # Test the ML service
    print("Testing ML Service...")
    
    test_data = {
        'document_type': 'scheme_application',
        'confidence': 0.85,
        'missing_fields': [],
        'risk_flags': [],
        'canonical': {
            'applicant': {
                'name': 'Test Farmer',
                'aadhaar_number': '123456789012',
                'mobile_number': '9876543210'
            },
            'request': {
                'requested_amount': '50000'
            }
        }
    }
    
    result = analyze_document_risk(test_data)
    print(f"Test result: {result}")
