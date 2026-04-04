"""
Intelligence Layer for Agricultural Document Processing
Built on top of existing extraction output

New Part 7: Generate real officer-facing summaries and contextual insights
"""

from typing import Dict, List, Any, Optional
import logging


logger = logging.getLogger(__name__)


class IntelligenceService:
    """Service for generating insights, decisions, and predictions from extracted data"""
    
    def generate_officer_summary(
        self,
        structured_data: Dict[str, Any],
        document_type: str,
        extracted_fields: Dict[str, Any]
    ) -> str:
        """
        Generate real officer-facing summary paragraph
        
        This is NOT template-based - it generates contextual text based on actual extracted data
        
        Args:
            structured_data: Clean extracted field values
            document_type: Type of document
            extracted_fields: Fields with metadata (confidence, source, etc.)
        
        Returns:
            Officer-facing summary paragraph
        """
        
        try:
            # Get key fields
            farmer_name = structured_data.get("farmer_name", "").strip()
            location_str = self._get_best_location_for_intelligence(structured_data)
            
            # Build summary based on document type
            summary = ""
            
            if document_type == "scheme_application":
                summary = self._generate_scheme_application_summary(
                    farmer_name, location_str, structured_data, extracted_fields
                )
            elif document_type == "subsidy_claim":
                summary = self._generate_subsidy_claim_summary(
                    farmer_name, location_str, structured_data, extracted_fields
                )
            elif document_type == "insurance_claim":
                summary = self._generate_insurance_claim_summary(
                    farmer_name, location_str, structured_data, extracted_fields
                )
            elif document_type == "grievance":
                summary = self._generate_grievance_summary(
                    farmer_name, location_str, structured_data, extracted_fields
                )
            elif document_type == "farmer_record":
                summary = self._generate_farmer_record_summary(
                    farmer_name, location_str, structured_data, extracted_fields
                )
            elif document_type == "supporting_document":
                summary = self._generate_supporting_document_summary(
                    farmer_name, location_str, structured_data, extracted_fields
                )
            else:
                summary = "Document processed and awaiting officer review."
            
            return summary
        
        except Exception as e:
            logger.error(f"Error generating officer summary: {e}")
            return "Document processed and awaiting officer review."
    
    def _generate_scheme_application_summary(
        self,
        farmer_name: str,
        location_str: Optional[str],
        structured_data: Dict[str, Any],
        extracted_fields: Dict[str, Any]
    ) -> str:
        """Generate scheme application summary"""
        
        scheme_name = structured_data.get("scheme_name", "").strip()
        amount_str = self._get_best_amount_for_intelligence(structured_data, "scheme_application")
        
        parts = []
        
        if farmer_name:
            parts.append(f"{farmer_name}")
        else:
            parts.append("A farmer")
        
        parts.append("submitted a scheme application")
        
        if scheme_name and scheme_name != "unknown" and len(scheme_name) > 2:
            parts.append(f"under {scheme_name}")
        
        if location_str:
            parts.append(f"from {location_str}")
        
        # Check identity and amount presence
        has_aadhaar = "aadhaar_number" in extracted_fields
        has_mobile = "mobile_number" in extracted_fields
        
        identity_status = []
        if has_aadhaar:
            identity_status.append("identity")
        if has_mobile:
            identity_status.append("contact")
        
        if identity_status:
            parts.append(f"with present. Application contains {' and '.join(identity_status)} fields.")
        else:
            parts.append("Application identity fields require verification.")
        
        if amount_str:
            parts.append(f"Requested amount: {amount_str}.")
        
        parts.append("Document appears suitable for case review.")
        
        return " ".join(parts)
    
    def _generate_subsidy_claim_summary(
        self,
        farmer_name: str,
        location_str: Optional[str],
        structured_data: Dict[str, Any],
        extracted_fields: Dict[str, Any]
    ) -> str:
        """Generate subsidy claim summary"""
        
        subsidy_type = structured_data.get("scheme_name", "").strip()
        amount_str = self._get_best_amount_for_intelligence(structured_data, "subsidy_claim")
        claim_reason = structured_data.get("claim_reason", "").strip()
        
        parts = []
        
        if farmer_name:
            parts.append(f"{farmer_name}")
        else:
            parts.append("A farmer")
        
        parts.append("submitted a subsidy claim")
        
        if subsidy_type and subsidy_type != "unknown":
            parts.append(f"related to {subsidy_type}")
        
        if location_str:
            parts.append(f"from {location_str}")
        
        if amount_str:
            parts.append(f"for amount {amount_str}")
        
        if claim_reason:
            parts.append(f"regarding {claim_reason}")
        
        parts.append("The claim needs review for subsidy context and completeness validation.")
        
        return " ".join(parts) + "."
    
    def _generate_insurance_claim_summary(
        self,
        farmer_name: str,
        location_str: Optional[str],
        structured_data: Dict[str, Any],
        extracted_fields: Dict[str, Any]
    ) -> str:
        """Generate insurance claim summary"""
        
        policy_number = structured_data.get("policy_number", "").strip()
        amount_str = self._get_best_amount_for_intelligence(structured_data, "insurance_claim")
        cause_of_loss = structured_data.get("cause_of_loss", "").strip()
        crop_name = structured_data.get("crop_name", "").strip()
        
        parts = []
        
        if farmer_name:
            parts.append(f"{farmer_name}")
        else:
            parts.append("A farmer")
        
        parts.append("submitted a crop insurance claim")
        
        if location_str:
            parts.append(f"from {location_str}")
        
        if cause_of_loss:
            parts.append(f"related to {cause_of_loss.lower()}")
        
        if crop_name:
            parts.append(f"for {crop_name}")
        
        detail_parts = []
        if policy_number:
            detail_parts.append(f"policy {policy_number}")
        if amount_str:
            detail_parts.append(f"claimed amount {amount_str}")
        
        if detail_parts:
            parts.append(f"The document contains {' and '.join(detail_parts)}")
            parts.append("and should be reviewed for loss verification and compensation validation.")
        else:
            parts.append("and should be reviewed for documentation and loss verification.")
        
        return " ".join(parts) + "."
    
    def _generate_grievance_summary(
        self,
        farmer_name: str,
        location_str: Optional[str],
        structured_data: Dict[str, Any],
        extracted_fields: Dict[str, Any]
    ) -> str:
        """Generate grievance summary"""
        
        description = structured_data.get("grievance_description", "").strip()
        related_scheme = structured_data.get("related_scheme", "").strip()
        
        parts = []
        
        if farmer_name:
            parts.append(f"{farmer_name}")
        else:
            parts.append("A farmer")
        
        parts.append("submitted a grievance")
        
        if related_scheme:
            parts.append(f"regarding {related_scheme}")
        elif description:
            # Extract key words from description for summary
            desc_lower = description.lower()
            if "delay" in desc_lower or "pending" in desc_lower:
                parts.append("regarding delayed payment or pending benefit")
            elif "not received" in desc_lower or "no response" in desc_lower:
                parts.append("regarding non-receipt of benefit or lack of response")
            elif "reduction" in desc_lower or "inconsistency" in desc_lower:
                parts.append("regarding amount reduction or payment inconsistency")
            else:
                parts.append("regarding a service or benefit issue")
        else:
            parts.append("regarding a service issue")
        
        if location_str:
            parts.append(f"from {location_str}")
        
        parts.append("The complaint requires issue escalation and officer action review.")
        
        return " ".join(parts) + "."
    
    def _generate_farmer_record_summary(
        self,
        farmer_name: str,
        location_str: Optional[str],
        structured_data: Dict[str, Any],
        extracted_fields: Dict[str, Any]
    ) -> str:
        """Generate farmer record summary"""
        
        parts = []
        
        if farmer_name:
            parts.append(f"Record for farmer {farmer_name}")
        else:
            parts.append("Farmer record")
        
        if location_str:
            parts.append(f"from {location_str}")
        
        has_aadhaar = "aadhaar_number" in extracted_fields
        has_mobile = "mobile_number" in extracted_fields
        has_land = "land_size" in extracted_fields
        
        parts.append("contains")
        field_parts = []
        if has_aadhaar:
            field_parts.append("identity verification")
        if has_mobile:
            field_parts.append("contact information")
        if has_land:
            field_parts.append("land details")
        
        if field_parts:
            parts.append(" and ".join(field_parts))
        else:
            parts.append("farmer profile information")
        
        parts.append("and is ready for profile validation.")
        
        return " ".join(parts) + "."
    
    def _generate_supporting_document_summary(
        self,
        farmer_name: str,
        location_str: Optional[str],
        structured_data: Dict[str, Any],
        extracted_fields: Dict[str, Any]
    ) -> str:
        """Generate supporting document summary"""
        
        doc_type_detail = structured_data.get("document_type_detail", "").strip()
        issuing_authority = structured_data.get("issuing_authority", "").strip()
        document_reference = structured_data.get("document_reference", "").strip()
        
        parts = []
        
        if farmer_name:
            parts.append(f"{farmer_name} submitted a supporting document")
        else:
            parts.append("Supporting document submitted")
        
        if doc_type_detail:
            parts.append(f"- type: {doc_type_detail}")
        
        if issuing_authority:
            parts.append(f"issued by {issuing_authority}")
        
        if document_reference:
            parts.append(f"reference: {document_reference}")
        
        parts.append("The document should be linked to related application for contextual validation.")
        
        return " ".join(parts) + "."
    
    def _get_best_amount_for_intelligence(self, structured_data: Dict[str, Any], document_type: str) -> str | None:
        """Extract best amount for intelligence with strict validation rules"""
        amount_fields = ["requested_amount", "claim_amount", "subsidy_amount", "amount"]
        
        best_amount = None
        best_confidence = 0
        
        for field in amount_fields:
            if field in structured_data:
                amount_value = structured_data[field]
                if amount_value and str(amount_value).strip():
                    try:
                        # Clean amount
                        clean_amount = str(amount_value).replace(",", "").replace("₹", "").replace("$", "").strip()
                        
                        # Reject obvious year/date fragments
                        if clean_amount in ["2023", "2024", "2025", "2022", "2021", "2020"]:
                            continue
                            
                        # Reject phone-like numbers (10+ digits starting with mobile prefixes)
                        if len(clean_amount) >= 10 and clean_amount.startswith(('9', '8', '7', '6', '0')):
                            continue
                            
                        # Reject application/reference ID patterns
                        if any(pattern in clean_amount.lower() for pattern in ['id', 'ref', 'app', 'claim', 'sub']):
                            continue
                            
                        # Validate it's a reasonable amount
                        if clean_amount.replace(".", "").isdigit():
                            amount_num = float(clean_amount)
                            
                            # Document type specific validation
                            if document_type == "grievance":
                                # Only accept amounts for grievances if there's a clear compensation field
                                if field not in ["requested_amount", "claim_amount"]:
                                    continue
                            elif document_type in ["scheme_application", "subsidy_claim", "insurance_claim"]:
                                # For these types, be stricter about year-only amounts
                                if amount_num > 2000 and amount_num < 2030:
                                    # Likely a year, not an amount
                                    continue
                            
                            # Reasonable amount range check
                            if 1 <= amount_num <= 10000000:  # ₹1 to ₹1 crore
                                # Higher confidence for proper amount fields
                                field_confidence = 0.9 if field in ["requested_amount", "claim_amount", "subsidy_amount"] else 0.7
                                
                                if field_confidence > best_confidence:
                                    best_amount = f"₹{clean_amount}"
                                    best_confidence = field_confidence
                    except:
                        pass
        
        return best_amount
    
    def _extract_scheme_from_context(self, structured_data: Dict[str, Any]) -> str | None:
        """Extract scheme name from various context fields"""
        # First try direct scheme_name
        scheme_name = structured_data.get("scheme_name")
        if scheme_name and scheme_name.strip() and scheme_name != "agricultural scheme":
            # Clean the scheme name
            clean_scheme = str(scheme_name).strip()
            # Remove header junk
            if not any(junk.lower() in clean_scheme.lower() for junk in ['applicant information', 'scheme details', 'personal information']):
                return clean_scheme
        
        # Try to extract from application_id (e.g., PMKISAN/2024/UP/012345)
        application_id = structured_data.get("application_id")
        if application_id and isinstance(application_id, str):
            app_id_upper = application_id.upper()
            if "PMKISAN" in app_id_upper:
                return "Pradhan Mantri Kisan Samman Nidhi"
            elif "PM" in app_id_upper and "KISAN" in app_id_upper:
                return "Pradhan Mantri Kisan Samman Nidhi"
        
        return None
    
    def _get_primary_entity_label_and_value(self, structured_data: Dict[str, Any], document_type: str) -> tuple[str | None, str | None]:
        if document_type == "scheme_application":
            return "Scheme", self._extract_scheme_from_context(structured_data)
        elif document_type == "subsidy_claim":
            return "Subsidy", structured_data.get("subsidy_type")
        elif document_type == "insurance_claim":
            return "Claim", structured_data.get("claim_type")
        elif document_type == "grievance":
            # Use grievance_type or issue_type, fallback to description
            issue = structured_data.get("grievance_type") or structured_data.get("issue_type")
            if not issue:
                desc = structured_data.get("issue_description", "")
                if desc and len(desc) > 10:
                    issue = desc[:50] + "..." if len(desc) > 50 else desc
            return "Issue", issue
        elif document_type == "farmer_record":
            return "Record Type", "Farmer profile update"
        elif document_type == "supporting_document":
            return "Document", structured_data.get("document_type_detail", "Supporting document")
        return None, None
    
    def _get_best_location_for_intelligence(self, structured_data: Dict[str, Any]) -> str | None:
        """Get clean location information with better quality rules"""
        location_parts = []
        
        # Header junk to reject completely (case-insensitive)
        header_junk = [
            "claimant name", "from", "to", "applicant information", "personal information",
            "policy information", "scheme details", "address details", "village", "district", 
            "location", "address", "main branch", "state bank of india", "branch manager",
            "policy number", "state", "number"
        ]
        
        # Priority: village + district if both meaningful, else location, else address
        village = structured_data.get("village")
        district = structured_data.get("district")
        location = structured_data.get("location")
        address = structured_data.get("address")
        
        def is_header_junk(value: str) -> bool:
            """Check if value is header junk"""
            if not value:
                return True
            value_lower = value.lower().strip()
            # Direct match
            if any(junk in value_lower or value_lower == junk for junk in header_junk):
                return True
            # Contains header junk as a significant part
            words = value_lower.split()
            if any(junk in words for junk in header_junk):
                return True
            # Starts with header junk
            if any(value_lower.startswith(junk) for junk in header_junk):
                return True
            # REJECT: Extracted from description that looks like header junk
            if any(word in value_lower for word in ["i am", "my", "from", "to", "subject"]):
                return True
            return False
        
        def extract_location_from_text(text: str) -> list:
            """Extract location patterns from free text"""
            if not text:
                return []
            
            locations = []
            import re
            
            # Village/District patterns
            patterns = [
                r'(?:village|vill)[:\s]*\s*([^,\n]+)(?:,\s*([^,\n]+)\s*district)?',
                r'(?:district|dist)[:\s]*\s*([^,\n]+)',
                r'resident\s+of\s+([^,\n]+)(?:\s+village|\s*,)',
                r'from\s+([^,\n]+)(?:\s+village|\s*,)',
                r'([^,\n]+)\s+village',
                r'([^,\n]+)\s+district'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        locations.extend([m.strip() for m in match if m.strip()])
                    else:
                        locations.append(match.strip())
            
            return locations[:3]  # Limit to first 3 locations
        
        # Process village
        if village and str(village).strip() and not is_header_junk(str(village)):
            location_parts.append(str(village).strip())
        
        # Process district - combine with village if both exist and meaningful
        if district and str(district).strip() and not is_header_junk(str(district)):
            district_clean = str(district).strip()
            if location_parts:
                # Combine with village
                location_parts[0] = f"{location_parts[0]}, {district_clean}"
            else:
                location_parts.append(district_clean)
        
        # If no village/district combo, try location
        if not location_parts and location and str(location).strip() and not is_header_junk(str(location)):
            location_parts.append(str(location).strip())
        
        # Finally try address if still empty
        if not location_parts and address and str(address).strip():
            address_clean = str(address).strip()
            # Extract meaningful location from address
            # Try to extract village and district from address
            import re
            # Look for "Village, District" pattern
            village_district_match = re.search(r'([^,]+),\s*([^,]+) District', address_clean)
            if village_district_match:
                village = village_district_match.group(1).strip()
                district = village_district_match.group(2).strip()
                # Check if they're not header junk
                if not is_header_junk(village) and not is_header_junk(district):
                    location_parts.append(f"{village}, {district}")
            else:
                # Look for "Village, District State" pattern
                village_district_state_match = re.search(r'([^,]+),\s*([^,]+)\s+([^,]+) State', address_clean)
                if village_district_state_match:
                    village = village_district_state_match.group(1).strip()
                    district = village_district_state_match.group(2).strip()
                    if not is_header_junk(village) and not is_header_junk(district):
                        location_parts.append(f"{village}, {district}")
                elif not any(junk in address_clean.lower() for junk in header_junk):
                    # Use address as-is if it doesn't contain header junk
                    location_parts.append(address_clean)
        
        # NEW: Try to extract location from description if still no location found
        if not location_parts:
            description = structured_data.get("description", "")
            if description:
                extracted_locations = extract_location_from_text(description)
                # Filter out header junk from extracted locations
                filtered_locations = [loc for loc in extracted_locations if not is_header_junk(loc)]
                if filtered_locations:
                    location_parts.append(filtered_locations[0])
        
        # Return the best location found
        return location_parts[0] if location_parts else None
    def _clean_structured_data(self, structured_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract only trusted business fields and clean header junk"""
        trusted_fields = {
            'farmer_name', 'scheme_name', 'subsidy_type', 'subsidy_amount', 'grievance_type',
            'issue_type', 'issue_description', 'description', 'claim_type',
            'claim_amount', 'requested_amount', 'amount', 'village', 'district',
            'location', 'address', 'application_id', 'claim_id', 'farmer_id',
            'reference_number', 'document_type_detail'
        }
        
        # Header junk to remove (case-insensitive)
        header_junk = [
            'applicant information', 'personal information', 'policy information', 
            'scheme details', 'address details', 'claimant name', 'from', 'to',
            'village', 'district', 'location', 'address'
        ]
        
        cleaned = {}
        for field, value in structured_data.items():
            if field in trusted_fields and value and str(value).strip():
                # Clean the value to remove header artifacts
                clean_value = str(value).strip()
                
                # Remove common header prefixes (case-insensitive)
                value_lower = clean_value.lower()
                for junk in header_junk:
                    if value_lower == junk:
                        clean_value = ""
                        break
                    if value_lower.startswith(junk + ':') or value_lower.startswith(junk):
                        # Remove the header prefix
                        if clean_value.lower().startswith(junk + ':'):
                            clean_value = clean_value[len(junk + ':'):].strip()
                        elif clean_value.lower().startswith(junk):
                            clean_value = clean_value[len(junk):].strip()
                        break
                
                # Only keep if we have a meaningful business value
                # Preserve valid business values like "Pradhan Mantri Kisan Samman Nidhi"
                if clean_value and len(clean_value) > 1:
                    cleaned[field] = clean_value
        
        return cleaned
    
    def generate_document_summary(self, extracted_data: Dict[str, Any]) -> str:
        """
        Generate contextual, specific summary using actual extracted content
        """
        structured_data = self._clean_structured_data(extracted_data.get("structured_data", {}))
        document_type = extracted_data.get("document_type", "document")
        farmer_name = structured_data.get("farmer_name", "Unknown farmer")
        
        # Get location for context
        location = self._get_best_location_for_intelligence(structured_data)
        location_part = f" from {location}" if location else ""
        
        # Get intelligent amount with strict validation
        amount = self._get_best_amount_for_intelligence(structured_data, document_type)
        
        # Generate highly specific summary based on actual extracted content
        if document_type == "grievance":
            grievance_type = structured_data.get("grievance_type", "an issue")
            description = structured_data.get("description", "")
            
            # Extract specific details from description
            issue_details = ""
            if description:
                # Look for specific amounts, schemes, or timeframes in description
                import re
                # FLEXIBLE amount patterns - handles any amount from ₹100 to ₹99,99,999
                amount_patterns = [
                    r'(?:payment|amount|sum|total|claim|subsidy|benefit|assistance)\s+(?:of|for)?\s*₹?\s*([0-9]{1,2}(?:[0-9,]{0,7})(?:\.\d{2})?)',
                    r'₹?\s*([0-9]{1,2}(?:[0-9,]{0,7})(?:\.\d{2})?)\s*(?:rupees|rs|inr|only)',
                    r'([0-9]{1,2}(?:[0-9,]{0,7})(?:\.\d{2})?)\s*(?:rupees|rs|inr)',
                    r'₹?\s*([0-9]{1,2}(?:[0-9,]{0,7})(?:\.\d{2})?)',
                    # Specific patterns for common formats
                    r'(?:payment|amount|claim)\s+(?:of|for)?\s*₹?\s*([0-9]{3,6})',
                    r'(?:subsidy|benefit|grant)\s+(?:of|for)?\s*₹?\s*([0-9]{3,6})'
                ]
                
                amount_in_desc = None
                for pattern in amount_patterns:
                    match = re.search(pattern, description, re.IGNORECASE)
                    if match:
                        amount_str = match.group(1)
                        # Validate it's a reasonable amount (₹100 to ₹99,99,999)
                        try:
                            # Clean and parse amount
                            clean_amount = amount_str.replace(',', '').replace(' ', '')
                            amount_num = float(clean_amount)
                            if 100 <= amount_num <= 99999999:  # ₹100 to ₹9,99,99,999
                                # Format with proper commas
                                if amount_num >= 100000:
                                    formatted_amount = f"₹{int(amount_num):,}"
                                else:
                                    formatted_amount = f"₹{int(amount_num)}"
                                amount_in_desc = formatted_amount
                                break
                        except (ValueError, TypeError):
                            continue
                
                # FLEXIBLE scheme detection - handle any agricultural scheme
                scheme_patterns = [
                    r'(pm\s*kisan|pradhan\s+mantri\s+kisan|kisan\s+samman\s+nidhi)',
                    r'(kisan\s+credit|crop\s+loan|farm\s+loan)',
                    r'(crop\s+insurance|fasal\s+bima|pmfby)',
                    r'(soil\s+health\s+card|shc|soil\s+health)',
                    r'(paramparagat\s+krishi|organic|natural\s+farming)',
                    r'(national\s+mission|rkvy|nmp|nhm)',
                    r'(subsidy|grant|assistance|aid|benefit)',
                    r'(drip\s+irrigation|micro\s+irrigation|sprinkler)',
                    r'(seeds|fertilizer|pesticide|machinery|equipment)',
                    r'(green\s+revolution|white\s+revolution|blue\s+revolution)',
                    # Generic scheme indicators
                    r'(scheme|yojana|program|project|initiative)'
                ]
                
                scheme_mentioned = None
                for pattern in scheme_patterns:
                    match = re.search(pattern, description, re.IGNORECASE)
                    if match:
                        scheme_mentioned = match.group(1)
                        # Normalize common scheme names
                        scheme_lower = scheme_mentioned.lower()
                        if 'pm kisan' in scheme_lower or 'pradhan mantri kisan' in scheme_lower:
                            scheme_mentioned = "PM Kisan"
                        elif 'kisan credit' in scheme_lower:
                            scheme_mentioned = "Kisan Credit"
                        elif 'crop insurance' in scheme_lower or 'fasal bima' in scheme_lower:
                            scheme_mentioned = "Crop Insurance"
                        elif 'soil health' in scheme_lower:
                            scheme_mentioned = "Soil Health Card"
                        elif 'paramparagat' in scheme_lower:
                            scheme_mentioned = "Paramparagat Krishi"
                        break
                
                # Extract issue type from description
                issue_type = None
                issue_patterns = [
                    r'(delay|delayed|pending|not\s+received|not\s+credited|yet\s+to\s+be)',
                    r'(rejection|rejected|not\s+approved|denied)',
                    r'(incomplete|missing|insufficient|inadequate)',
                    r'(error|mistake|incorrect|wrong)',
                    r'(damage|destroyed|lost|affected)',
                    r'(request|apply|application|submission)'
                ]
                
                for pattern in issue_patterns:
                    match = re.search(pattern, description, re.IGNORECASE)
                    if match:
                        issue_type = match.group(1)
                        break
                
                # Build issue details with flexible logic
                if amount_in_desc and scheme_mentioned:
                    issue_details = f" regarding {scheme_mentioned} payment of {amount_in_desc}"
                elif amount_in_desc and issue_type:
                    issue_details = f" regarding payment of {amount_in_desc}"
                elif scheme_mentioned:
                    issue_details = f" regarding {scheme_mentioned} benefits"
                elif amount_in_desc:
                    issue_details = f" regarding payment of {amount_in_desc}"
                elif issue_type:
                    issue_details = f" regarding {issue_type}"
                else:
                    # Use first 60 chars of description if no specific details
                    issue_details = f" regarding {description[:60]}..." if len(description) > 60 else f" regarding {description}"
            
            return f"{farmer_name}{location_part} has filed a grievance{issue_details}. This requires immediate attention for resolution."
        
        elif document_type == "scheme_application":
            scheme_name = self._extract_scheme_from_context(structured_data)
            if scheme_name:
                amount_part = f" for {amount}" if amount else ""
                return f"{farmer_name}{location_part} is applying for {scheme_name}{amount_part}. Application appears complete for processing."
            else:
                return f"{farmer_name}{location_part} submitted a scheme application{f' requesting {amount}' if amount else ''}. Scheme identification needed for further processing."
        
        elif document_type == "subsidy_claim":
            subsidy_type = structured_data.get("subsidy_type", "agricultural subsidy")
            description = structured_data.get("description", "")
            
            # Extract specific details from description for subsidy claims
            claim_details = ""
            if description:
                import re
                # Look for equipment, purpose, or timeline details
                equipment_patterns = [
                    r'(tractor|pump|irrigation|seeder|harvester|tiller)',
                    r'(equipment|machinery|tool|implement)'
                ]
                
                equipment_mentioned = None
                for pattern in equipment_patterns:
                    match = re.search(pattern, description, re.IGNORECASE)
                    if match:
                        equipment_mentioned = match.group(1).lower()
                        break
                
                # Look for purpose/reason
                purpose_patterns = [
                    r'for\s+(.+?)(?:\s+in\s+(?:field|farm)|\.|$)',
                    r'purpose\s*:?\s*(.+?)(?:\.|$)',
                    r'reason\s*:?\s*(.+?)(?:\.|$)'
                ]
                
                purpose_mentioned = None
                for pattern in purpose_patterns:
                    match = re.search(pattern, description, re.IGNORECASE)
                    if match:
                        purpose_mentioned = match.group(1).strip()
                        if len(purpose_mentioned) > 3:
                            break
                
                if equipment_mentioned and amount:
                    claim_details = f" for {equipment_mentioned} purchase worth {amount}"
                elif equipment_mentioned:
                    claim_details = f" for {equipment_mentioned} equipment"
                elif purpose_mentioned:
                    claim_details = f" for {purpose_mentioned[:30]}..." if len(purpose_mentioned) > 30 else f" for {purpose_mentioned}"
                elif amount:
                    claim_details = f" for {subsidy_type} worth {amount}"
            
            if claim_details:
                return f"{farmer_name}{location_part} has submitted a subsidy claim{claim_details}. Claim ready for financial verification."
            elif amount:
                return f"{farmer_name}{location_part} is claiming {amount} for {subsidy_type}. Claim ready for financial verification."
            else:
                return f"{farmer_name}{location_part} has submitted a {subsidy_type} claim. Amount details require verification."
        
        elif document_type == "insurance_claim":
            claim_type = structured_data.get("claim_type", "crop insurance")
            description = structured_data.get("description", "")
            
            # Extract specific details from description for insurance claims
            claim_details = ""
            if description:
                import re
                # Look for crop types, damage causes, or affected area
                crop_patterns = [
                    r'(wheat|rice|paddy|cotton|sugarcane|maize|corn|pulses|vegetables)',
                    r'(kharif|rabi|zaid)\s+(crop|crops)'
                ]
                
                crop_mentioned = None
                for pattern in crop_patterns:
                    match = re.search(pattern, description, re.IGNORECASE)
                    if match:
                        crop_mentioned = match.group(1).lower()
                        break
                
                # Look for damage causes
                damage_patterns = [
                    r'(flood|drought|pest|disease|fire|storm|heavy rain|excess rain)',
                    r'(damaged|destroyed|affected|lost|ruined)\s+by\s+(.+?)(?:\.|$)'
                ]
                
                damage_mentioned = None
                for pattern in damage_patterns:
                    match = re.search(pattern, description, re.IGNORECASE)
                    if match:
                        damage_mentioned = match.group(1) if len(match.groups()) > 1 else match.group(0)
                        damage_mentioned = damage_mentioned.lower()
                        break
                
                # Look for area affected
                area_patterns = [
                    r'(\d+(?:\.\d+)?)\s*(?:acre|hectare|bigha)',
                    r'area\s*:?\s*(\d+(?:\.\d+)?)'
                ]
                
                area_mentioned = None
                for pattern in area_patterns:
                    match = re.search(pattern, description, re.IGNORECASE)
                    if match:
                        area_mentioned = f"{match.group(1)} acres"
                        break
                
                details_parts = []
                if crop_mentioned:
                    details_parts.append(f"{crop_mentioned} crop")
                if damage_mentioned:
                    details_parts.append(f"damaged by {damage_mentioned}")
                if area_mentioned:
                    details_parts.append(f"affecting {area_mentioned}")
                if amount:
                    details_parts.append(f"claiming {amount}")
                
                if details_parts:
                    claim_details = " for " + ", ".join(details_parts[:2])  # Limit to 2 details
            
            if claim_details:
                return f"{farmer_name}{location_part} filed an insurance claim{claim_details}. Damage assessment needed."
            elif amount:
                return f"{farmer_name}{location_part} filed an insurance claim for {amount} under {claim_type}. Damage assessment needed."
            else:
                return f"{farmer_name}{location_part} submitted a {claim_type} claim. Claim amount and damage details require verification."
        
        elif document_type == "farmer_record":
            # Extract specific details for farmer records
            record_type = structured_data.get("record_type", "profile update")
            description = structured_data.get("description", "")
            
            record_details = ""
            if description:
                import re
                # Look for what's being updated
                update_patterns = [
                    r'(address|contact|mobile|phone|bank|account|aadhaar|pan)',
                    r'(change|update|modify|correct)\s+(.+?)(?:\.|$)'
                ]
                
                update_mentioned = None
                for pattern in update_patterns:
                    match = re.search(pattern, description, re.IGNORECASE)
                    if match:
                        update_mentioned = match.group(1).lower()
                        break
                
                if update_mentioned:
                    record_details = f" to update {update_mentioned} information"
                else:
                    record_details = " for profile verification"
            
            return f"{farmer_name}{location_part} submitted farmer record{record_details}. Identity verification completed."
        
        elif document_type == "supporting_document":
            doc_detail = structured_data.get("document_type_detail", "supporting document")
            description = structured_data.get("description", "")
            
            # Extract context for supporting documents
            support_context = ""
            if description:
                import re
                # Look for what this document supports
                purpose_patterns = [
                    r'(proof|evidence|support|verification)\s+of\s+(.+?)(?:\.|$)',
                    r'(for|against|regarding)\s+(.+?)(?:\.|$)',
                    r'(application|claim|scheme|subsidy|insurance)'
                ]
                
                purpose_mentioned = None
                for pattern in purpose_patterns:
                    match = re.search(pattern, description, re.IGNORECASE)
                    if match:
                        purpose_mentioned = match.group(1) if len(match.groups()) > 1 else match.group(0)
                        if len(purpose_mentioned) > 3:
                            break
                
                if purpose_mentioned:
                    support_context = f" as {purpose_mentioned} evidence"
                else:
                    support_context = " for case validation"
            
            return f"{farmer_name}{location_part} provided {doc_detail}{support_context}. Document requires linkage to main application."
        
        else:
            return f"{farmer_name}{location_part} submitted a {document_type.replace('_', ' ')}{f' for {amount}' if amount else ''} for processing."
    
    def generate_case_insight(self, extracted_data: Dict[str, Any]) -> List[str]:
        """
        Generate structured bullet points with dynamic labels
        """
        structured_data = self._clean_structured_data(extracted_data.get("structured_data", {}))
        document_type = extracted_data.get("document_type", "")
        insights = []
        
        # 1. Farmer: <name>
        farmer_name = structured_data.get("farmer_name")
        if farmer_name and farmer_name.strip():
            insights.append(f"Farmer: {farmer_name.strip()}")
        
        # 2. Request: <actual request>
        request_desc = {
            "scheme_application": "Scheme application",
            "subsidy_claim": "Subsidy claim", 
            "grievance": "Grievance filing",
            "insurance_claim": "Insurance claim",
            "farmer_record": "Record update",
            "supporting_document": "Document review"
        }.get(document_type, "Document processing")
        
        insights.append(f"Request: {request_desc}")
        
        # 3. Dynamic label: <entity value>
        label, entity_value = self._get_primary_entity_label_and_value(structured_data, document_type)
        if label and entity_value and str(entity_value).strip():
            # For scheme_application, always include scheme if it exists
            if document_type == "scheme_application" and label == "Scheme":
                insights.append(f"{label}: {entity_value.strip()}")
            else:
                insights.append(f"{label}: {entity_value.strip()}")
        
        # 4. Amount: ₹<amount> (only if valid and appropriate)
        amount = self._get_best_amount_for_intelligence(structured_data, document_type)
        if amount:
            insights.append(f"Amount: {amount}")
        
        # 5. Location: <best location> (only if valid)
        location = self._get_best_location_for_intelligence(structured_data)
        if location:
            insights.append(f"Location: {location}")
        
        return insights
    
    def generate_decision_support(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate decision support with exact contract
        
        RETURN EXACTLY:
        {
          "decision": "approve" | "review" | "reject",
          "confidence": float,
          "reasoning": [...]
        }
        """
        confidence = extracted_data.get("confidence", 0)
        missing_fields = extracted_data.get("missing_fields", [])
        structured_data = extracted_data.get("structured_data", {})
        document_type = extracted_data.get("document_type", "")
        
        # Count critical missing fields
        critical_missing = [f for f in missing_fields if self._is_critical_field(f)]
        
        # Get amount for context-aware decisions
        amount = self._get_best_amount_for_intelligence(structured_data, document_type)
        amount_value = 0
        if amount:
            try:
                amount_value = float(amount.replace("₹", "").replace(",", "").replace("$", ""))
            except:
                pass
        
        # Context-aware decision engine
        reasoning = []
        
        # CASE 1: APPROVE
        if confidence >= 0.8 and len(critical_missing) == 0 and document_type not in ["supporting_document"]:
            decision = "approve"
            reasoning = ["High confidence extraction", "All critical fields present"]
        
        # CASE 2: REVIEW
        elif confidence >= 0.5 or len(critical_missing) <= 2 or amount_value > 100000 or document_type == "supporting_document":
            decision = "review"
            
            # Smart reasoning based on context
            if document_type == "supporting_document":
                reasoning.append("Supporting document requires linkage validation")
            elif amount_value > 100000:
                reasoning.append("High value request requires manual verification")
            elif len(critical_missing) > 0:
                reasoning.append(f"Missing {len(critical_missing)} critical identity or scheme details")
            elif confidence < 0.5:
                reasoning.append("Low extraction confidence")
            else:
                reasoning.append("Requires manual verification")
        
        # CASE 3: REJECT
        else:
            decision = "reject"
            
            if len(critical_missing) > 2:
                reasoning.append("Missing key identity or scheme details")
            elif confidence < 0.5:
                reasoning.append("Low extraction confidence")
            else:
                reasoning.append("Insufficient data for processing")
        
        # Limit to max 3 reasoning points
        reasoning = reasoning[:3]
        
        return {
            "decision": decision,
            "confidence": confidence,
            "reasoning": reasoning
        }
    
    def generate_predictions(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate predictive insights with priority engine
        
        RETURN:
        {
          processing_time: "X days",
          approval_likelihood: "X%",
          risk_level: "Low | Medium | High",
          priority_score: int,
          queue: str,
          prediction_method: str
        }
        """
        confidence = extracted_data.get("confidence", 0)
        missing_fields = extracted_data.get("missing_fields", [])
        structured_data = extracted_data.get("structured_data", {})
        document_type = extracted_data.get("document_type", "")
        
        # Processing time calculation
        base_time = 2
        time_penalty = len(missing_fields)  # +1 per missing field
        amount_penalty = 0
        
        # Check for amount fields
        amount = self._get_best_amount_for_intelligence(structured_data, document_type)
        amount_value = 0
        if amount:
            try:
                amount_value = float(amount.replace("₹", "").replace(",", "").replace("$", ""))
                if amount_value > 100000:
                    amount_penalty = 2
            except:
                pass
        
        processing_time = base_time + time_penalty + amount_penalty
        
        # Approval likelihood calculation
        likelihood = 50  # Base 50%
        if len(missing_fields) == 0:
            likelihood += 20  # +20% if no missing fields
        if confidence > 0.8:
            likelihood += 20  # +20% if confidence > 0.8
        
        critical_missing = [f for f in missing_fields if self._is_critical_field(f)]
        if len(critical_missing) > 0:
            likelihood -= 20  # -20% if missing critical fields
        
        likelihood = max(0, min(100, likelihood))  # Clamp between 0-100
        
        # Risk level
        if confidence > 0.75 and len(critical_missing) == 0:
            risk_level = "Low"
        elif confidence >= 0.5 and len(critical_missing) <= 2:
            risk_level = "Medium"
        else:
            risk_level = "High"
        
        # Priority Engine (Real Intelligence)
        priority_score = 40  # Base score
        queue = "standard_processing"
        
        # Check for grievance urgency
        if document_type == "grievance":
            # Look for urgency keywords in text
            text_content = " ".join([str(v) for v in structured_data.values() if v]).lower()
            if "delay" in text_content or "urgent" in text_content:
                priority_score = 90
                queue = "high_priority"
        
        # High value requests
        elif amount_value > 100000:
            priority_score = 80
            queue = "financial_review"
        
        # Missing fields require verification
        elif len(missing_fields) > 0:
            priority_score = 60
            queue = "verification_queue"
        
        # Priority score is already set to 40 for standard processing
        
        return {
            "processing_time": f"{processing_time} days",
            "approval_likelihood": f"{likelihood}%",
            "risk_level": risk_level,
            "priority_score": priority_score,
            "queue": queue,
            "prediction_method": "rule_based_fallback"
        }
    
    # Helper methods (private)
    
    def _get_main_purpose(self, structured_data: Dict[str, Any], document_type: str) -> str:
        """Determine main purpose based on document type and data"""
        if document_type == "scheme_application":
            scheme = structured_data.get("scheme_name", "agricultural scheme")
            if not scheme or scheme == "agricultural scheme":
                # Try to extract from other fields or use fallback
                return "scheme application"
            return f"application for {scheme}"
        elif document_type == "subsidy_claim":
            return "subsidy claim reimbursement"
        elif document_type == "grievance":
            issue = structured_data.get("issue_type", "issue")
            return f"{issue} grievance"
        elif document_type == "insurance_claim":
            return "insurance claim for crop damage"
        elif document_type == "farmer_record":
            return "farmer record update"
        else:
            return "document processing"
    
    def _get_key_info(self, structured_data: Dict[str, Any], document_type: str) -> str:
        """Get key information like amount, scheme, issue"""
        if document_type == "scheme_application":
            scheme = structured_data.get("scheme_name", "a scheme")
            if not scheme or scheme == "a scheme":
                return "scheme participation"
            return f"participation in {scheme}"
        elif document_type == "subsidy_claim":
            amount = structured_data.get("claim_amount", structured_data.get("amount", "unspecified amount"))
            return f"subsidy claim for {amount}"
        elif document_type == "grievance":
            issue = structured_data.get("issue_description", "unspecified issue")
            return f"resolution of {issue[:50]}..." if len(issue) > 50 else issue
        elif document_type == "insurance_claim":
            amount = structured_data.get("claim_amount", structured_data.get("amount", "unspecified amount"))
            return f"insurance claim for {amount}"
        elif document_type == "farmer_record":
            return "record verification and update"
        else:
            return "document processing"
    
    def _get_request_type(self, structured_data: Dict[str, Any], document_type: str) -> str:
        """Get request type description"""
        if document_type == "scheme_application":
            scheme = structured_data.get("scheme_name", "scheme")
            return f"Application for {scheme}"
        elif document_type == "subsidy_claim":
            return "Subsidy reimbursement"
        elif document_type == "grievance":
            issue = structured_data.get("issue_type", "General grievance")
            return f"{issue} grievance"
        elif document_type == "insurance_claim":
            return "Crop insurance claim"
        elif document_type == "farmer_record":
            return "Record update"
        else:
            return "Document processing"
    
    def _get_key_data_points(self, structured_data: Dict[str, Any]) -> List[str]:
        """Extract key data points for insights"""
        data_points = []
        
        # Amount fields
        amount_fields = {
            "amount": "Amount",
            "claim_amount": "Claim Amount", 
            "subsidy_amount": "Subsidy Amount",
            "loan_amount": "Loan Amount"
        }
        
        for field, label in amount_fields.items():
            if field in structured_data:
                value = structured_data[field]
                data_points.append(f"{label}: {value}")
                break  # Only include one amount field
        
        # Scheme/program
        if "scheme_name" in structured_data:
            data_points.append(f"Scheme: {structured_data['scheme_name']}")
        
        # Date
        date_fields = ["application_date", "submission_date", "claim_date"]
        
        return data_points
    
    def _is_critical_field(self, field_name: str) -> bool:
        """Check if a field is critical for document processing"""
        critical_fields = {
            "farmer_name", "scheme_name", "claim_type", 
            "policy_number", "grievance_type", "aadhaar_number",
            "mobile_number", "requested_amount", "claim_amount",
            "subsidy_amount", "description", "issue_description"
        }
        return field_name in critical_fields
        for field in date_fields:
            if field in structured_data:
                data_points.append(f"Date: {structured_data[field]}")
                break
        
        # ID fields
        id_fields = ["application_id", "farmer_id", "claim_id"]
        for field in id_fields:
            if field in structured_data:
                data_points.append(f"ID: {structured_data[field]}")
                break
        
        return data_points[:2]  # Limit to 2 data points to keep total under 5
    
    def _is_critical_field(self, field_name: str) -> bool:
        """Determine if a field is critical for processing"""
        critical_fields = {
            "farmer_name", "applicant_name", "name",
            "application_id", "claim_id", "farmer_id",
            "scheme_name", "issue_type", "claim_amount",
            "amount", "village", "district"
        }
        return field_name.lower() in [f.lower() for f in critical_fields]
