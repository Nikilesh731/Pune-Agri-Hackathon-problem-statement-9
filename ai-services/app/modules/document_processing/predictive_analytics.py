"""
Predictive Analytics for Agricultural Documents
Purpose: Advanced predictive insights and trend analysis
"""
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum


class PredictionType(Enum):
    """Types of predictive insights"""
    PROCESSING_TIME = "processing_time"
    APPROVAL_LIKELIHOOD = "approval_likelihood"
    RISK_SCORE = "risk_score"
    BENEFIT_ELIGIBILITY = "benefit_eligibility"
    TREND_ANALYSIS = "trend_analysis"
    ANOMALY_DETECTION = "anomaly_detection"


@dataclass
class Prediction:
    """Represents a predictive insight"""
    prediction_type: PredictionType
    value: Any
    confidence: float
    reasoning: List[str]
    time_horizon: str  # immediate, short_term, medium_term, long_term
    factors: List[str]


class PredictiveAnalytics:
    """Predictive analytics engine for agricultural document processing"""
    
    def __init__(self):
        # Historical patterns and benchmarks
        self.processing_time_benchmarks = {
            'complete_document': 1.2,  # days
            'missing_fields': 3.5,
            'high_value_claim': 5.0,
            'complex_case': 7.0,
            'verification_required': 4.2
        }
        
        self.approval_likelihood_factors = {
            'high_confidence': 0.85,
            'complete_fields': 0.90,
            'standard_amount': 0.80,
            'valid_identification': 0.85,
            'consistent_data': 0.75,
            'low_risk_profile': 0.80
        }
        
        self.risk_factors = {
            'high_amount': 0.3,
            'missing_fields': 0.4,
            'low_confidence': 0.5,
            'invalid_id': 0.6,
            'inconsistent_data': 0.3,
            'urgent_indicators': 0.2
        }
        
        # Scheme-specific eligibility criteria
        self.scheme_eligibility = {
            'pm_kisan': {
                'max_land': 2.0,  # hectares
                'min_income': 0,
                'required_docs': ['aadhaar', 'land_record'],
                'benefit_amount': 6000
            },
            'soil_health': {
                'max_land': 10.0,
                'min_income': 0,
                'required_docs': ['aadhaar', 'land_record'],
                'benefit_amount': 0  # Variable
            },
            'crop_insurance': {
                'max_land': 50.0,
                'min_income': 0,
                'required_docs': ['aadhaar', 'land_record', 'crop_details'],
                'benefit_amount': 0  # Based on crop loss
            }
        }
        
        # Anomaly detection thresholds
        self.anomaly_thresholds = {
            'amount_outliers': {
                'scheme_application': 50000,
                'subsidy_claim': 500000,
                'insurance_claim': 1000000
            },
            'land_size_outliers': {
                'small': 0.1,
                'large': 50.0
            },
            'processing_time_outliers': 14.0  # days
        }
    
    def generate_predictions(self, extraction_result: Dict[str, Any], document_type: str) -> List[Prediction]:
        """Generate comprehensive predictive insights"""
        predictions = []
        
        # 1. Processing Time Prediction
        predictions.append(self._predict_processing_time(extraction_result, document_type))
        
        # 2. Approval Likelihood
        predictions.append(self._predict_approval_likelihood(extraction_result, document_type))
        
        # 3. Risk Score
        predictions.append(self._calculate_risk_score(extraction_result, document_type))
        
        # 4. Benefit Eligibility
        if document_type in ['scheme_application', 'subsidy_claim']:
            predictions.append(self._assess_benefit_eligibility(extraction_result, document_type))
        
        # 5. Anomaly Detection
        predictions.append(self._detect_anomalies(extraction_result, document_type))
        
        # 6. Trend Analysis (if historical data available)
        predictions.append(self._analyze_trends(extraction_result, document_type))
        
        return [p for p in predictions if p is not None]
    
    def _predict_processing_time(self, result: Dict[str, Any], doc_type: str) -> Prediction:
        """Predict document processing time"""
        base_time = self.processing_time_benchmarks['complete_document']
        adjustments = []
        
        # Check for missing fields
        missing_fields = result.get('missing_fields', [])
        if missing_fields:
            adjustment_factor = len(missing_fields) * 0.5
            base_time += adjustment_factor
            adjustments.append(f"Missing {len(missing_fields)} fields adds {adjustment_factor:.1f} days")
        
        # Check for high-value claims
        extracted_fields = result.get('structured_data', {})
        if 'requested_amount' in extracted_fields:
            try:
                amount = float(re.sub(r'[^\d.]', '', str(extracted_fields['requested_amount'])))
                if amount > 100000:
                    base_time += 2.0
                    adjustments.append(f"High value claim (₹{amount:,.0f}) adds 2.0 days")
            except (ValueError, TypeError):
                pass
        
        # Check extraction confidence
        confidence = result.get('confidence', 0.0)
        if confidence < 0.5:
            base_time += 1.5
            adjustments.append(f"Low confidence ({confidence:.1%}) adds 1.5 days")
        
        # Document type adjustments
        if doc_type == 'insurance_claim':
            base_time *= 1.3  # Insurance claims take longer
            adjustments.append("Insurance claim complexity adds 30% time")
        elif doc_type == 'grievance':
            base_time *= 1.2  # Grievances require investigation
            adjustments.append("Grievance investigation adds 20% time")
        
        # Determine time horizon
        if base_time <= 2:
            time_horizon = "immediate"
        elif base_time <= 5:
            time_horizon = "short_term"
        elif base_time <= 10:
            time_horizon = "medium_term"
        else:
            time_horizon = "long_term"
        
        return Prediction(
            prediction_type=PredictionType.PROCESSING_TIME,
            value=f"{base_time:.1f} days",
            confidence=0.7,
            reasoning=[f"Base time: {self.processing_time_benchmarks['complete_document']:.1f} days"] + adjustments,
            time_horizon=time_horizon,
            factors=["missing_fields", "amount", "confidence", "document_type"]
        )
    
    def _predict_approval_likelihood(self, result: Dict[str, Any], doc_type: str) -> Prediction:
        """Predict approval likelihood"""
        likelihood = 0.5  # Base 50%
        factors = []
        reasoning = []
        
        extracted_fields = result.get('structured_data', {})
        confidence = result.get('confidence', 0.0)
        missing_fields = result.get('missing_fields', [])
        
        # High confidence boost
        if confidence > 0.8:
            likelihood += 0.25
            factors.append("high_confidence")
            reasoning.append(f"High extraction confidence ({confidence:.1%}) increases likelihood")
        
        # Complete fields boost
        if not missing_fields:
            likelihood += 0.20
            factors.append("complete_fields")
            reasoning.append("All required fields present increases likelihood")
        elif len(missing_fields) <= 2:
            likelihood += 0.10
            factors.append("mostly_complete")
            reasoning.append(f"Only {len(missing_fields)} missing fields has minor impact")
        
        # Valid identification boost
        if 'aadhaar_number' in extracted_fields:
            aadhaar = str(extracted_fields['aadhaar_number'])
            clean_aadhaar = re.sub(r'[\s-]', '', aadhaar)
            if len(clean_aadhaar) == 12 and clean_aadhaar.isdigit():
                likelihood += 0.15
                factors.append("valid_identification")
                reasoning.append("Valid Aadhaar number increases likelihood")
        
        # Standard amount boost
        if 'requested_amount' in extracted_fields:
            try:
                amount = float(re.sub(r'[^\d.]', '', str(extracted_fields['requested_amount'])))
                if doc_type == 'scheme_application' and amount <= 50000:
                    likelihood += 0.10
                    factors.append("standard_amount")
                    reasoning.append("Standard scheme amount within expected range")
                elif doc_type == 'subsidy_claim' and amount <= 500000:
                    likelihood += 0.10
                    factors.append("standard_amount")
                    reasoning.append("Subsidy amount within expected range")
                elif amount > 1000000:
                    likelihood -= 0.20
                    factors.append("high_amount_risk")
                    reasoning.append("High amount requires additional scrutiny")
            except (ValueError, TypeError):
                pass
        
        # Document type adjustments
        if doc_type == 'supporting_document':
            likelihood += 0.10  # Supporting documents usually approved
            reasoning.append("Supporting documents typically approved")
        elif doc_type == 'grievance':
            likelihood -= 0.10  # Grievances require investigation
            reasoning.append("Grievances require investigation")
        
        # Clamp to valid range
        likelihood = max(0.1, min(0.95, likelihood))
        
        # Determine confidence in prediction
        prediction_confidence = 0.6
        if len(factors) >= 3:
            prediction_confidence = 0.8
        elif len(factors) >= 2:
            prediction_confidence = 0.7
        
        return Prediction(
            prediction_type=PredictionType.APPROVAL_LIKELIHOOD,
            value=f"{likelihood:.1%}",
            confidence=prediction_confidence,
            reasoning=reasoning,
            time_horizon="short_term",
            factors=factors
        )
    
    def _calculate_risk_score(self, result: Dict[str, Any], doc_type: str) -> Prediction:
        """Calculate comprehensive risk score"""
        risk_score = 0.0  # Lower is better
        risk_factors = []
        reasoning = []
        
        extracted_fields = result.get('structured_data', {})
        confidence = result.get('confidence', 0.0)
        missing_fields = result.get('missing_fields', [])
        
        # Missing fields risk
        if missing_fields:
            field_risk = len(missing_fields) * 0.1
            risk_score += field_risk
            risk_factors.append("missing_fields")
            reasoning.append(f"Missing {len(missing_fields)} fields adds {field_risk:.1f} risk")
        
        # Low confidence risk
        if confidence < 0.5:
            risk_score += 0.3
            risk_factors.append("low_confidence")
            reasoning.append(f"Low confidence ({confidence:.1%}) adds 0.3 risk")
        elif confidence < 0.7:
            risk_score += 0.1
            risk_factors.append("medium_confidence")
            reasoning.append(f"Medium confidence ({confidence:.1%}) adds 0.1 risk")
        
        # High amount risk
        if 'requested_amount' in extracted_fields:
            try:
                amount = float(re.sub(r'[^\d.]', '', str(extracted_fields['requested_amount'])))
                if doc_type == 'subsidy_claim' and amount > 500000:
                    risk_score += 0.3
                    risk_factors.append("high_amount")
                    reasoning.append(f"High subsidy amount (₹{amount:,.0f}) adds 0.3 risk")
                elif doc_type == 'insurance_claim' and amount > 1000000:
                    risk_score += 0.4
                    risk_factors.append("high_amount")
                    reasoning.append(f"High insurance claim (₹{amount:,.0f}) adds 0.4 risk")
            except (ValueError, TypeError):
                pass
        
        # Invalid identification risk
        if 'aadhaar_number' in extracted_fields:
            aadhaar = str(extracted_fields['aadhaar_number'])
            clean_aadhaar = re.sub(r'[\s-]', '', aadhaar)
            if not (len(clean_aadhaar) == 12 and clean_aadhaar.isdigit()):
                risk_score += 0.4
                risk_factors.append("invalid_id")
                reasoning.append("Invalid Aadhaar format adds 0.4 risk")
        
        # Urgent indicators risk
        reasoning_text = ' '.join(result.get('reasoning', [])).lower()
        if any(urgent in reasoning_text for urgent in ['urgent', 'emergency', 'immediate']):
            risk_score += 0.2
            risk_factors.append("urgent_indicators")
            reasoning.append("Urgent indicators add 0.2 risk")
        
        # Normalize risk score to 0-1 scale
        risk_score = min(risk_score, 1.0)
        
        # Determine risk level
        if risk_score < 0.3:
            risk_level = "Low"
        elif risk_score < 0.6:
            risk_level = "Medium"
        else:
            risk_level = "High"
        
        return Prediction(
            prediction_type=PredictionType.RISK_SCORE,
            value=f"{risk_score:.2f} ({risk_level})",
            confidence=0.8,
            reasoning=reasoning,
            time_horizon="immediate",
            factors=risk_factors
        )
    
    def _assess_benefit_eligibility(self, result: Dict[str, Any], doc_type: str) -> Prediction:
        """Assess benefit eligibility for schemes and subsidies"""
        extracted_fields = result.get('structured_data', {})
        eligibility_score = 0.0
        reasoning = []
        factors = []
        
        # Determine scheme type
        scheme_name = extracted_fields.get('scheme_name', '').lower()
        if 'pm kisan' in scheme_name or 'kisan samman' in scheme_name:
            scheme_type = 'pm_kisan'
        elif 'soil health' in scheme_name or 'soil card' in scheme_name:
            scheme_type = 'soil_health'
        elif 'insurance' in scheme_name or 'crop insurance' in scheme_name:
            scheme_type = 'crop_insurance'
        else:
            scheme_type = 'general'
        
        # Check land size eligibility
        if 'land_size' in extracted_fields:
            try:
                land_size = float(extracted_fields['land_size'])
                if scheme_type in self.scheme_eligibility:
                    max_land = self.scheme_eligibility[scheme_type]['max_land']
                    if land_size <= max_land:
                        eligibility_score += 0.4
                        factors.append("land_eligible")
                        reasoning.append(f"Land size ({land_size} ha) within limit ({max_land} ha)")
                    else:
                        factors.append("land_exceeds_limit")
                        reasoning.append(f"Land size ({land_size} ha) exceeds limit ({max_land} ha)")
            except (ValueError, TypeError):
                pass
        
        # Check required documents
        required_docs = self.scheme_eligibility.get(scheme_type, {}).get('required_docs', [])
        available_docs = []
        
        if 'aadhaar_number' in extracted_fields:
            available_docs.append('aadhaar')
        if 'land_size' in extracted_fields:
            available_docs.append('land_record')
        
        doc_coverage = len([d for d in required_docs if d in available_docs]) / len(required_docs) if required_docs else 1.0
        eligibility_score += doc_coverage * 0.3
        reasoning.append(f"Document coverage: {doc_coverage:.1%}")
        
        # Check identification validity
        if 'aadhaar_number' in extracted_fields:
            aadhaar = str(extracted_fields['aadhaar_number'])
            clean_aadhaar = re.sub(r'[\s-]', '', aadhaar)
            if len(clean_aadhaar) == 12 and clean_aadhaar.isdigit():
                eligibility_score += 0.3
                factors.append("valid_aadhaar")
                reasoning.append("Valid Aadhaar number present")
        
        # Determine eligibility
        if eligibility_score > 0.7:
            eligibility_status = "Likely Eligible"
        elif eligibility_score > 0.4:
            eligibility_status = "Possibly Eligible"
        else:
            eligibility_status = "Likely Ineligible"
        
        return Prediction(
            prediction_type=PredictionType.BENEFIT_ELIGIBILITY,
            value=f"{eligibility_score:.2f} ({eligibility_status})",
            confidence=0.7,
            reasoning=reasoning,
            time_horizon="medium_term",
            factors=factors
        )
    
    def _detect_anomalies(self, result: Dict[str, Any], doc_type: str) -> Prediction:
        """Detect anomalies and outliers"""
        anomalies = []
        reasoning = []
        factors = []
        
        extracted_fields = result.get('structured_data', {})
        
        # Amount anomalies
        if 'requested_amount' in extracted_fields:
            try:
                amount = float(re.sub(r'[^\d.]', '', str(extracted_fields['requested_amount'])))
                threshold = self.anomaly_thresholds['amount_outliers'].get(doc_type, 100000)
                if amount > threshold:
                    anomalies.append(f"Amount ₹{amount:,.0f} exceeds typical threshold ₹{threshold:,.0f}")
                    factors.append("amount_outlier")
            except (ValueError, TypeError):
                pass
        
        # Land size anomalies
        if 'land_size' in extracted_fields:
            try:
                land_size = float(extracted_fields['land_size'])
                if land_size < self.anomaly_thresholds['land_size_outliers']['small']:
                    anomalies.append(f"Land size {land_size} ha is unusually small")
                    factors.append("small_land")
                elif land_size > self.anomaly_thresholds['land_size_outliers']['large']:
                    anomalies.append(f"Land size {land_size} ha is unusually large")
                    factors.append("large_land")
            except (ValueError, TypeError):
                pass
        
        # Confidence anomalies
        confidence = result.get('confidence', 0.0)
        if confidence < 0.3:
            anomalies.append(f"Very low extraction confidence ({confidence:.1%})")
            factors.append("low_confidence")
        
        # Field count anomalies
        field_count = len(extracted_fields)
        if field_count < 3:
            anomalies.append(f"Very few fields extracted ({field_count})")
            factors.append("sparse_extraction")
        elif field_count > 25:
            anomalies.append(f"Unusually many fields extracted ({field_count})")
            factors.append("dense_extraction")
        
        anomaly_value = "No anomalies detected" if not anomalies else f"{len(anomalies)} anomalies"
        
        return Prediction(
            prediction_type=PredictionType.ANOMALY_DETECTION,
            value=anomaly_value,
            confidence=0.8,
            reasoning=anomalies,
            time_horizon="immediate",
            factors=factors
        )
    
    def _analyze_trends(self, result: Dict[str, Any], doc_type: str) -> Prediction:
        """Analyze trends (placeholder for future historical data integration)"""
        # This would integrate with historical data when available
        # For now, provide basic trend indicators
        
        reasoning = [
            "Trend analysis requires historical data integration",
            "Current analysis based on document patterns only"
        ]
        
        return Prediction(
            prediction_type=PredictionType.TREND_ANALYSIS,
            value="Limited trend data",
            confidence=0.3,
            reasoning=reasoning,
            time_horizon="long_term",
            factors=["historical_data_needed"]
        )
    
    def format_predictions_for_output(self, predictions: List[Prediction]) -> Dict[str, Any]:
        """Format predictions for API output"""
        formatted = {
            'predictions': {},
            'summary': {
                'total_predictions': len(predictions),
                'high_confidence': len([p for p in predictions if p.confidence > 0.7]),
                'medium_confidence': len([p for p in predictions if 0.5 < p.confidence <= 0.7]),
                'low_confidence': len([p for p in predictions if p.confidence <= 0.5])
            }
        }
        
        for prediction in predictions:
            pred_type = prediction.prediction_type.value
            formatted['predictions'][pred_type] = {
                'value': prediction.value,
                'confidence': prediction.confidence,
                'reasoning': prediction.reasoning,
                'time_horizon': prediction.time_horizon,
                'factors': prediction.factors
            }
        
        return formatted
