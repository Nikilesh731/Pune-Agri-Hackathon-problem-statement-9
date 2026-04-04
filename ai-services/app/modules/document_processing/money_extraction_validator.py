"""
Strict Money Extraction Validator
Purpose: Validates financial field extraction with strict rules to prevent:
- Wrong amounts from being extracted
- Reference IDs being confused with amounts
- Years being extracted as amounts
- Aadhaar/Phone numbers being extracted as amounts
- Truncated or malformed amounts

Key rule: Money extraction MUST have explicit financial context
"""

import re
from typing import Optional, Dict, Any, Tuple, List


class MoneyExtractionValidator:
    """Strict validator for financial field extraction"""
    
    # Explicit financial context keywords that ALLOW amount extraction
    ALLOWED_AMOUNT_CONTEXTS = {
        "requested_amount": [
            "requested amount", "amount requested", "request amount",
            "total requested", "amount of request"
        ],
        "claim_amount": [
            "claim amount", "amount claimed", "claimed amount",
            "claim value", "amount of claim"
        ],
        "subsidy_amount": [
            "subsidy amount", "subsidy requested", "subsidy value",
            "subsidy claim", "government subsidy"
        ],
        "compensation_amount": [
            "compensation amount", "compensation value", "compensation paid",
            "insurance payout"
        ],
        "premium_paid": [
            "premium paid", "premium amount", "insurance premium",
            "policy premium"
        ],
        "loan_amount": [
            "loan amount", "loan requested", "credit amount",
            "kisan credit"
        ]
    }
    
    # Patterns that indicate financial context
    FINANCIAL_CONTEXT_PATTERNS = [
        r"rs[.\s]*\d+",  # Rs amount
        r"₹\s*\d+",  # Rupee symbol
        r"\bcurrency\b",
        r"\bpayment\b",
        r"\bfunding\b",
        r"\bcost\b",
        r"\bprice\b",
        r"\bclaim\b",
        r"\bsubsidy\b",
        r"\bcompensation\b",
        r"\bloan\b",
        r"\bcredit\b",
    ]
    
    # Patterns that indicate NON-financial contexts (reject if present)
    NON_FINANCIAL_CONTEXT_PATTERNS = [
        r"\breference\b",
        r"\bapplication\b",
        r"\bdocument\b",
        r"\bid\s+number\b",
        r"\code\b",
        r"\bseries\b",
        r"\bversion\b",
        r"\bchapter\b",
        r"\bsection\b",
        r"\barticle\b",
        r"\bclause\b",
    ]
    
    # Year patterns to reject
    YEAR_PATTERNS = [
        r"^(19|20)\d{2}$",  # 1900-2099
        r"^(2020|2021|2022|2023|2024|2025|2026)$",  # Specific years
    ]
    
    # Phone-like patterns to reject
    PHONE_PATTERNS = [
        r"^[6-9]\d{9}$",  # Indian mobile
        r"^\+91\d{10}$",  # International format
    ]
    
    # Aadhaar-like patterns to reject
    AADHAAR_PATTERNS = [
        r"^\d{4}\s*\d{4}\s*\d{4}$",  # Aadhaar format
    ]
    
    def __init__(self):
        pass
    
    def validate_money_extraction(
        self,
        value: Any,
        field_name: str,
        surrounding_text: str = "",
        document_type: str = "unknown"
    ) -> Tuple[bool, float, str]:
        """
        Validate if a value should be extracted as money
        
        Args:
            value: The value to validate
            field_name: Name of the money field (e.g., "requested_amount")
            surrounding_text: Text around the value for context analysis
            document_type: Type of document being processed
        
        Returns:
            Tuple of (is_valid, confidence, rejection_reason)
            - is_valid: Whether value passes validation
            - confidence: Confidence score (0.0-1.0) if valid
            - rejection_reason: Reason if rejected
        """
        
        if value is None:
            return False, 0.0, "Value is None"
        
        value_str = str(value).strip()
        
        if not value_str:
            return False, 0.0, "Value is empty"
        
        # Step 1: Check for disallowed patterns
        disallow_result = self._check_disallowed_patterns(value_str)
        if not disallow_result["allowed"]:
            return False, 0.0, disallow_result["reason"]
        
        # Step 2: Check for explicit financial context requirement
        context_check = self._check_financial_context(
            value_str=value_str,
            field_name=field_name,
            surrounding_text=surrounding_text
        )
        
        if not context_check["has_context"]:
            return False, 0.0, context_check["reason"]
        
        # Step 3: Validate numeric format and range
        numeric_check = self._validate_numeric_format(value_str, field_name, document_type)
        
        if not numeric_check["valid"]:
            return False, 0.0, numeric_check["reason"]
        
        # Step 4: Document-type specific validation
        doc_type_check = self._validate_for_document_type(
            value_str=value_str,
            field_name=field_name,
            document_type=document_type
        )
        
        if not doc_type_check["valid"]:
            return False, 0.0, doc_type_check["reason"]
        
        # All checks passed - return valid
        return True, 0.9, ""
    
    def _check_disallowed_patterns(self, value_str: str) -> Dict[str, Any]:
        """Check if value matches disallowed patterns"""
        
        value_clean = value_str.replace(",", "").replace("₹", "").replace("$", "").strip()
        
        # Check if it's a year
        for pattern in self.YEAR_PATTERNS:
            if re.match(pattern, value_clean):
                return {
                    "allowed": False,
                    "reason": f"Value looks like a year: {value_str}"
                }
        
        # Check if it's a phone number
        for pattern in self.PHONE_PATTERNS:
            if re.match(pattern, value_clean):
                return {
                    "allowed": False,
                    "reason": f"Value looks like a phone number: {value_str}"
                }
        
        # Check if it's Aadhaar-like
        for pattern in self.AADHAAR_PATTERNS:
            if re.match(pattern, value_clean):
                return {
                    "allowed": False,
                    "reason": f"Value looks like Aadhaar number: {value_str}"
                }
        
        # Check for very long digit sequences (likely reference IDs)
        if re.match(r"^\d{12,}$", value_clean):
            return {
                "allowed": False,
                "reason": f"Value is very long number sequence (likely ID): {value_str}"
            }
        
        # Check for reference ID patterns
        reference_patterns = [
            r"^[A-Z]{2,}\d+",  # PMKISAN/2024/UP/012345
            r"^[A-Z][A-Z0-9]*\/\d+",  # APP/123456
            r"^REF\d+",  # REF123
            r"^APP\d+",  # APP123
            r"^CLAIM\d+",  # CLAIM123
        ]
        
        for pattern in reference_patterns:
            if re.match(pattern, value_str, re.IGNORECASE):
                return {
                    "allowed": False,
                    "reason": f"Value looks like a reference ID: {value_str}"
                }
        
        return {"allowed": True, "reason": ""}
    
    def _check_financial_context(
        self,
        value_str: str,
        field_name: str,
        surrounding_text: str
    ) -> Dict[str, Any]:
        """Check if value has explicit financial context"""
        
        # For supporting documents, financial fields should not exist
        # This check should be done at schema level, but validate here too
        if field_name in ["requested_amount", "claim_amount", "subsidy_amount", "amount"]:
            # Check for explicit context keywords for this field type
            context_keywords = self.ALLOWED_AMOUNT_CONTEXTS.get(field_name, [])
            
            # Also check broader financial context patterns
            all_context_patterns = context_keywords + [
                "requested", "claimed", "compensation", "subsidy",
                "premium", "cost", "price", "loan", "credit"
            ]
            
            # Check if any keyword appears in surrounding text
            surrounding_lower = surrounding_text.lower()
            
            has_context = False
            for keyword in all_context_patterns:
                if keyword.lower() in surrounding_lower:
                    has_context = True
                    break
            
            if not has_context:
                # Check for financial context patterns
                for pattern in self.FINANCIAL_CONTEXT_PATTERNS:
                    if re.search(pattern, surrounding_lower):
                        has_context = True
                        break
            
            if not has_context:
                return {
                    "has_context": False,
                    "reason": f"No explicit financial context found for {field_name}"
                }
            
            # Check for non-financial context that would reject the amount
            for pattern in self.NON_FINANCIAL_CONTEXT_PATTERNS:
                if re.search(pattern, surrounding_lower):
                    return {
                        "has_context": False,
                        "reason": f"Non-financial context detected: {pattern}"
                    }
        
        return {"has_context": True, "reason": ""}
    
    def _validate_numeric_format(
        self,
        value_str: str,
        field_name: str,
        document_type: str
    ) -> Dict[str, Any]:
        """Validate numeric format and range"""
        
        # Clean value
        value_clean = value_str.replace(",", "").replace("₹", "").replace("$", "").strip()
        
        # Reject if contains non-numeric characters (except standard formatting)
        if not re.match(r"^\d+(?:\.\d{2})?$", value_clean):
            # Check if it's a float with more decimals
            if not re.match(r"^\d+(?:\.\d+)?$", value_clean):
                return {
                    "valid": False,
                    "reason": f"Value contains non-numeric characters: {value_str}"
                }
        
        # Convert to float
        try:
            amount_float = float(value_clean)
        except ValueError:
            return {
                "valid": False,
                "reason": f"Cannot parse as number: {value_str}"
            }
        
        # Check range
        MIN_AMOUNT = 1
        MAX_AMOUNT = 10000000  # 1 crore
        
        if amount_float < MIN_AMOUNT:
            return {
                "valid": False,
                "reason": f"Amount too small: {amount_float} < {MIN_AMOUNT}"
            }
        
        if amount_float > MAX_AMOUNT:
            return {
                "valid": False,
                "reason": f"Amount too large: {amount_float} > {MAX_AMOUNT}"
            }
        
        # Reject truncated amounts (e.g., "600" when should be "6000" or "6,000")
        # This is a heuristic - if amount is suspiciously small and looks truncated
        if amount_float < 100 and len(value_clean) >= 4:
            # Might be truncated like "2,60" from "2,60,000"
            if "," in value_str or value_clean.endswith("60"):
                return {
                    "valid": False,
                    "reason": f"Value appears truncated: {value_str}"
                }
        
        return {"valid": True, "reason": ""}
    
    def _validate_for_document_type(
        self,
        value_str: str,
        field_name: str,
        document_type: str
    ) -> Dict[str, Any]:
        """Apply document-type specific validation"""
        
        # Supporting documents should NOT have financial fields
        if document_type == "supporting_document":
            if field_name in ["requested_amount", "claim_amount", "subsidy_amount", "loan_amount"]:
                return {
                    "valid": False,
                    "reason": f"Supporting documents should not have {field_name}"
                }
        
        # Grievances should not have financial fields
        if document_type == "grievance":
            if field_name in ["requested_amount", "claim_amount", "subsidy_amount"]:
                return {
                    "valid": False,
                    "reason": f"Grievances should not have {field_name}"
                }
        
        # Farmer records should not have financial fields
        if document_type == "farmer_record":
            if field_name in ["requested_amount", "claim_amount", "subsidy_amount", "loan_amount"]:
                return {
                    "valid": False,
                    "reason": f"Farmer records should not have {field_name}"
                }
        
        return {"valid": True, "reason": ""}
    
    def normalize_money_value(self, value: str) -> str:
        """
        Normalize Indian money format to standard format
        
        Examples:
        - "6,000" -> "6000"
        - "2,60,000" -> "260000"
        - "75,000" -> "75000"
        """
        if not value:
            return ""
        
        # Remove currency symbols
        value = value.replace("₹", "").replace("$", "").strip()
        
        # Handle Indian number format (2,60,000 -> 260000)
        # Pattern: digit, comma, 2 digits, comma, 3 digits
        if re.match(r"^\d+,\d{2},\d{3}$", value):
            value = value.replace(",", "")
        # Handle standard format (75,000 -> 75000)
        elif re.match(r"^\d+,\d{3}(?:,\d{3})*$", value):
            value = value.replace(",", "")
        # Otherwise just remove all commas
        else:
            value = value.replace(",", "")
        
        return value
    
    def get_safe_amount_for_display(
        self,
        value: Optional[str],
        field_name: str,
        surrounding_text: str = "",
        document_type: str = "unknown"
    ) -> Optional[str]:
        """
        Get safe amount value for display, or None if not valid
        
        Returns formatted amount like "₹6,00,000" or None
        """
        
        if not value:
            return None
        
        # Validate
        is_valid, confidence, reason = self.validate_money_extraction(
            value=value,
            field_name=field_name,
            surrounding_text=surrounding_text,
            document_type=document_type
        )
        
        if not is_valid:
            return None
        
        # Normalize
        normalized = self.normalize_money_value(value)
        
        # Format for display (Indian format)
        try:
            amount_int = int(float(normalized))
            # Convert to Indian format with commas
            return self._format_indian_currency(amount_int)
        except Exception:
            return None
    
    def _format_indian_currency(self, amount: int) -> str:
        """Format amount in Indian currency format"""
        # Convert to string and reverse for easier processing
        amount_str = str(amount)
        reversed_str = amount_str[::-1]
        
        # Insert commas
        parts = []
        for i, char in enumerate(reversed_str):
            if i > 0 and i % 2 == 0 and i < 5:  # Every 2 digits up to last 5
                parts.append(",")
            elif i == 5:
                parts.append(",")  # Comma after 5th digit (hundreds of thousands)
            elif i > 5 and (i - 5) % 2 == 0:  # Every 2 digits after that
                parts.append(",")
            parts.append(char)
        
        # Reverse back
        formatted = "".join(parts)[::-1]
        return f"₹{formatted}"
