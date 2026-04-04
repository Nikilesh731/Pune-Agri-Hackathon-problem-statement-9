"""
Reasoning Engine for Enhanced Decision Support
Purpose: Advanced reasoning and decision support for agricultural documents
"""
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum


class ReasoningType(Enum):
    """Types of reasoning insights"""
    EXTRACTION_QUALITY = "extraction_quality"
    COMPLETENESS = "completeness"
    CONSISTENCY = "consistency"
    RISK_ASSESSMENT = "risk_assessment"
    ACTION_RECOMMENDATION = "action_recommendation"
    PREDICTIVE_INSIGHT = "predictive_insight"


@dataclass
class ReasoningInsight:
    """Represents a reasoning insight"""
    reasoning_type: ReasoningType
    message: str
    confidence: float
    evidence: List[str]
    impact: str  # high, medium, low
    actionable: bool


class ReasoningEngine:
    """Advanced reasoning engine for agricultural document processing"""
    
    def __init__(self):
        # Document type-specific reasoning rules
        self.reasoning_rules = {
            'scheme_application': {
                'required_fields': ['farmer_name', 'scheme_name'],
                'optional_fields': ['aadhaar_number', 'location', 'land_size', 'requested_amount'],
                'quality_indicators': {
                    'high_confidence': ['farmer_name', 'scheme_name'],
                    'medium_confidence': ['aadhaar_number', 'location'],
                    'validation_fields': ['aadhaar_number', 'requested_amount']
                },
                'risk_patterns': [
                    r'missing.*farmer.*name',
                    r'missing.*scheme.*name',
                    r'invalid.*aadhaar',
                    r'amount.*exceeds.*limit'
                ]
            },
            'farmer_record': {
                'required_fields': ['farmer_name', 'aadhaar_number', 'mobile_number'],
                'optional_fields': ['location', 'village', 'district'],
                'quality_indicators': {
                    'high_confidence': ['farmer_name', 'aadhaar_number'],
                    'medium_confidence': ['mobile_number'],
                    'validation_fields': ['aadhaar_number', 'mobile_number']
                },
                'risk_patterns': [
                    r'missing.*aadhaar',
                    r'invalid.*mobile',
                    r'duplicate.*record'
                ]
            },
            'grievance': {
                'required_fields': ['farmer_name', 'grievance_type', 'description'],
                'optional_fields': ['location', 'aadhaar_number'],
                'quality_indicators': {
                    'high_confidence': ['farmer_name', 'grievance_type'],
                    'medium_confidence': ['description'],
                    'validation_fields': ['description']
                },
                'risk_patterns': [
                    r'missing.*description',
                    r'vague.*grievance',
                    r'urgent.*attention'
                ]
            },
            'insurance_claim': {
                'required_fields': ['farmer_name', 'claim_type', 'loss_description'],
                'optional_fields': ['claim_amount', 'location', 'aadhaar_number'],
                'quality_indicators': {
                    'high_confidence': ['farmer_name', 'claim_type'],
                    'medium_confidence': ['loss_description'],
                    'validation_fields': ['claim_amount']
                },
                'risk_patterns': [
                    r'missing.*claim.*amount',
                    r'insufficient.*documentation',
                    r'high.*value.*claim'
                ]
            },
            'subsidy_claim': {
                'required_fields': ['farmer_name', 'subsidy_type', 'requested_amount'],
                'optional_fields': ['location', 'aadhaar_number', 'land_size'],
                'quality_indicators': {
                    'high_confidence': ['farmer_name', 'subsidy_type'],
                    'medium_confidence': ['requested_amount'],
                    'validation_fields': ['requested_amount', 'land_size']
                },
                'risk_patterns': [
                    r'amount.*exceeds.*subsidy.*limit',
                    r'missing.*land.*details',
                    r'ineligible.*subsidy'
                ]
            }
        }
        
        # Cross-document consistency rules
        self.consistency_rules = {
            'name_consistency': {
                'fields': ['farmer_name', 'applicant_name', 'complainant', 'claimant'],
                'threshold': 0.8  # Similarity threshold
            },
            'contact_consistency': {
                'fields': ['phone_number', 'mobile_number', 'contact_number'],
                'threshold': 0.9
            },
            'location_consistency': {
                'fields': ['location', 'village', 'district', 'address'],
                'threshold': 0.7
            }
        }
        
        # Action recommendation rules
        self.action_rules = {
            'high_priority': [
                'Missing required fields',
                'Invalid identification',
                'Amount exceeds limits',
                'Urgent attention required'
            ],
            'medium_priority': [
                'Low confidence extraction',
                'Inconsistent information',
                'Missing optional details'
            ],
            'low_priority': [
                'Minor formatting issues',
                'Additional verification suggested'
            ]
        }
    
    def generate_reasoning(self, extraction_result: Dict[str, Any], document_type: str) -> List[ReasoningInsight]:
        """Generate comprehensive reasoning for document processing"""
        insights = []
        
        # 1. Extraction Quality Assessment
        insights.extend(self._assess_extraction_quality(extraction_result, document_type))
        
        # 2. Completeness Analysis
        insights.extend(self._assess_completeness(extraction_result, document_type))
        
        # 3. Consistency Check
        insights.extend(self._assess_consistency(extraction_result, document_type))
        
        # 4. Risk Assessment
        insights.extend(self._assess_risks(extraction_result, document_type))
        
        # 5. Action Recommendations
        insights.extend(self._generate_action_recommendations(extraction_result, document_type))
        
        # 6. Predictive Insights
        insights.extend(self._generate_predictive_insights(extraction_result, document_type))
        
        return insights
    
    def _assess_extraction_quality(self, result: Dict[str, Any], doc_type: str) -> List[ReasoningInsight]:
        """Assess the quality of extracted information"""
        insights = []
        
        rules = self.reasoning_rules.get(doc_type, {})
        extracted_fields = result.get('structured_data', {})
        extracted_metadata = result.get('extracted_fields', {})
        
        # High confidence required fields
        high_conf_fields = rules.get('quality_indicators', {}).get('high_confidence', [])
        high_conf_present = [f for f in high_conf_fields if f in extracted_fields]
        high_conf_missing = [f for f in high_conf_fields if f not in extracted_fields]
        
        if high_conf_present:
            insights.append(ReasoningInsight(
                reasoning_type=ReasoningType.EXTRACTION_QUALITY,
                message=f"High confidence core fields present: {', '.join(high_conf_present)}",
                confidence=0.9,
                evidence=[f"Field {f} extracted with confidence {extracted_metadata.get(f, {}).get('confidence', 0):.2f}" 
                          for f in high_conf_present],
                impact="high",
                actionable=False
            ))
        
        if high_conf_missing:
            insights.append(ReasoningInsight(
                reasoning_type=ReasoningType.EXTRACTION_QUALITY,
                message=f"Missing critical fields: {', '.join(high_conf_missing)}",
                confidence=0.8,
                evidence=[f"Required field {f} not found in extraction" for f in high_conf_missing],
                impact="high",
                actionable=True
            ))
        
        # Overall extraction confidence
        overall_confidence = result.get('confidence', 0.0)
        if overall_confidence > 0.8:
            insights.append(ReasoningInsight(
                reasoning_type=ReasoningType.EXTRACTION_QUALITY,
                message=f"High overall extraction quality ({overall_confidence:.1%})",
                confidence=0.9,
                evidence=[f"Overall confidence score: {overall_confidence:.3f}"],
                impact="medium",
                actionable=False
            ))
        elif overall_confidence < 0.5:
            insights.append(ReasoningInsight(
                reasoning_type=ReasoningType.EXTRACTION_QUALITY,
                message=f"Low extraction quality requires review ({overall_confidence:.1%})",
                confidence=0.8,
                evidence=[f"Overall confidence score: {overall_confidence:.3f}"],
                impact="high",
                actionable=True
            ))
        
        return insights
    
    def _assess_completeness(self, result: Dict[str, Any], doc_type: str) -> List[ReasoningInsight]:
        """Assess document completeness"""
        insights = []
        
        rules = self.reasoning_rules.get(doc_type, {})
        required_fields = rules.get('required_fields', [])
        optional_fields = rules.get('optional_fields', [])
        
        extracted_fields = result.get('structured_data', {})
        missing_fields = result.get('missing_fields', [])
        
        # SPECIAL HANDLING FOR SUPPORTING_DOCUMENT
        # For supporting documents, do not emit "missing required fields: none" messages
        if doc_type == 'supporting_document':
            # Only mention completeness if there are optional fields present
            optional_present = len([f for f in optional_fields if f in extracted_fields])
            if optional_present > 0:
                insights.append(ReasoningInsight(
                    reasoning_type=ReasoningType.COMPLETENESS,
                    message=f"Supporting document contains {optional_present} optional fields",
                    confidence=0.6,
                    evidence=[f"Optional fields: {', '.join([f for f in optional_fields if f in extracted_fields])}"],
                    impact="low",
                    actionable=False
                ))
            else:
                # For supporting documents with no required fields, just confirm it's a valid supporting document
                insights.append(ReasoningInsight(
                    reasoning_type=ReasoningType.COMPLETENESS,
                    message="Supporting document requires linkage validation",
                    confidence=0.7,
                    evidence=["Document type: supporting_document"],
                    impact="medium",
                    actionable=True
                ))
            return insights
        
        # STANDARD COMPLETENESS ASSESSMENT FOR OTHER DOCUMENT TYPES
        # Required fields completeness
        required_present = len([f for f in required_fields if f in extracted_fields])
        required_completeness = required_present / len(required_fields) if required_fields else 1.0
        
        # Only generate missing field messages if there are actually missing fields
        if len(missing_fields) == 0:
            insights.append(ReasoningInsight(
                reasoning_type=ReasoningType.COMPLETENESS,
                message="All required fields present - document is complete",
                confidence=0.95,
                evidence=[f"Required fields found: {', '.join(required_fields)}"],
                impact="high",
                actionable=False
            ))
        elif required_completeness >= 0.7:
            insights.append(ReasoningInsight(
                reasoning_type=ReasoningType.COMPLETENESS,
                message=f"Most required fields present ({required_completeness:.1%})",
                confidence=0.7,
                evidence=[f"Required fields present: {required_present}/{len(required_fields)}"],
                impact="medium",
                actionable=True
            ))
        else:
            insights.append(ReasoningInsight(
                reasoning_type=ReasoningType.COMPLETENESS,
                message=f"Critical missing fields - document incomplete ({required_completeness:.1%})",
                confidence=0.9,
                evidence=[f"Missing required fields: {', '.join(missing_fields)}"],
                impact="high",
                actionable=True
            ))
        
        # Optional fields coverage
        optional_present = len([f for f in optional_fields if f in extracted_fields])
        if optional_present > 0:
            insights.append(ReasoningInsight(
                reasoning_type=ReasoningType.COMPLETENESS,
                message=f"Additional details available: {optional_present} optional fields",
                confidence=0.6,
                evidence=[f"Optional fields: {', '.join([f for f in optional_fields if f in extracted_fields])}"],
                impact="low",
                actionable=False
            ))
        
        return insights
    
    def _assess_consistency(self, result: Dict[str, Any], doc_type: str) -> List[ReasoningInsight]:
        """Assess internal consistency of extracted information"""
        insights = []
        
        extracted_fields = result.get('structured_data', {})
        extracted_metadata = result.get('extracted_fields', {})
        
        # Check name consistency across different name fields
        name_fields = ['farmer_name', 'applicant_name', 'complainant', 'claimant']
        present_name_fields = {k: v for k, v in extracted_fields.items() if k in name_fields and v}
        
        if len(present_name_fields) > 1:
            # Simple consistency check - same names should match
            names = list(present_name_fields.values())
            if len(set(names)) == 1:
                insights.append(ReasoningInsight(
                    reasoning_type=ReasoningType.CONSISTENCY,
                    message="Name fields are consistent across document",
                    confidence=0.8,
                    evidence=[f"{k}: {v}" for k, v in present_name_fields.items()],
                    impact="medium",
                    actionable=False
                ))
            else:
                insights.append(ReasoningInsight(
                    reasoning_type=ReasoningType.CONSISTENCY,
                    message="Inconsistent names detected - requires verification",
                    confidence=0.7,
                    evidence=[f"{k}: {v}" for k, v in present_name_fields.items()],
                    impact="high",
                    actionable=True
                ))
        
        # Check contact consistency
        contact_fields = ['phone_number', 'mobile_number', 'contact_number']
        present_contact_fields = {k: v for k, v in extracted_fields.items() if k in contact_fields and v}
        
        if len(present_contact_fields) > 1:
            contacts = list(present_contact_fields.values())
            # Normalize contacts (remove spaces, dashes)
            normalized_contacts = [re.sub(r'[\s-]', '', str(c)) for c in contacts]
            if len(set(normalized_contacts)) == 1:
                insights.append(ReasoningInsight(
                    reasoning_type=ReasoningType.CONSISTENCY,
                    message="Contact information is consistent",
                    confidence=0.8,
                    evidence=[f"{k}: {v}" for k, v in present_contact_fields.items()],
                    impact="low",
                    actionable=False
                ))
        
        # Check location consistency
        location_fields = ['location', 'village', 'district', 'address']
        present_location_fields = {k: v for k, v in extracted_fields.items() if k in location_fields and v}
        
        if 'location' in extracted_fields and 'village' in extracted_fields:
            location = extracted_fields['location'].lower()
            village = extracted_fields['village'].lower()
            if village in location:
                insights.append(ReasoningInsight(
                    reasoning_type=ReasoningType.CONSISTENCY,
                    message="Location fields are properly related",
                    confidence=0.7,
                    evidence=[f"Location: {location}", f"Village: {village}"],
                    impact="low",
                    actionable=False
                ))
        
        return insights
    
    def _assess_risks(self, result: Dict[str, Any], doc_type: str) -> List[ReasoningInsight]:
        """Assess potential risks and issues"""
        insights = []
        
        rules = self.reasoning_rules.get(doc_type, {})
        risk_patterns = rules.get('risk_patterns', [])
        
        extracted_fields = result.get('structured_data', {})
        reasoning = result.get('reasoning', [])
        missing_fields = result.get('missing_fields', [])
        
        # Only generate missing-field risk if there are actually missing fields
        if len(missing_fields) > 0:
            # Check for critical missing fields
            critical_missing = [f for f in missing_fields if f in ['farmer_name', 'scheme_name', 'subsidy_type', 'claim_type', 'grievance_type']]
            if critical_missing:
                insights.append(ReasoningInsight(
                    reasoning_type=ReasoningType.RISK_ASSESSMENT,
                    message=f"Critical missing fields: {', '.join(critical_missing)}",
                    confidence=0.9,
                    evidence=[f"Missing required: {', '.join(critical_missing)}"],
                    impact="high",
                    actionable=True
                ))
        
        # Document-specific risk assessments
        if doc_type == 'subsidy_claim' and 'requested_amount' in extracted_fields:
            try:
                amount = float(re.sub(r'[^\d.]', '', str(extracted_fields['requested_amount'])))
                if amount > 500000:  # High threshold for subsidy claims
                    insights.append(ReasoningInsight(
                        reasoning_type=ReasoningType.RISK_ASSESSMENT,
                        message=f"High value subsidy claim requires additional verification (₹{amount:,.0f})",
                        confidence=0.9,
                        evidence=[f"Amount: ₹{amount:,.0f} exceeds standard limit"],
                        impact="high",
                        actionable=True
                    ))
            except (ValueError, TypeError):
                pass
        
        if doc_type == 'insurance_claim' and 'claim_amount' in extracted_fields:
            try:
                amount = float(re.sub(r'[^\d.]', '', str(extracted_fields['claim_amount'])))
                if amount > 1000000:  # High threshold for insurance claims
                    insights.append(ReasoningInsight(
                        reasoning_type=ReasoningType.RISK_ASSESSMENT,
                        message=f"High value insurance claim requires detailed review (₹{amount:,.0f})",
                        confidence=0.9,
                        evidence=[f"Claim amount: ₹{amount:,.0f} exceeds standard limit"],
                        impact="high",
                        actionable=True
                    ))
            except (ValueError, TypeError):
                pass
        
        # Check for invalid identification numbers
        if 'aadhaar_number' in extracted_fields:
            aadhaar = str(extracted_fields['aadhaar_number'])
            # Basic Aadhaar validation
            clean_aadhaar = re.sub(r'[\s-]', '', aadhaar)
            if not (len(clean_aadhaar) == 12 and clean_aadhaar.isdigit()):
                insights.append(ReasoningInsight(
                    reasoning_type=ReasoningType.RISK_ASSESSMENT,
                    message="Invalid Aadhaar number format detected",
                    confidence=0.9,
                    evidence=[f"Aadhaar: {aadhaar}"],
                    impact="high",
                    actionable=True
                ))
        
        return insights
    
    def _generate_action_recommendations(self, result: Dict[str, Any], doc_type: str) -> List[ReasoningInsight]:
        """Generate actionable recommendations"""
        insights = []
        
        missing_fields = result.get('missing_fields', [])
        overall_confidence = result.get('confidence', 0.0)
        
        # High priority actions
        if missing_fields:
            insights.append(ReasoningInsight(
                reasoning_type=ReasoningType.ACTION_RECOMMENDATION,
                message=f"Request missing required fields: {', '.join(missing_fields)}",
                confidence=0.9,
                evidence=[f"Missing: {', '.join(missing_fields)}"],
                impact="high",
                actionable=True
            ))
        
        if overall_confidence < 0.5:
            insights.append(ReasoningInsight(
                reasoning_type=ReasoningType.ACTION_RECOMMENDATION,
                message="Manual review recommended due to low extraction confidence",
                confidence=0.8,
                evidence=[f"Confidence: {overall_confidence:.1%}"],
                impact="medium",
                actionable=True
            ))
        
        # Medium priority actions
        if doc_type == 'scheme_application' and 'land_size' not in result.get('structured_data', {}):
            insights.append(ReasoningInsight(
                reasoning_type=ReasoningType.ACTION_RECOMMENDATION,
                message="Consider collecting land details for better scheme eligibility assessment",
                confidence=0.6,
                evidence=["Land size not found in document"],
                impact="medium",
                actionable=True
            ))
        
        # Low priority actions
        if overall_confidence > 0.8 and not missing_fields:
            insights.append(ReasoningInsight(
                reasoning_type=ReasoningType.ACTION_RECOMMENDATION,
                message="Document ready for automated processing",
                confidence=0.9,
                evidence=[f"High confidence: {overall_confidence:.1%}", "All required fields present"],
                impact="low",
                actionable=False
            ))
        
        return insights
    
    def _generate_predictive_insights(self, result: Dict[str, Any], doc_type: str) -> List[ReasoningInsight]:
        """Generate predictive insights and recommendations"""
        insights = []
        
        extracted_fields = result.get('structured_data', {})
        
        # Predict processing time based on completeness
        missing_fields = result.get('missing_fields', [])
        if not missing_fields:
            insights.append(ReasoningInsight(
                reasoning_type=ReasoningType.PREDICTIVE_INSIGHT,
                message="Predicted processing time: 1-2 business days",
                confidence=0.7,
                evidence=["Complete document with all required fields"],
                impact="low",
                actionable=False
            ))
        elif len(missing_fields) <= 2:
            insights.append(ReasoningInsight(
                reasoning_type=ReasoningType.PREDICTIVE_INSIGHT,
                message="Predicted processing time: 3-5 business days (pending clarification)",
                confidence=0.6,
                evidence=[f"Missing {len(missing_fields)} fields"],
                impact="medium",
                actionable=False
            ))
        else:
            insights.append(ReasoningInsight(
                reasoning_type=ReasoningType.PREDICTIVE_INSIGHT,
                message="Predicted processing time: 7+ business days (requires significant clarification)",
                confidence=0.7,
                evidence=[f"Missing {len(missing_fields)} fields"],
                impact="high",
                actionable=False
            ))
        
        # Predict approval likelihood based on quality indicators
        overall_confidence = result.get('confidence', 0.0)
        if overall_confidence > 0.8 and not missing_fields:
            insights.append(ReasoningInsight(
                reasoning_type=ReasoningType.PREDICTIVE_INSIGHT,
                message="High approval likelihood based on document quality",
                confidence=0.6,
                evidence=[f"Quality score: {overall_confidence:.1%}"],
                impact="medium",
                actionable=False
            ))
        
        # Document-specific predictions
        if doc_type == 'subsidy_claim' and 'land_size' in extracted_fields:
            try:
                land_size = float(extracted_fields['land_size'])
                if land_size > 5:  # Large land holding
                    insights.append(ReasoningInsight(
                        reasoning_type=ReasoningType.PREDICTIVE_INSIGHT,
                        message=f"Large land holding ({land_size} hectares) may qualify for additional benefits",
                        confidence=0.5,
                        evidence=[f"Land size: {land_size} hectares"],
                        impact="medium",
                        actionable=False
                    ))
            except (ValueError, TypeError):
                pass
        
        return insights
    
    def format_reasoning_for_output(self, insights: List[ReasoningInsight]) -> List[str]:
        """Format reasoning insights for output"""
        formatted_reasoning = []
        
        # Group by type for better organization
        grouped_insights = {}
        for insight in insights:
            reasoning_type = insight.reasoning_type.value
            if reasoning_type not in grouped_insights:
                grouped_insights[reasoning_type] = []
            grouped_insights[reasoning_type].append(insight)
        
        # Format each group
        type_order = [
            ReasoningType.EXTRACTION_QUALITY.value,
            ReasoningType.COMPLETENESS.value,
            ReasoningType.CONSISTENCY.value,
            ReasoningType.RISK_ASSESSMENT.value,
            ReasoningType.ACTION_RECOMMENDATION.value,
            ReasoningType.PREDICTIVE_INSIGHT.value
        ]
        
        for reasoning_type in type_order:
            if reasoning_type in grouped_insights:
                insights_of_type = grouped_insights[reasoning_type]
                for insight in insights_of_type:
                    if insight.confidence > 0.5:  # Only include confident insights
                        prefix = ""
                        if insight.impact == "high":
                            prefix = "🚨 "
                        elif insight.impact == "medium":
                            prefix = "⚠️ "
                        else:
                            prefix = "ℹ️ "
                        
                        formatted_reasoning.append(f"{prefix}{insight.message}")
        
        return formatted_reasoning
