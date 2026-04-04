"""
Document Type Schemas
Purpose: Explicit per-document schemas that drive extraction, validation, and field completeness

These schemas define:
- Required fields (must be present for completeness)
- Optional fields (nice-to-have but extracted when available)
- Field-specific validation rules
- Document-specific business logic
"""

from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from enum import Enum


class FieldType(Enum):
    """Standard field types for extraction"""
    PERSON_NAME = "person_name"
    IDENTIFICATION = "identification"  # Aadhaar, PAN, etc.
    CONTACT = "contact"  # Phone number
    LOCATION = "location"  # Village, District, etc.
    MONEY = "money"  # Requested amount, claim amount, etc.
    AGRICULTURE = "agriculture"  # Land size, crop type, etc.
    SCHEME = "scheme"  # Scheme name, scheme type
    POLICY = "policy"  # Policy number for insurance
    DESCRIPTION = "description"  # Issue/reason text
    METADATA = "metadata"  # Reference numbers, document dates, etc.
    AUTHORITY = "authority"  # Authority, issuing body
    OTHER = "other"


@dataclass
class FieldSchema:
    """Schema for a single extraction field"""
    name: str
    field_type: FieldType
    required: bool = False
    optional: bool = False
    
    # Validation rules
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None  # Regex pattern
    allowed_values: Optional[List[str]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    
    # Extraction guidance
    synonyms: List[str] = field(default_factory=list)
    context_keywords: List[str] = field(default_factory=list)
    rejection_patterns: List[str] = field(default_factory=list)
    
    # Metadata
    description: str = ""
    examples: List[str] = field(default_factory=list)


@dataclass
class DocumentSchema:
    """Schema for a document type"""
    document_type: str
    display_name: str
    description: str
    
    # Field definitions
    required_fields: Dict[str, FieldSchema] = field(default_factory=dict)
    optional_fields: Dict[str, FieldSchema] = field(default_factory=dict)
    
    # Validation rules
    min_required_field_count: int = 1
    completeness_threshold: float = 0.8  # Percentage of fields for "complete" status
    
    # Document-specific rules
    business_rules: Dict[str, Any] = field(default_factory=dict)
    
    def get_all_fields(self) -> Dict[str, FieldSchema]:
        """Get all fields (required + optional)"""
        return {**self.required_fields, **self.optional_fields}
    
    def get_required_field_names(self) -> Set[str]:
        """Get name of all required fields"""
        return set(self.required_fields.keys())
    
    def get_optional_field_names(self) -> Set[str]:
        """Get name of all optional fields"""
        return set(self.optional_fields.keys())
    
    def is_field_required(self, field_name: str) -> bool:
        """Check if a field is required"""
        return field_name in self.required_fields
    
    def calculate_completeness(self, extracted_field_names: Set[str]) -> float:
        """Calculate completeness percentage based on extracted fields"""
        all_fields = self.get_all_fields()
        if not all_fields:
            return 0.0
        
        if not extracted_field_names:
            return 0.0
        
        match_count = len(extracted_field_names & set(all_fields.keys()))
        return match_count / len(all_fields)


# ============================================================================
# Document Type Schema Definitions
# ============================================================================

SCHEME_APPLICATION_SCHEMA = DocumentSchema(
    document_type="scheme_application",
    display_name="Scheme Application",
    description="Application for government agricultural schemes (PM-KISAN, KCC, etc.)",
    
    required_fields={
        "farmer_name": FieldSchema(
            name="farmer_name",
            field_type=FieldType.PERSON_NAME,
            required=True,
            min_length=3,
            max_length=50,
            synonyms=["applicant_name", "name", "farmer", "applicant"],
            context_keywords=["farmer", "applicant", "name", "applicant name"],
            description="Name of the applying farmer/applicant",
            examples=["Rajesh Kumar", "Sita Devi", "Mohan Singh"]
        ),
        "scheme_name": FieldSchema(
            name="scheme_name",
            field_type=FieldType.SCHEME,
            required=True,
            min_length=3,
            max_length=100,
            synonyms=["scheme", "scheme type", "program"],
            context_keywords=["scheme", "pm kisan", "pradhan mantri", "scheme name"],
            description="Name of the scheme being applied for",
            examples=["PM-KISAN", "Kisan Credit Card", "Soil Health Card"]
        ),
    },
    
    optional_fields={
        "aadhaar_number": FieldSchema(
            name="aadhaar_number",
            field_type=FieldType.IDENTIFICATION,
            required=False,
            pattern=r"^\d{4}\s*\d{4}\s*\d{4}$",
            synonyms=["aadhar", "aadhaar", "aadhaar_id"],
            context_keywords=["aadhaar", "aadhar", "identification", "id number"],
            rejection_patterns=[r"^0+$", r"^1{4}\s*1{4}\s*1{4}$"],
            description="12-digit Aadhaar number of farmer",
            examples=["1234 5678 9012", "9876 5432 1098"]
        ),
        "mobile_number": FieldSchema(
            name="mobile_number",
            field_type=FieldType.CONTACT,
            required=False,
            pattern=r"^[6-9]\d{9}$",
            synonyms=["phone", "phone_number", "contact", "mobile"],
            context_keywords=["mobile", "phone", "contact", "number"],
            rejection_patterns=[r"^0+$", r"^1{10}$"],
            description="10-digit mobile number of farmer",
            examples=["9876543210", "8765432109"]
        ),
        "requested_amount": FieldSchema(
            name="requested_amount",
            field_type=FieldType.MONEY,
            required=False,
            min_value=1,
            max_value=10000000,
            synonyms=["amount", "amount_requested", "requested", "claimed amount"],
            context_keywords=["requested amount", "amount", "rupees", "rs", "₹"],
            description="Amount requested under scheme",
            examples=["50000", "100000", "500000"]
        ),
        "village": FieldSchema(
            name="village",
            field_type=FieldType.LOCATION,
            required=False,
            min_length=2,
            max_length=50,
            synonyms=["village_name", "gram", "location"],
            context_keywords=["village", "gram", "location"],
            description="Village name where farmer resides",
            examples=["Karari", "Amanpur", "Sarai"]
        ),
        "district": FieldSchema(
            name="district",
            field_type=FieldType.LOCATION,
            required=False,
            min_length=2,
            max_length=50,
            synonyms=["district_name", "district", "tehsil"],
            context_keywords=["district", "district name"],
            description="District name",
            examples=["Kaushambi", "Banda", "Varanasi"]
        ),
        "land_size": FieldSchema(
            name="land_size",
            field_type=FieldType.AGRICULTURE,
            required=False,
            min_value=0.1,
            max_value=1000,
            synonyms=["land_area", "area", "hectare", "acre"],
            context_keywords=["land", "area", "acre", "hectare", "land size"],
            description="Size of landholding in acres/hectares",
            examples=["5 acres", "2.5 hectares", "10"]
        ),
        "crop_name": FieldSchema(
            name="crop_name",
            field_type=FieldType.AGRICULTURE,
            required=False,
            min_length=2,
            max_length=50,
            synonyms=["crop", "crop_type", "crop grown"],
            context_keywords=["crop", "crop type", "cultivated"],
            description="Primary crop grown",
            examples=["Wheat", "Rice", "Cotton"]
        ),
    },
    
    min_required_field_count=2,
    completeness_threshold=0.6,
    
    business_rules={
        "requires_identity": True,
        "allows_financial": True,
        "allows_land_info": True,
    }
)

SUBSIDY_CLAIM_SCHEMA = DocumentSchema(
    document_type="subsidy_claim",
    display_name="Subsidy Claim",
    description="Claim for government subsidy (irrigation, equipment, etc.)",
    
    required_fields={
        "farmer_name": FieldSchema(
            name="farmer_name",
            field_type=FieldType.PERSON_NAME,
            required=True,
            min_length=3,
            max_length=50,
            synonyms=["applicant_name", "claimant_name", "name"],
            context_keywords=["farmer", "applicant", "claimant", "name"],
            description="Name of the farmer making subsidy claim",
            examples=["Ravi Kumar", "Sita Devi", "Mohan Singh"]
        ),
        "claimed_amount": FieldSchema(
            name="claimed_amount",
            field_type=FieldType.MONEY,
            required=True,
            min_value=1,
            max_value=10000000,
            synonyms=["amount", "subsidy_amount", "claim_amount", "requested_amount"],
            context_keywords=["subsidy amount", "claim amount", "amount claimed", "rupees"],
            description="Amount of subsidy being claimed",
            examples=["50000", "100000", "250000"]
        ),
    },
    
    optional_fields={
        "aadhaar_number": FieldSchema(
            name="aadhaar_number",
            field_type=FieldType.IDENTIFICATION,
            required=False,
            pattern=r"^\d{4}\s*\d{4}\s*\d{4}$",
            synonyms=["aadhar", "aadhaar", "id"],
            description="Aadhaar number",
        ),
        "mobile_number": FieldSchema(
            name="mobile_number",
            field_type=FieldType.CONTACT,
            required=False,
            pattern=r"^[6-9]\d{9}$",
            synonyms=["phone", "contact"],
            description="Mobile number for contact",
        ),
        "scheme_name": FieldSchema(
            name="scheme_name",
            field_type=FieldType.SCHEME,
            required=False,
            synonyms=["scheme", "subsidy_type"],
            context_keywords=["subsidy type", "scheme", "drip", "micro irrigation"],
            description="Type of subsidy or scheme",
            examples=["Drip Irrigation Subsidy", "Micro Irrigation", "Equipment Subsidy"]
        ),
        "claim_reason": FieldSchema(
            name="claim_reason",
            field_type=FieldType.DESCRIPTION,
            required=False,
            synonyms=["reason", "purpose", "claim_description"],
            description="Reason for subsidy claim",
        ),
        "village": FieldSchema(
            name="village",
            field_type=FieldType.LOCATION,
            required=False,
            synonyms=["village_name", "gram"],
            description="Village name",
        ),
        "district": FieldSchema(
            name="district",
            field_type=FieldType.LOCATION,
            required=False,
            synonyms=["district_name"],
            description="District name",
        ),
    },
    
    min_required_field_count=2,
    completeness_threshold=0.5,
    
    business_rules={
        "requires_identity": False,
        "requires_amount": True,
        "strong_keywords": ["subsidy", "drip", "micro irrigation", "reimbursement", "installation"],
    }
)

INSURANCE_CLAIM_SCHEMA = DocumentSchema(
    document_type="insurance_claim",
    display_name="Insurance Claim",
    description="Claim for crop insurance benefits",
    
    required_fields={
        "farmer_name": FieldSchema(
            name="farmer_name",
            field_type=FieldType.PERSON_NAME,
            required=True,
            min_length=3,
            max_length=50,
            synonyms=["claimant_name", "applicant", "name"],
            description="Name of policy holder/claimant",
        ),
        "policy_number": FieldSchema(
            name="policy_number",
            field_type=FieldType.POLICY,
            required=True,
            min_length=5,
            max_length=50,
            synonyms=["policy", "policy_id", "reference"],
            context_keywords=["policy number", "policy", "policy id"],
            description="Insurance policy number",
        ),
    },
    
    optional_fields={
        "aadhaar_number": FieldSchema(
            name="aadhaar_number",
            field_type=FieldType.IDENTIFICATION,
            required=False,
            pattern=r"^\d{4}\s*\d{4}\s*\d{4}$",
        ),
        "mobile_number": FieldSchema(
            name="mobile_number",
            field_type=FieldType.CONTACT,
            required=False,
            pattern=r"^[6-9]\d{9}$",
        ),
        "claim_amount": FieldSchema(
            name="claim_amount",
            field_type=FieldType.MONEY,
            required=False,
            min_value=1,
            max_value=50000000,
            synonyms=["amount", "compensation_amount"],
            description="Claimed compensation amount",
        ),
        "cause_of_loss": FieldSchema(
            name="cause_of_loss",
            field_type=FieldType.DESCRIPTION,
            required=False,
            synonyms=["loss_reason", "cause", "damage_cause"],
            context_keywords=["damage", "loss", "weather", "pest"],
            description="Reason for insurance claim (weather, pest, etc.)",
        ),
        "crop_name": FieldSchema(
            name="crop_name",
            field_type=FieldType.AGRICULTURE,
            required=False,
            synonyms=["crop", "crop_type"],
            description="Crop affected",
        ),
        "village": FieldSchema(
            name="village",
            field_type=FieldType.LOCATION,
            required=False,
            synonyms=["village_name"],
        ),
        "district": FieldSchema(
            name="district",
            field_type=FieldType.LOCATION,
            required=False,
            synonyms=["district_name"],
        ),
    },
    
    min_required_field_count=1,
    completeness_threshold=0.5,
    
    business_rules={
        "requires_identity": False,
        "strong_keywords": ["insurance", "policy", "crop loss", "compensation", "pmfby"],
    }
)

GRIEVANCE_SCHEMA = DocumentSchema(
    document_type="grievance",
    display_name="Grievance",
    description="Farmer grievance or complaint regarding schemes/benefits",
    
    required_fields={
        "farmer_name": FieldSchema(
            name="farmer_name",
            field_type=FieldType.PERSON_NAME,
            required=True,
            min_length=3,
            max_length=50,
            synonyms=["complainant", "applicant", "name"],
            description="Name of farmer raising grievance",
        ),
    },
    
    optional_fields={
        "mobile_number": FieldSchema(
            name="mobile_number",
            field_type=FieldType.CONTACT,
            required=False,
            pattern=r"^[6-9]\d{9}$",
            description="Contact number",
        ),
        "grievance_description": FieldSchema(
            name="grievance_description",
            field_type=FieldType.DESCRIPTION,
            required=False,
            min_length=10,
            max_length=5000,
            synonyms=["issue_summary", "complaint", "description", "issue"],
            context_keywords=["grievance", "complaint", "issue", "problem"],
            description="Description of the grievance",
        ),
        "related_scheme": FieldSchema(
            name="related_scheme",
            field_type=FieldType.SCHEME,
            required=False,
            synonyms=["scheme", "scheme_name"],
            description="Related scheme if applicable",
        ),
        "aadhaar_number": FieldSchema(
            name="aadhaar_number",
            field_type=FieldType.IDENTIFICATION,
            required=False,
            pattern=r"^\d{4}\s*\d{4}\s*\d{4}$",
        ),
        "village": FieldSchema(
            name="village",
            field_type=FieldType.LOCATION,
            required=False,
            synonyms=["village_name"],
        ),
        "district": FieldSchema(
            name="district",
            field_type=FieldType.LOCATION,
            required=False,
            synonyms=["district_name"],
        ),
    },
    
    min_required_field_count=1,
    completeness_threshold=0.3,
    
    business_rules={
        "requires_identity": False,
        "allows_financial": False,
        "strong_keywords": ["grievance", "complaint", "issue", "problem", "urgent"],
    }
)

FARMER_RECORD_SCHEMA = DocumentSchema(
    document_type="farmer_record",
    display_name="Farmer Record",
    description="Farmer profile or registration record",
    
    required_fields={
        "farmer_name": FieldSchema(
            name="farmer_name",
            field_type=FieldType.PERSON_NAME,
            required=True,
            description="Name of farmer",
        ),
        "aadhaar_number": FieldSchema(
            name="aadhaar_number",
            field_type=FieldType.IDENTIFICATION,
            required=True,
            pattern=r"^\d{4}\s*\d{4}\s*\d{4}$",
            description="Aadhaar number",
        ),
    },
    
    optional_fields={
        "mobile_number": FieldSchema(
            name="mobile_number",
            field_type=FieldType.CONTACT,
            required=False,
            pattern=r"^[6-9]\d{9}$",
            description="Mobile number",
        ),
        "address": FieldSchema(
            name="address",
            field_type=FieldType.LOCATION,
            required=False,
            synonyms=["full_address", "location"],
            description="Full address",
        ),
        "village": FieldSchema(
            name="village",
            field_type=FieldType.LOCATION,
            required=False,
            synonyms=["village_name"],
        ),
        "district": FieldSchema(
            name="district",
            field_type=FieldType.LOCATION,
            required=False,
            synonyms=["district_name"],
        ),
        "land_size": FieldSchema(
            name="land_size",
            field_type=FieldType.AGRICULTURE,
            required=False,
            synonyms=["land_area", "area"],
            description="Total land area",
        ),
        "crop_name": FieldSchema(
            name="crop_name",
            field_type=FieldType.AGRICULTURE,
            required=False,
            synonyms=["crop", "crop_type"],
        ),
    },
    
    min_required_field_count=2,
    completeness_threshold=0.5,
    
    business_rules={
        "requires_identity": True,
        "allows_financial": False,
    }
)

SUPPORTING_DOCUMENT_SCHEMA = DocumentSchema(
    document_type="supporting_document",
    display_name="Supporting Document",
    description="Document provided as supporting evidence (identity proof, authority letter, etc.)",
    
    required_fields={},
    
    optional_fields={
        "farmer_name": FieldSchema(
            name="farmer_name",
            field_type=FieldType.PERSON_NAME,
            required=False,
            description="Name if mentioned in document",
        ),
        "aadhaar_number": FieldSchema(
            name="aadhaar_number",
            field_type=FieldType.IDENTIFICATION,
            required=False,
            pattern=r"^\d{4}\s*\d{4}\s*\d{4}$",
            description="Aadhaar if present",
        ),
        "mobile_number": FieldSchema(
            name="mobile_number",
            field_type=FieldType.CONTACT,
            required=False,
            pattern=r"^[6-9]\d{9}$",
            description="Contact number if present",
        ),
        "issuing_authority": FieldSchema(
            name="issuing_authority",
            field_type=FieldType.AUTHORITY,
            required=False,
            synonyms=["authority", "issuer", "issued_by"],
            description="Government authority that issued document",
        ),
        "document_reference": FieldSchema(
            name="document_reference",
            field_type=FieldType.METADATA,
            required=False,
            synonyms=["reference", "reference_number"],
            description="Reference number or ID from document",
        ),
        "document_type_detail": FieldSchema(
            name="document_type_detail",
            field_type=FieldType.METADATA,
            required=False,
            synonyms=["document_type", "doc_type"],
            description="Specific type (e.g., 'Land Certificate', 'Authority Letter')",
        ),
    },
    
    min_required_field_count=0,
    completeness_threshold=0.2,
    
    business_rules={
        "requires_identity": False,
        "allows_financial": False,
        "no_requested_amount": True,
        "no_claim_amount": True,
        "linkage_focused": True,
    }
)


# Schema registry for lookup by document type
DOCUMENT_SCHEMAS: Dict[str, DocumentSchema] = {
    "scheme_application": SCHEME_APPLICATION_SCHEMA,
    "subsidy_claim": SUBSIDY_CLAIM_SCHEMA,
    "insurance_claim": INSURANCE_CLAIM_SCHEMA,
    "grievance": GRIEVANCE_SCHEMA,
    "farmer_record": FARMER_RECORD_SCHEMA,
    "supporting_document": SUPPORTING_DOCUMENT_SCHEMA,
}


def get_schema(document_type: str) -> Optional[DocumentSchema]:
    """Get schema for a document type"""
    return DOCUMENT_SCHEMAS.get(document_type.lower())


def get_all_schemas() -> Dict[str, DocumentSchema]:
    """Get all registered schemas"""
    return DOCUMENT_SCHEMAS.copy()
