"""
Document Classification Service
Purpose: Clean rule-based agricultural document classifier with standardized output
"""
import re
from typing import Dict, List, Any, Optional, Tuple


class DocumentClassificationService:
    """Service for classifying agricultural office documents"""
    
    def __init__(self):
        
        # Classification keywords and patterns for each document type
        self.classification_rules = {
            'scheme_application': {
                'keywords': [
                    'scheme', 'application', 'benefit', 'applicant', 'pradhan mantri',
                    'pm kisan', 'kisan credit', 'crop insurance', 'soil health',
                    'paramparagat', 'national mission', 'rkvy', 'agricultural scheme',
                    'government scheme', 'beneficiary', 'apply', 'form', 'scheme name',
                    'applicant name', 'requested amount', 'subsidy amount', 'kisan samman nidhi'
                ],
                'patterns': [
                    r'(?:scheme\s+application|application\s+form)',
                    r'(?:pradhan\s+mantri|pm\s*kisan)',
                    r'(?:kisan\s+credit|crop\s+insurance)',
                    r'(?:beneficiary|applicant\s+details)',
                    r'(?:scheme\s+name|applicant\s+name)',
                    r'(?:requested\s+amount|subsidy\s+amount)'
                ]
            },
            'farmer_record': {
                'keywords': [
                    'farmer id', 'land holding', 'guardian', 'village', 'district',
                    'profile', 'record', 'registration', 'demographics', 'family details',
                    'farmer name', 'address', 'contact', 'aadhaar', 'khasra',
                    'land size', 'total land', 'cultivated area', 'farmer details'
                ],
                'patterns': [
                    r'(?:farmer\s+id|farmer\s+profile)',
                    r'(?:land\s+holding|land\s+record)',
                    r'(?:family\s+details|guardian\s+name)',
                    r'(?:registration\s+form|farmer\s+details)',
                    r'(?:land\s+size|total\s+land)',
                    r'(?:cultivated\s+area|village\s+name)'
                ]
            },
            'grievance': {
                'keywords': [
                    'grievance', 'complaint', 'issue', 'problem', 'delay', 'pending',
                    'not received', 'request for action', 'resolve', 'suffering',
                    'no response', 'repeated request', 'follow up', 'reminder',
                    'urgent attention', 'immediate action', 'rejected', 'not processed',
                    'complainant', 'subject', 'department', 'reference number'
                ],
                'patterns': [
                    r'(?:grievance\s+letter|complaint\s+letter)',
                    r'(?:request\s+for\s+action|issue\s+resolution)',
                    r'(?:grievance\s+redressal|problem\s+statement)',
                    r'(?:kindly\s+resolve|please\s+resolve)',
                    r'(?:suffering\s+due\s+to|facing\s+issue)',
                    r'(?:pending\s+for\s+long|delayed\s+payment)',
                    r'(?:complaint\s+subject|grievance\s+subject)',
                    r'(?:reference\s+number|grievance\s+no)'
                ]
            },
            'insurance_claim': {
                'keywords': [
                    'insurance', 'claim', 'policy', 'insured', 'premium', 'loss',
                    'crop insurance', 'claim settlement', 'damage', 'compensation',
                    'policy number', 'claim amount', 'insured amount', 'crop damage',
                    'claimant', 'incident', 'loss reason', 'crop name', 'estimated loss'
                ],
                'patterns': [
                    r'(?:insurance\s+claim|claim\s+settlement)',
                    r'(?:crop\s+insurance|policy\s+number)',
                    r'(?:premium\s+paid|insured\s+amount)',
                    r'(?:claim\s+form|damage\s+assessment)',
                    r'(?:claim\s+amount|policy\s+holder)',
                    r'(?:loss\s+reason|incident\s+date)'
                ]
            },
            'subsidy_claim': {
                'keywords': [
                    'subsidy', 'claim', 'amount', 'financial assistance', 'grant',
                    'subsidy claim', 'financial support', 'aid', 'relief',
                    'subsidy amount', 'claim amount', 'government assistance',
                    'subsidy type', 'benefit amount', 'requested amount', 'grant claim',
                    # Strong subsidy-specific indicators
                    'drip irrigation', 'micro irrigation', 'per drop more crop',
                    'subsidy release', 'reimbursement', 'installation',
                    'agricultural subsidy', 'irrigation subsidy', 'equipment subsidy',
                    'subsidy application', 'subsidy request', 'subsidy scheme'
                ],
                'patterns': [
                    r'(?:subsidy\s+claim|claim\s+form)',
                    r'(?:financial\s+assistance|grant\s+application)',
                    r'(?:subsidy\s+amount|claim\s+amount)',
                    r'(?:government\s+aid|financial\s+support)',
                    r'(?:subsidy\s+type|benefit\s+amount)',
                    r'(?:requested\s+amount|grant\s+claim)',
                    # Strong subsidy-specific patterns
                    r'(?:drip\s+irrigation|micro\s+irrigation)',
                    r'(?:per\s+drop\s+more\s+crop)',
                    r'(?:subsidy\s+release|reimbursement)',
                    r'(?:installation\s+subsidy|equipment\s+subsidy)',
                    r'(?:agricultural\s+subsidy|irrigation\s+subsidy)'
                ]
            },
            'supporting_document': {
                'keywords': [
                    'attachment', 'certificate', 'proof', 'passbook', 'id', 'supporting',
                    'document', 'verification', 'evidence', 'enclosure', 'annexure',
                    'appendix', 'schedule', 'exhibit', 'document reference',
                    'certificate number', 'issuing authority', 'document type'
                ],
                'patterns': [
                    r'(?:supporting\s+document|attachment)',
                    r'(?:certificate\s+of|proof\s+of)',
                    r'(?:bank\s+passbook|id\s+proof)',
                    r'(?:enclosure|annexure|appendix)',
                    r'(?:document\s+reference|certificate\s+number)',
                    r'(?:issuing\s+authority|document\s+type)'
                ]
            }
        }
        
        # Confidence thresholds
        self.min_confidence_threshold = 0.3
        self.grievance_override_threshold = 0.6
        
    def classify_document(self, text: str, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Classify document based on text content and optional filename
        
        Args:
            text: OCR extracted text
            filename: Optional filename for additional context
            
        Returns:
            Classification result with exact structure:
            {
              "document_type": str,
              "classification_confidence": float,
              "classification_reasoning": {
                "keywords_found": List[str],
                "structural_indicators": List[str],
                "confidence_factors": List[str]
              }
            }
        """
        if not text or len(text.strip()) < 10:
            return {
                "document_type": "unknown",
                "classification_confidence": 0.0,
                "classification_reasoning": {
                    "keywords_found": [],
                    "structural_indicators": ["No text content"],
                    "confidence_factors": ["Insufficient text for classification"]
                }
            }
        
        text_lower = text.lower()
        
        # Priority 1: Check for grievance intent override
        grievance_score, grievance_reasoning = self._detect_grievance_intent(text_lower)
        if grievance_score >= self.grievance_override_threshold:
            # Add filename indicators if available
            if filename:
                filename_indicators = self._analyze_filename(filename)
                grievance_reasoning["structural_indicators"].extend(filename_indicators)
                grievance_reasoning["confidence_factors"].append("Filename analysis included")
            
            grievance_reasoning["confidence_factors"].append("Grievance intent override applied")
            
            return {
                "document_type": "grievance",
                "classification_confidence": min(grievance_score, 1.0),
                "classification_reasoning": grievance_reasoning
            }
        
        # Priority 1.5: Check for scheme_application priority override (HIGHEST priority for structure)
        scheme_score, scheme_reasoning = self._detect_scheme_application_priority(text_lower, filename)
        if scheme_score >= 0.6:  # Lower threshold for strong structural indicators
            # Add filename indicators if available
            if filename:
                filename_indicators = self._analyze_filename(filename)
                scheme_reasoning["structural_indicators"].extend(filename_indicators)
                scheme_reasoning["confidence_factors"].append("Filename analysis included")
            
            scheme_reasoning["confidence_factors"].append("Scheme application priority override applied")
            
            return {
                "document_type": "scheme_application",
                "classification_confidence": min(scheme_score, 1.0),
                "classification_reasoning": scheme_reasoning
            }
        
        # Priority 1.6: Check for insurance priority override (higher priority than subsidy)
        insurance_score, insurance_reasoning = self._detect_insurance_priority(text_lower)
        subsidy_score, subsidy_reasoning = self._detect_subsidy_priority(text_lower)
        
        # NEW: Tie-break logic when both insurance and subsidy have strong signals
        if insurance_score >= 0.7 and subsidy_score >= 0.7:
            # Use exclusive indicators to break ties
            insurance_exclusive = ['policy', 'premium', 'insured', 'damage', 'compensation', 'crop damage', 'pmfby', 'fasal bima', 'policy number', 'claim settlement']
            subsidy_exclusive = [
                'subsidy', 'grant', 'financial assistance', 'government aid', 'government assistance', 
                'subsidy application', 'subsidy request', 'drip irrigation', 'micro irrigation', 
                'per drop more crop', 'subsidy release', 'reimbursement', 'installation',
                'agricultural subsidy', 'irrigation subsidy', 'equipment subsidy'
            ]
            
            insurance_exclusive_count = sum(1 for term in insurance_exclusive if term in text_lower)
            subsidy_exclusive_count = sum(1 for term in subsidy_exclusive if term in text_lower)
            
            # Only apply override if there are strong exclusive indicators
            if insurance_exclusive_count >= 2 and subsidy_exclusive_count <= 1:
                # Clear insurance win
                if filename:
                    filename_indicators = self._analyze_filename(filename)
                    insurance_reasoning["structural_indicators"].extend(filename_indicators)
                    insurance_reasoning["confidence_factors"].append("Filename analysis included")
                
                insurance_reasoning["confidence_factors"].append("Insurance priority override applied (tie-break)")
                insurance_reasoning["confidence_factors"].append(f"Insurance exclusive indicators: {insurance_exclusive_count}, Subsidy exclusive indicators: {subsidy_exclusive_count}")
                
                return {
                    "document_type": "insurance_claim",
                    "classification_confidence": min(insurance_score, 1.0),
                    "classification_reasoning": insurance_reasoning
                }
            elif subsidy_exclusive_count >= 2 and insurance_exclusive_count <= 1:
                # Clear subsidy win
                if filename:
                    filename_indicators = self._analyze_filename(filename)
                    subsidy_reasoning["structural_indicators"].extend(filename_indicators)
                    subsidy_reasoning["confidence_factors"].append("Filename analysis included")
                
                subsidy_reasoning["confidence_factors"].append("Subsidy priority override applied (tie-break)")
                subsidy_reasoning["confidence_factors"].append(f"Subsidy exclusive indicators: {subsidy_exclusive_count}, Insurance exclusive indicators: {insurance_exclusive_count}")
                
                return {
                    "document_type": "subsidy_claim",
                    "classification_confidence": min(subsidy_score, 1.0),
                    "classification_reasoning": subsidy_reasoning
                }
            else:
                # Mixed signals without clear winner - continue to normal classification
                insurance_reasoning["confidence_factors"].append("Mixed insurance/subsidy signals - deferring to normal classification")
                subsidy_reasoning["confidence_factors"].append("Mixed insurance/subsidy signals - deferring to normal classification")
        elif insurance_score >= 0.7:
            # Clear insurance win without tie
            if filename:
                filename_indicators = self._analyze_filename(filename)
                insurance_reasoning["structural_indicators"].extend(filename_indicators)
                insurance_reasoning["confidence_factors"].append("Filename analysis included")
            
            insurance_reasoning["confidence_factors"].append("Insurance priority override applied")
            
            return {
                "document_type": "insurance_claim",
                "classification_confidence": min(insurance_score, 1.0),
                "classification_reasoning": insurance_reasoning
            }
        
        # Priority 2: Check for subsidy priority override (only if insurance didn't win)
        if subsidy_score >= 0.7:  # High confidence subsidy signals
            # Add filename indicators if available
            if filename:
                filename_indicators = self._analyze_filename(filename)
                subsidy_reasoning["structural_indicators"].extend(filename_indicators)
                subsidy_reasoning["confidence_factors"].append("Filename analysis included")
            
            subsidy_reasoning["confidence_factors"].append("Subsidy priority override applied")
            
            return {
                "document_type": "subsidy_claim",
                "classification_confidence": min(subsidy_score, 1.0),
                "classification_reasoning": subsidy_reasoning
            }
        
        # Priority 2: Normal classification scoring
        type_scores = {}
        type_reasoning = {}
        
        for doc_type, rules in self.classification_rules.items():
            score, reasoning = self._calculate_type_score(text_lower, doc_type, rules)
            
            # Add filename score boost if available
            if filename:
                filename_boost = self._calculate_filename_boost(filename, doc_type)
                if filename_boost > 0:
                    score = min(score + filename_boost, 1.0)
                    reasoning["confidence_factors"].append(f"Filename boost: +{filename_boost:.1f}")
            
            type_scores[doc_type] = score
            type_reasoning[doc_type] = reasoning
        
        # Find the best match
        best_type = max(type_scores, key=type_scores.get)
        best_score = type_scores[best_type]
        
        # Apply confidence thresholds
        if best_score < self.min_confidence_threshold:
            final_type = "unknown"
            final_score = 0.0
            reasoning = {
                "keywords_found": [],
                "structural_indicators": ["Low confidence match"],
                "confidence_factors": [f'Best score {best_score:.2f} below threshold {self.min_confidence_threshold}']
            }
        else:
            final_type = best_type
            final_score = best_score
            reasoning = type_reasoning[best_type]
        
        # Add filename-based reasoning if available
        if filename:
            filename_indicators = self._analyze_filename(filename)
            reasoning["structural_indicators"].extend(filename_indicators)
            reasoning["confidence_factors"].append("Filename analysis included")
        
        return {
            "document_type": final_type,
            "classification_confidence": final_score,
            "classification_reasoning": reasoning
        }
    
    def _detect_scheme_application_priority(self, text_lower: str, filename: Optional[str] = None) -> Tuple[float, Dict[str, List[str]]]:
        """Detect scheme application priority with strong structural indicators override"""
        # Strong scheme application indicators that should override subsidy_claim
        scheme_signals = [
            # Very strong structural indicators
            'scheme application form', 'application form', 'scheme name', 'request type',
            'new scheme enrollment', 'scheme enrollment', 'beneficiary details', 'applicant details',
            # Form structure indicators
            'applicant name', 'father name', 'guardian name', 'aadhaar number', 'mobile number',
            'village name', 'district', 'state', 'pin code', 'address',
            # Agriculture-specific scheme fields
            'land size', 'land area', 'cultivated area', 'soil type', 'crop pattern',
            'irrigation facility', 'farm equipment', 'agricultural land',
            # Scheme-specific terminology
            'pradhan mantri', 'pm kisan', 'kisan samman nidhi', 'kisan credit card',
            'paramparagat krishi', 'national mission', 'rkvy', 'mgnrega',
            # Government scheme indicators
            'government scheme', 'central scheme', 'state scheme', 'benefit scheme',
            'financial assistance scheme', 'agricultural scheme', 'development scheme'
        ]
        
        # Strong scheme application patterns
        scheme_patterns = [
            r'(?:scheme\s+application|application\s+form)',
            r'(?:scheme\s+name|request\s+type)',
            r'(?:new\s+scheme\s+enrollment|scheme\s+enrollment)',
            r'(?:beneficiary\s+details|applicant\s+details)',
            r'(?:applicant\s+name|father\s+name|guardian\s+name)',
            r'(?:aadhaar\s+number|mobile\s+number)',
            r'(?:village\s+name|district\s+name|state\s+name)',
            r'(?:land\s+size|land\s+area|cultivated\s+area)',
            r'(?:pradhan\s+mantri|pm\s+kisan)',
            r'(?:kisan\s+samman|kisan\s+credit)',
            r'(?:government\s+scheme|central\s+scheme)',
            r'(?:financial\s+assistance\s+scheme|agricultural\s+scheme)'
        ]
        
        # Initialize variables
        keyword_matches = []
        keyword_score = 0.0
        
        # Keyword matching with higher weight for structural indicators
        for signal in scheme_signals:
            if self._is_keyword_match_safe(signal, text_lower):
                keyword_matches.append(signal)
                # Count occurrences
                occurrences = self._count_keyword_occurrences(signal, text_lower)
                # Very high weight for structural indicators
                if signal in ['scheme application form', 'application form', 'scheme name', 'request type']:
                    keyword_score += occurrences * 0.5  # Very high weight
                elif signal in ['applicant name', 'beneficiary details', 'land size', 'government scheme']:
                    keyword_score += occurrences * 0.3  # High weight
                else:
                    keyword_score += occurrences * 0.2  # Normal weight
        
        # Pattern matching
        pattern_matches = []
        pattern_score = 0.0
        
        for pattern in scheme_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                pattern_matches.extend(matches)
                pattern_score += len(matches) * 0.4
        
        # Calculate total scheme score
        scheme_score = keyword_score + pattern_score
        
        # Build reasoning
        confidence_factors = []
        if keyword_matches:
            confidence_factors.append(f"Found scheme application keywords: {', '.join(keyword_matches[:3])}")
        if pattern_matches:
            confidence_factors.append(f"Found scheme application patterns: {len(pattern_matches)} matches")
        
        # Strong boost for filename indicators
        if filename and 'scheme_application' in filename.lower():
            scheme_score += 0.3
            confidence_factors.append("Filename indicates scheme application")
        
        # Boost for multiple structural indicators
        structural_signals = ['scheme application form', 'application form', 'scheme name', 'request type', 'applicant name', 'beneficiary details']
        structural_count = sum(1 for signal in structural_signals if signal in text_lower)
        
        if structural_count >= 2:
            scheme_score += 0.25
            confidence_factors.append("Multiple structural scheme application indicators detected")
        
        # Penalty for explicit subsidy indicators (to reduce misclassification)
        explicit_subsidy_indicators = ['subsidy claim', 'subsidy application', 'subsidy request', 'reimbursement', 'drip irrigation', 'micro irrigation']
        subsidy_count = sum(1 for indicator in explicit_subsidy_indicators if indicator in text_lower)
        
        if subsidy_count > 0 and structural_count >= 2:
            # If we have strong structural indicators, ignore some subsidy signals
            scheme_score += 0.1
            confidence_factors.append("Strong scheme structure overrides subsidy signals")
        elif subsidy_count > 0 and structural_count < 2:
            # If weak structural signals but strong subsidy signals, penalize
            scheme_score -= subsidy_count * 0.1
            confidence_factors.append(f"Penalty for {subsidy_count} explicit subsidy indicators (weak scheme structure)")
        
        # Build reasoning structure
        reasoning = {
            "keywords_found": keyword_matches[:5],  # Limit to top 5
            "structural_indicators": ["Scheme application structure detected"],
            "confidence_factors": confidence_factors
        }
        
        return min(scheme_score, 1.0), reasoning
    
    def _detect_subsidy_priority(self, text_lower: str) -> Tuple[float, Dict[str, List[str]]]:
        """Detect subsidy priority with strong signals override"""
        # Strong subsidy-positive signals that should override insurance_claim
        subsidy_signals = [
            'subsidy', 'claim', 'amount', 'financial assistance', 'grant',
            'subsidy claim', 'financial support', 'aid', 'relief',
            'subsidy amount', 'claim amount', 'government assistance',
            'subsidy type', 'benefit amount', 'requested amount', 'grant claim',
            'subsidy application', 'subsidy request', 'subsidy scheme',
            # Very strong subsidy-specific indicators
            'drip irrigation', 'micro irrigation', 'per drop more crop',
            'subsidy release', 'reimbursement', 'installation',
            'agricultural subsidy', 'irrigation subsidy', 'equipment subsidy'
        ]
        
        # Strong subsidy patterns
        subsidy_patterns = [
            r'(?:subsidy\s+claim|claim\s+form)',
            r'(?:financial\s+assistance|grant\s+application)',
            r'(?:subsidy\s+amount|claim\s+amount)',
            r'(?:government\s+aid|financial\s+support)',
            r'(?:subsidy\s+type|benefit\s+amount)',
            r'(?:requested\s+amount|grant\s+claim)',
            r'(?:subsidy\s+application|subsidy\s+request)',
            # Very strong subsidy-specific patterns
            r'(?:drip\s+irrigation|micro\s+irrigation)',
            r'(?:per\s+drop\s+more\s+crop)',
            r'(?:subsidy\s+release|reimbursement)',
            r'(?:installation\s+subsidy|equipment\s+subsidy)',
            r'(?:agricultural\s+subsidy|irrigation\s+subsidy)'
        ]
        
        # Initialize variables
        keyword_matches = []
        keyword_score = 0.0
        
        # Keyword matching with higher weight for strong signals
        for keyword in subsidy_signals:
            if self._is_keyword_match_safe(keyword, text_lower):
                keyword_matches.append(keyword)
                # Count occurrences
                occurrences = self._count_keyword_occurrences(keyword, text_lower)
                # Very high weight for strong subsidy-specific indicators
                if keyword in ['drip irrigation', 'micro irrigation', 'per drop more crop', 'subsidy release', 'reimbursement', 'installation']:
                    keyword_score += occurrences * 0.4  # Very high weight
                elif keyword in ['subsidy', 'claim', 'grant', 'financial assistance']:
                    keyword_score += occurrences * 0.2  # High weight
                else:
                    keyword_score += occurrences * 0.15  # Normal weight
        
        # Pattern matching
        pattern_matches = []
        pattern_score = 0.0
        
        for pattern in subsidy_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                pattern_matches.extend(matches)
                pattern_score += len(matches) * 0.3
        
        # Calculate total subsidy score
        subsidy_score = keyword_score + pattern_score
        
        # Build reasoning
        confidence_factors = []
        if keyword_matches:
            confidence_factors.append(f"Found subsidy keywords: {', '.join(keyword_matches[:3])}")
        if pattern_matches:
            confidence_factors.append(f"Found subsidy patterns: {len(pattern_matches)} matches")
        
        # Boost for very strong indicators
        strong_signals = ['subsidy', 'claim', 'grant', 'financial assistance', 'government assistance']
        strong_signal_count = sum(1 for signal in strong_signals if signal in text_lower)
        
        if strong_signal_count >= 2:
            subsidy_score += 0.2  # Strong boost for multiple strong signals
            confidence_factors.append("Multiple strong subsidy signals detected")
        
        # Penalty for insurance indicators (to reduce misclassification)
        insurance_indicators = ['insurance', 'policy', 'premium', 'insured', 'pmfby', 'fasal bima', 'pradhan mantri fasal bima']
        insurance_count = sum(1 for indicator in insurance_indicators if indicator in text_lower)
        
        # Strong boost for explicit subsidy indicators
        strong_subsidy_indicators = ['subsidy claim', 'subsidy application', 'subsidy request', 'financial assistance', 'government assistance']
        strong_subsidy_count = sum(1 for indicator in strong_subsidy_indicators if indicator in text_lower)
        
        if insurance_count > 0 and strong_subsidy_count == 0:
            # Only penalize if there are insurance indicators but no strong subsidy indicators
            subsidy_score -= insurance_count * 0.15  # Stronger penalty for insurance indicators
            confidence_factors.append(f"Penalty for {insurance_count} insurance indicators (no strong subsidy signals)")
        elif insurance_count > 0 and strong_subsidy_count > 0:
            # Mixed signals - let the stronger signals win
            confidence_factors.append("Mixed insurance/subsidy signals - using strongest indicators")
        
        # Build reasoning structure
        reasoning = {
            "keywords_found": keyword_matches[:5],  # Limit to top 5
            "structural_indicators": ["Subsidy document pattern detected"],
            "confidence_factors": confidence_factors
        }
        
        return min(subsidy_score, 1.0), reasoning

    def _detect_insurance_priority(self, text_lower: str) -> Tuple[float, Dict[str, List[str]]]:
        """Detect insurance priority with strong signals override"""
        # Strong insurance-positive signals that should override scheme_application
        insurance_signals = [
            'insurance', 'claim', 'policy', 'insured', 'premium', 'loss',
            'crop insurance', 'claim settlement', 'damage', 'compensation',
            'policy number', 'claim amount', 'insured amount', 'crop damage',
            'claimant', 'incident', 'loss reason', 'estimated loss',
            'pmfby', 'fasal bima', 'pradhan mantri fasal bima yojana'
        ]
        
        # Strong insurance patterns
        insurance_patterns = [
            r'(?:insurance\s+claim|claim\s+settlement)',
            r'(?:crop\s+insurance|policy\s+number)',
            r'(?:premium\s+paid|insured\s+amount)',
            r'(?:claim\s+form|damage\s+assessment)',
            r'(?:claim\s+amount|policy\s+holder)',
            r'(?:loss\s+reason|incident\s+date)',
            r'(?:pmfby|fasal\s+bima)',
            r'(?:pradhan\s+mantri\s+fasal\s+bima)'
        ]
        
        # Initialize variables
        keyword_matches = []
        keyword_score = 0.0
        
        # Keyword matching with higher weight for strong signals
        for keyword in insurance_signals:
            if self._is_keyword_match_safe(keyword, text_lower):
                keyword_matches.append(keyword)
                # Count occurrences
                occurrences = self._count_keyword_occurrences(keyword, text_lower)
                # Higher weight for strong signals
                if keyword in ['insurance', 'claim', 'policy', 'pmfby', 'fasal bima']:
                    keyword_score += occurrences * 0.2
                else:
                    keyword_score += occurrences * 0.15
        
        # Pattern matching
        pattern_matches = []
        pattern_score = 0.0
        
        for pattern in insurance_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                pattern_matches.extend(matches)
                pattern_score += len(matches) * 0.3
        
        # Calculate total insurance score
        insurance_score = keyword_score + pattern_score
        
        # Build reasoning
        confidence_factors = []
        if keyword_matches:
            confidence_factors.append(f"Found insurance keywords: {', '.join(keyword_matches[:3])}")
        if pattern_matches:
            confidence_factors.append(f"Found insurance patterns: {len(pattern_matches)} matches")
        
        # Boost for very strong indicators
        strong_signals = ['insurance', 'claim', 'policy', 'pmfby', 'fasal bima']
        strong_signal_count = sum(1 for signal in strong_signals if signal in text_lower)
        
        if strong_signal_count >= 2:
            insurance_score += 0.3
            confidence_factors.append("Multiple strong insurance signals detected")
        elif strong_signal_count >= 1:
            insurance_score += 0.15
            confidence_factors.append("Strong insurance signals detected")
        
        return min(insurance_score, 1.0), {
            "keywords_found": keyword_matches,
            "structural_indicators": pattern_matches,
            "confidence_factors": confidence_factors
        }
    
    def _detect_grievance_intent(self, text_lower: str) -> Tuple[float, Dict[str, List[str]]]:
        """Detect grievance intent with priority override"""
        grievance_keywords = [
            'grievance', 'complaint', 'issue', 'problem', 'delay', 'pending for long',
            'not received', 'request for action', 'request to resolve', 'kindly resolve',
            'please take action', 'suffering due to', 'no response', 'repeated request',
            'pending', 'delayed', 'not processed', 'not approved', 'rejected', 'waiting',
            'follow up', 'reminder', 'urgent attention', 'immediate action'
        ]
        
        # HIGH-VALUE grievance patterns that should strongly indicate grievance
        grievance_patterns = [
            r'(?:grievance\s+letter|complaint\s+letter)',
            r'(?:request\s+for\s+action|issue\s+resolution)',
            r'(?:grievance\s+redressal|problem\s+statement)',
            r'(?:kindly\s+resolve|please\s+resolve)',
            r'(?:suffering\s+due\s+to|facing\s+issue)',
            r'(?:pending\s+for\s+long|delayed\s+payment)',
            r'(?:not\s+received|no\s+response)',
            r'(?:urgent\s+attention|immediate\s+action)',
            # ENHANCED: Payment-related grievance patterns
            r'(?:payment\s+delay|payment\s+not\s+credited|payment\s+pending)',
            r'(?:subsidy\s+not\s+received|subsidy\s+delay|benefit\s+not\s+received)',
            r'(?:has\s+not\s+been\s+credited|not\s+credited|yet\s+to\s+be\s+credited)',
            r'(?:supposed\s+to\s+be\s+released|still\s+pending|please\s+look\s+into)',
            r'(?:help\s+me\s+get|need\s+my|waiting\s+for)'
        ]
        
        # Initialize variables
        keyword_matches = []
        keyword_score = 0.0
        
        # Keyword matching with safer handling for short/ambiguous grievance words
        for keyword in grievance_keywords:
            if self._is_keyword_match_safe(keyword, text_lower):
                keyword_matches.append(keyword)
                # Count occurrences consistently with safer matching
                occurrences = self._count_keyword_occurrences(keyword, text_lower)
                keyword_score += occurrences * 0.15
        
        # Pattern matching
        pattern_matches = []
        pattern_score = 0.0
        
        for pattern in grievance_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                pattern_matches.extend(matches)
                # ENHANCED: Higher weight for payment-related grievance patterns
                pattern_weight = 0.4 if any(word in pattern for word in ['payment', 'subsidy', 'credited', 'delay']) else 0.25
                pattern_score += len(matches) * pattern_weight
        
        # Calculate total grievance score
        grievance_score = keyword_score + pattern_score
        
        # Build reasoning
        confidence_factors = []
        if keyword_matches:
            confidence_factors.append(f"Found grievance keywords: {', '.join(keyword_matches[:3])}")
        if pattern_matches:
            confidence_factors.append(f"Found grievance patterns: {len(pattern_matches)} matches")
        
        # Boost for strong indicators - require more evidence for override
        strong_indicators = ['grievance', 'complaint', 'delay', 'pending', 'not received']
        action_phrases = ['request for action', 'please take action', 'urgent attention', 'immediate action']
        
        strong_indicator_count = sum(1 for indicator in strong_indicators if indicator in text_lower)
        action_phrase_count = sum(1 for phrase in action_phrases if phrase in text_lower)
        
        # Require both strong indicators AND action phrases for override boost
        if strong_indicator_count >= 2 and action_phrase_count >= 1:
            grievance_score += 0.2
            confidence_factors.append("Strong grievance indicators with action phrases detected")
        elif strong_indicator_count >= 3:
            grievance_score += 0.15
            confidence_factors.append("Multiple strong grievance indicators detected")
        elif any(indicator in text_lower for indicator in strong_indicators):
            confidence_factors.append("Strong grievance indicators detected")
        
        return min(grievance_score, 1.0), {
            "keywords_found": keyword_matches,
            "structural_indicators": pattern_matches,
            "confidence_factors": confidence_factors
        }
    
    def _calculate_type_score(self, text_lower: str, doc_type: str, rules: Dict[str, List[str]]) -> Tuple[float, Dict[str, List[str]]]:
        """Calculate classification score for a specific document type"""
        # Keyword matching
        keyword_matches = []
        keyword_score = 0.0
        
        # Keyword matching with safer handling for short/ambiguous words
        for keyword in rules['keywords']:
            if self._is_keyword_match_safe(keyword, text_lower):
                keyword_matches.append(keyword)
                # Count occurrences consistently with safer matching
                occurrences = self._count_keyword_occurrences(keyword, text_lower)
                keyword_score += occurrences * 0.1
        
        # Pattern matching with human-friendly reasoning
        pattern_matches = []
        pattern_score = 0.0
        
        for pattern in rules['patterns']:
            matches = re.findall(pattern, text_lower)
            if matches:
                # Store human-friendly pattern description instead of raw regex
                pattern_desc = self._get_pattern_description(pattern)
                pattern_matches.append(pattern_desc)
                pattern_score += len(matches) * 0.2
        
        # Calculate base score
        base_score = keyword_score + pattern_score
        
        # Initialize confidence_factors early to fix runtime bug
        confidence_factors = []
        
        # Apply type-specific weight and claim separation logic
        type_weights = {
            'scheme_application': 1.0,
            'farmer_record': 0.9,
            'grievance': 0.8,
            'insurance_claim': 0.9,
            'subsidy_claim': 0.9,
            'supporting_document': 0.7
        }
        
        weight = type_weights.get(doc_type, 0.8)
        base_score = base_score * weight
        
        # Improve insurance vs subsidy claim separation
        if doc_type == 'insurance_claim':
            insurance_specific = ['policy', 'premium', 'insured', 'damage', 'compensation', 'crop damage']
            if any(term in text_lower for term in insurance_specific):
                base_score += 0.15
                confidence_factors.append("Insurance-specific terms detected")
        elif doc_type == 'subsidy_claim':
            subsidy_specific = ['subsidy', 'grant', 'financial assistance', 'government aid', 'government assistance']
            if any(term in text_lower for term in subsidy_specific):
                base_score += 0.15
                confidence_factors.append("Subsidy-specific terms detected")
        
        final_score = min(base_score, 1.0)
        
        # Build reasoning
        if keyword_matches:
            confidence_factors.append(f"Found {len(keyword_matches)} keywords: {', '.join(keyword_matches[:3])}")
        if pattern_matches:
            confidence_factors.append(f"Found {len(pattern_matches)} pattern matches")
        confidence_factors.append(f"Type weight applied: {weight}")
        
        return final_score, {
            "keywords_found": keyword_matches,
            "structural_indicators": pattern_matches,
            "confidence_factors": confidence_factors
        }
    
    def _analyze_filename(self, filename: str) -> List[str]:
        """Analyze filename for classification indicators"""
        if not filename:
            return []
        
        filename_lower = filename.lower()
        indicators = []
        
        filename_patterns = {
            'scheme_application': ['application', 'scheme', 'pm-kisan', 'kisan', 'benefit', 'form'],
            'farmer_record': ['record', 'profile', 'registration', 'farmer', 'id', 'details'],
            'grievance': ['grievance', 'complaint', 'petition', 'issue', 'problem'],
            'insurance_claim': ['insurance', 'claim', 'policy', 'damage', 'loss'],
            'subsidy_claim': ['subsidy', 'claim', 'grant', 'financial', 'assistance'],
            'supporting_document': ['attachment', 'supporting', 'certificate', 'proof', 'document']
        }
        
        for doc_type, patterns in filename_patterns.items():
            # Use safer matching for short/ambiguous filename tokens
            if any(self._is_filename_token_safe(pattern, filename_lower) for pattern in patterns):
                indicators.append(f"Filename suggests {doc_type}")
        
        return indicators
    
    def _is_keyword_match_safe(self, keyword: str, text_lower: str) -> bool:
        """Safer keyword matching that avoids noisy substring matches for short words"""
        # Short/ambiguous words that need word boundary matching
        ambiguous_words = {'form', 'app', 'id', 'claim', 'record', 'scheme', 'policy', 'proof'}
        
        if keyword in ambiguous_words:
            # Use word boundary regex for short words
            pattern = rf'\b{re.escape(keyword)}\b'
            return bool(re.search(pattern, text_lower))
        else:
            # For longer phrases, simple substring match is fine
            return keyword in text_lower
    
    def _calculate_filename_boost(self, filename: str, doc_type: str) -> float:
        """Calculate modest filename-based score boost"""
        if not filename:
            return 0.0
        
        filename_lower = filename.lower()
        
        # Strong filename patterns that deserve a boost
        strong_patterns = {
            'scheme_application': ['scheme', 'application', 'pm-kisan', 'kisan', 'benefit', 'form'],
            'farmer_record': ['farmer', 'record', 'profile', 'registration', 'id', 'details'],
            'grievance': ['grievance', 'complaint', 'petition', 'issue', 'problem'],
            'insurance_claim': ['insurance', 'claim', 'policy', 'damage', 'loss'],
            'subsidy_claim': ['subsidy', 'claim', 'grant', 'financial', 'assistance'],
            'supporting_document': ['attachment', 'supporting', 'certificate', 'proof', 'document']
        }
        
        patterns = strong_patterns.get(doc_type, [])
        matches = sum(1 for pattern in patterns if pattern in filename_lower)
        
        # Modest boost: 0.1 for 1 match, 0.15 for 2+ matches
        if matches >= 2:
            return 0.15
        elif matches == 1:
            return 0.1
        
        return 0.0
    
    def _get_pattern_description(self, pattern: str) -> str:
        """Convert regex pattern to human-friendly description"""
        pattern_descriptions = {
            r'(?:scheme\s+application|application\s+form)': 'Scheme application form structure',
            r'(?:pradhan\s+mantri|pm\s*kisan)': 'PM Kisan scheme references',
            r'(?:kisan\s+credit|crop\s+insurance)': 'Agricultural credit/insurance terms',
            r'(?:beneficiary|applicant\s+details)': 'Beneficiary/applicant information',
            r'(?:farmer\s+id|farmer\s+profile)': 'Farmer identification structure',
            r'(?:land\s+holding|land\s+record)': 'Land record terminology',
            r'(?:family\s+details|guardian\s+name)': 'Family information structure',
            r'(?:registration\s+form|farmer\s+details)': 'Farmer registration format',
            r'(?:grievance\s+letter|complaint\s+letter)': 'Grievance/complaint format',
            r'(?:request\s+for\s+action|issue\s+resolution)': 'Action request structure',
            r'(?:grievance\s+redressal|problem\s+statement)': 'Problem statement format',
            r'(?:kindly\s+resolve|please\s+resolve)': 'Resolution request phrasing',
            r'(?:suffering\s+due\s+to|facing\s+issue)': 'Hardship description pattern',
            r'(?:pending\s+for\s+long|delayed\s+payment)': 'Delay-related terminology',
            r'(?:insurance\s+claim|claim\s+settlement)': 'Insurance claim structure',
            r'(?:crop\s+insurance|policy\s+number)': 'Insurance policy terminology',
            r'(?:premium\s+paid|insured\s+amount)': 'Insurance payment terms',
            r'(?:claim\s+form|damage\s+assessment)': 'Claim documentation format',
            r'(?:subsidy\s+claim|claim\s+form)': 'Subsidy claim structure',
            r'(?:financial\s+assistance|grant\s+application)': 'Financial aid terminology',
            r'(?:subsidy\s+amount|claim\s+amount)': 'Amount claim format',
            r'(?:government\s+aid|financial\s+support)': 'Government support terms',
            r'(?:supporting\s+document|attachment)': 'Supporting document reference',
            r'(?:certificate\s+of|proof\s+of)': 'Certificate/proof structure',
            r'(?:bank\s+passbook|id\s+proof)': 'Bank/ID documentation',
            r'(?:enclosure|annexure|appendix)': 'Document attachment terms'
        }
        
        return pattern_descriptions.get(pattern, 'Pattern match detected')
    
    def _count_keyword_occurrences(self, keyword: str, text_lower: str) -> int:
        """Count keyword occurrences consistently with safer matching logic"""
        # Short/ambiguous words that need word boundary matching
        ambiguous_words = {'form', 'app', 'id', 'claim', 'record', 'scheme', 'policy', 'proof'}
        
        if keyword in ambiguous_words:
            # Use word boundary regex for counting
            pattern = rf'\b{re.escape(keyword)}\b'
            matches = re.findall(pattern, text_lower)
            return len(matches)
        else:
            # For longer phrases, simple count is fine
            return text_lower.count(keyword)
    
    def _is_filename_token_safe(self, token: str, filename_lower: str) -> bool:
        """Safer filename token matching that avoids noisy matches"""
        # Very short/ambiguous tokens that need word boundaries
        ambiguous_tokens = {'app', 'id', 'form', 'claim'}
        
        if token in ambiguous_tokens:
            # Use word boundary regex for short tokens
            pattern = rf'\b{re.escape(token)}\b'
            return bool(re.search(pattern, filename_lower))
        else:
            # For longer tokens, simple substring is fine
            return token in filename_lower
