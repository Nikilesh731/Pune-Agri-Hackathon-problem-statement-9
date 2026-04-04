import ast
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

ROOT = Path(__file__).resolve().parents[1]

INCLUDE_DIRS = [
    ROOT / "app" / "modules" / "document_processing",
]

EXCLUDE_DIRS = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".git",
    "venv",
    "node_modules",
}

OUTPUT_FILE = ROOT / "docs" / "document-processing-code-context.md"


def is_python_file(path: Path) -> bool:
    return path.is_file() and path.suffix == ".py"


def should_skip(path: Path) -> bool:
    return any(part in EXCLUDE_DIRS for part in path.parts)


def walk_python_files() -> List[Path]:
    files: List[Path] = []
    for base in INCLUDE_DIRS:
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            if not should_skip(path):
                files.append(path)
    return sorted(files)


def safe_read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def get_module_docstring(tree: ast.AST) -> Optional[str]:
    return ast.get_docstring(tree)


def get_imports(tree: ast.AST) -> List[str]:
    imports: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            names = ", ".join(alias.name for alias in node.names)
            prefix = "." * node.level
            imports.append(f"{prefix}{module}: {names}")
    return sorted(set(imports))


def get_top_level_functions(tree: ast.Module) -> List[Dict[str, Any]]:
    funcs: List[Dict[str, Any]] = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            funcs.append({
                "name": node.name,
                "args": [arg.arg for arg in node.args.args],
                "doc": ast.get_docstring(node),
            })
        elif isinstance(node, ast.AsyncFunctionDef):
            funcs.append({
                "name": node.name,
                "args": [arg.arg for arg in node.args.args],
                "doc": ast.get_docstring(node),
            })
    return funcs


def get_class_methods(node: ast.ClassDef) -> List[Dict[str, Any]]:
    methods: List[Dict[str, Any]] = []
    for item in node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            methods.append({
                "name": item.name,
                "args": [arg.arg for arg in item.args.args],
                "doc": ast.get_docstring(item),
            })
    return methods


def get_classes(tree: ast.Module) -> List[Dict[str, Any]]:
    classes: List[Dict[str, Any]] = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            bases = []
            for base in node.bases:
                if isinstance(base, ast.Name):
                    bases.append(base.id)
                elif isinstance(base, ast.Attribute):
                    bases.append(base.attr)
                else:
                    bases.append(ast.unparse(base) if hasattr(ast, "unparse") else "unknown")
            classes.append({
                "name": node.name,
                "bases": bases,
                "doc": ast.get_docstring(node),
                "methods": get_class_methods(node),
            })
    return classes


def infer_role(path: Path, imports: List[str], classes: List[Dict[str, Any]], funcs: List[Dict[str, Any]]) -> str:
    name = path.name.lower()

    if "router" in name:
        return "API/router layer"
    if "service" in name:
        return "service/orchestration layer"
    if "processor" in name:
        return "workflow engine / pipeline execution layer"
    if "handler" in name:
        return "document-type-specific extraction handler"
    if "schema" in name:
        return "schema / response contract layer"
    if "utils" in name:
        return "shared utility/helper layer"
    if any(cls["name"].endswith("Handler") for cls in classes):
        return "document handler"
    if any("APIRouter" in imp for imp in imports):
        return "FastAPI router"
    return "module"


def infer_pipeline_connections(path: Path, imports: List[str]) -> List[str]:
    connections: List[str] = []
    import_text = " | ".join(imports).lower()

    mapping = {
        "classification_service": "classification stage",
        "extraction_service": "extraction stage",
        "document_processing_service": "service orchestration",
        "processors": "workflow engine",
        "base_handler": "handler base contract",
        "utils": "shared extraction utilities",
        "service_schema": "response/schema contract",
        "fastapi": "API layer",
    }

    for key, value in mapping.items():
        if key in import_text:
            connections.append(value)

    return sorted(set(connections))


def summarize_file(path: Path) -> Dict[str, Any]:
    source = safe_read(path)
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return {
            "path": path,
            "error": f"SyntaxError: {e}",
        }

    imports = get_imports(tree)
    classes = get_classes(tree)
    funcs = get_top_level_functions(tree)
    module_doc = get_module_docstring(tree)
    role = infer_role(path, imports, classes, funcs)
    connections = infer_pipeline_connections(path, imports)

    return {
        "path": path,
        "module_doc": module_doc,
        "imports": imports,
        "classes": classes,
        "functions": funcs,
        "role": role,
        "connections": connections,
    }


def short_doc(text: Optional[str]) -> str:
    if not text:
        return "-"
    line = text.strip().splitlines()[0].strip()
    return line if line else "-"


def render_method(method: Dict[str, Any]) -> str:
    args = ", ".join(method["args"])
    doc = short_doc(method["doc"])
    return f"- `{method['name']}({args})` — {doc}"


def render_function(fn: Dict[str, Any]) -> str:
    args = ", ".join(fn["args"])
    doc = short_doc(fn["doc"])
    return f"- `{fn['name']}({args})` — {doc}"


def render_current_source_of_truth(items: List[Dict[str, Any]]) -> List[str]:
    lines: List[str] = []
    lines.append("# Current Source of Truth")
    lines.append("")
    
    expected_files = {
        "classification_service.py": "document classification logic",
        "document_processing_router.py": "main API router for document processing",
        "document_processing_service.py": "orchestrates classification + extraction pipeline",
        "extraction_service.py": "dispatches to document-specific handlers",
        "processors.py": "main workflow engine for classify/extract/full_process",
        "utils.py": "shared extraction utilities and helpers",
        "service_schema.py": "response contract and data models",
        "base_handler.py": "base contract for all document handlers",
        "generic_extractor.py": "common/shared field extractor used before handler-specific extraction",
    }
    
    for item in items:
        rel_path = item["path"].relative_to(ROOT).as_posix()
        filename = item["path"].name
        
        if filename in expected_files:
            role = expected_files[filename]
            lines.append(f"- `{rel_path}` — {role}")
        elif "handlers/" in rel_path and filename.endswith("_handler.py"):
            handler_type = filename.replace("_handler.py", "")
            lines.append(f"- `{rel_path}` — {handler_type} document handler")
    
    lines.append("")
    return lines


def render_live_pipeline(items: List[Dict[str, Any]]) -> List[str]:
    lines: List[str] = []
    lines.append("# Live Pipeline")
    lines.append("")
    lines.append("Main production workflow:")
    lines.append("")
    lines.append("document_processing_router.py")
    lines.append("→ document_processing_service.py")
    lines.append("→ processors.py")
    lines.append("→ classification_service.py")
    lines.append("→ extraction_service.py")
    lines.append("→ generic_extractor.py + handlers/*")
    lines.append("→ service_schema.py output")
    lines.append("")
    
    has_extraction_router = any(item["path"].name == "extraction_router.py" for item in items)
    if has_extraction_router:
        lines.append("Separate testing workflow:")
        lines.append("- extraction_router.py — internal/testing extraction router, not main production workflow")
        lines.append("")
    
    return lines


def render_locked_files(items: List[Dict[str, Any]]) -> List[str]:
    lines: List[str] = []
    lines.append("# Locked / Rebuilt Files")
    lines.append("")
    
    for item in items:
        rel_path = item["path"].relative_to(ROOT).as_posix()
        source = safe_read(item["path"])
        
        # STRICT: Only lock if meets criteria AND not excluded
        is_locked = False
        reasons = []
        
        # Check exclusions first
        if "/schema/" in rel_path:
            continue  # Skip all schema/ files
        
        if "BaseDocumentHandler" in source:
            continue  # Skip files using old BaseDocumentHandler
        
        # Check inclusion criteria
        if "BaseHandler" in source and "build_result" in source:
            is_locked = True
            reasons.append("uses BaseHandler, build_result")
        elif "safe_set_field" in source:
            is_locked = True
            reasons.append("uses safe_set_field")
        else:
            # Check if core pipeline file (expanded to include router)
            filename = item["path"].name
            if filename in ["processors.py", "document_processing_service.py", "classification_service.py", "extraction_service.py", "service_schema.py", "document_processing_router.py", "generic_extractor.py", "base_handler.py", "utils.py"]:
                is_locked = True
                reasons.append("core pipeline file")
        
        if is_locked:
            lines.append(f"- `{rel_path}` — {', '.join(reasons)}")
    lines.append("")
    return lines


def render_legacy_files(items: List[Dict[str, Any]]) -> List[str]:
    lines: List[str] = []
    lines.append("# Legacy / Stale / Review Carefully")
    lines.append("")
    
    for item in items:
        rel_path = item["path"].relative_to(ROOT).as_posix()
        source = safe_read(item["path"])
        
        # EXCLUSIONS - skip these entirely
        if "service_schema.py" in rel_path:
            continue  # NEVER mark service_schema.py as legacy
        
        if "BaseHandler" in source:
            continue  # Files using BaseHandler are current, not legacy
        
        # HARD SEPARATION: All /schema/ files are legacy
        if "/schema/" in rel_path:
            lines.append(f"- `{rel_path}` — old enum/model-based extraction schema")
            continue
        
        # Check for legacy patterns
        reasons = []
        legacy_patterns = [
            ("DocumentType", "old DocumentType enum"),
            ("ExtractedField", "old ExtractedField model"),
            ("ExtractionResult", "old ExtractionResult model"),
            ("FieldConfidence", "old FieldConfidence model"),
            ("BaseDocumentHandler", "old BaseDocumentHandler class"),
        ]
        
        for pattern, reason in legacy_patterns:
            if pattern in source:
                reasons.append(reason)
        
        # Special handling for handlers/__init__.py
        if "handlers/__init__.py" in rel_path:
            if "BaseDocumentHandler" in source:
                lines.append(f"- `{rel_path}` — uses old BaseDocumentHandler import, needs cleanup to BaseHandler")
                continue
        
        # If any legacy patterns found, mark as legacy
        if reasons:
            lines.append(f"- `{rel_path}` — {', '.join(reasons)}")
    
    lines.append("")
    return lines


def render_auxiliary_files(items: List[Dict[str, Any]]) -> List[str]:
    lines: List[str] = []
    lines.append("# Auxiliary / Not in Main Live Path")
    lines.append("")
    
    # Collect files that are already classified
    source_of_truth_files = set()
    locked_files = set()
    legacy_files = set()
    
    # Build sets of already classified files
    for item in items:
        rel_path = item["path"].relative_to(ROOT).as_posix()
        filename = item["path"].name
        source = safe_read(item["path"])
        
        # Current Source of Truth
        if filename in ["classification_service.py", "document_processing_router.py", "document_processing_service.py", 
                       "extraction_service.py", "processors.py", "utils.py", "service_schema.py", 
                       "base_handler.py", "generic_extractor.py"] or ("handlers/" in rel_path and filename.endswith("_handler.py")):
            source_of_truth_files.add(rel_path)
        
        # Locked Files
        is_locked = False
        if "/schema/" not in rel_path and "BaseDocumentHandler" not in source:
            if ("BaseHandler" in source and "build_result" in source) or "safe_set_field" in source:
                is_locked = True
            elif filename in ["processors.py", "document_processing_service.py", "classification_service.py", 
                            "extraction_service.py", "service_schema.py", "document_processing_router.py"]:
                is_locked = True
        
        if is_locked:
            locked_files.add(rel_path)
        
        # Legacy Files
        is_legacy = False
        if "service_schema.py" not in rel_path and "BaseHandler" not in source:
            if "/schema/" in rel_path:
                is_legacy = True
            elif any(pattern in source for pattern in ["DocumentType", "ExtractedField", "ExtractionResult", "FieldConfidence", "BaseDocumentHandler"]):
                is_legacy = True
        
        if is_legacy:
            legacy_files.add(rel_path)
    
    # Find auxiliary files (not in any of the above categories)
    for item in items:
        rel_path = item["path"].relative_to(ROOT).as_posix()
        filename = item["path"].name
        
        if rel_path not in source_of_truth_files and rel_path not in locked_files and rel_path not in legacy_files:
            # Determine reason
            if "decision" in filename.lower():
                reason = "auxiliary decision/recommendation logic, not part of main rebuilt live pipeline"
            else:
                reason = "present in module inventory but not currently marked as source-of-truth or legacy"
            
            lines.append(f"- `{rel_path}` — {reason}")
    
    lines.append("")
    return lines


def render_next_work_items(items: List[Dict[str, Any]]) -> List[str]:
    lines: List[str] = []
    lines.append("# Next Work Items")
    lines.append("")
    
    # Expected handler files
    expected_handlers = [
        "scheme_application_handler.py",
        "farmer_record_handler.py",
        "grievance_handler.py",
        "insurance_claim_handler.py",
        "subsidy_claim_handler.py",
        "supporting_document_handler.py",
    ]
    
    # Find existing handlers
    existing_handlers = {}
    legacy_handlers = set()
    
    for item in items:
        rel_path = item["path"].relative_to(ROOT).as_posix()
        filename = item["path"].name
        
        if filename.endswith("_handler.py"):
            existing_handlers[filename] = item
            
            # Check if handler appears legacy
            source = safe_read(item["path"])
            if "BaseDocumentHandler" in source or "DocumentType" in source:
                legacy_handlers.add(filename)
    
    # List missing handlers
    for handler in expected_handlers:
        if handler not in existing_handlers:
            lines.append(f"- create {handler}")
        elif handler in legacy_handlers:
            lines.append(f"- rebuild/review {handler} (appears legacy)")
    
    # If all major handlers exist, suggest next integration work
    if all(handler in existing_handlers for handler in expected_handlers[:4]):  # Check first 4 main handlers
        lines.append("- end-to-end testing with OCR text samples")
        lines.append("- validate extraction_service handler dispatch")
        lines.append("- verify processors.py output shape against frontend/backend usage")
    
    lines.append("")
    return lines


def render_handler_contract() -> List[str]:
    lines: List[str] = []
    lines.append("# Handler Contract")
    lines.append("")
    lines.append("All document handlers must follow this standard:")
    lines.append("")
    lines.append("- All document handlers inherit from `BaseHandler`")
    lines.append("- All handlers should return only through `build_result(...)`")
    lines.append("- All field writes should use `safe_set_field(...)`")
    lines.append("- Standard handler output shape:")
    lines.append("  - document_type")
    lines.append("  - structured_data")
    lines.append("  - extracted_fields")
    lines.append("  - missing_fields")
    lines.append("  - confidence")
    lines.append("  - reasoning")
    lines.append("")
    lines.append("Preferred extraction philosophy:")
    lines.append("- labeled regex primary")
    lines.append("- boundary-aware optional")
    lines.append("- keyword fallback where helpful")
    lines.append("- no fake/sample data")
    lines.append("- no one-template logic")
    lines.append("")
    return lines


def render_handler_field_contract() -> List[str]:
    lines: List[str] = []
    lines.append("# Handler Field Contract (Strict)")
    lines.append("")
    lines.append("--------------------------------------------------")
    lines.append("scheme_application")
    lines.append("--------------------------------------------------")
    lines.append("REQUIRED:")
    lines.append("- farmer_name")
    lines.append("- scheme_name")
    lines.append("")
    lines.append("OPTIONAL:")
    lines.append("- aadhaar_number")
    lines.append("- location")
    lines.append("- village")
    lines.append("- district")
    lines.append("- land_size")
    lines.append("- requested_amount")
    lines.append("- crop_type")
    lines.append("- season")
    lines.append("- phone_number")
    lines.append("- application_id")
    lines.append("")
    lines.append("--------------------------------------------------")
    lines.append("farmer_record")
    lines.append("--------------------------------------------------")
    lines.append("REQUIRED:")
    lines.append("- farmer_id")
    lines.append("- farmer_name")
    lines.append("")
    lines.append("OPTIONAL:")
    lines.append("- land_holding")
    lines.append("- land_size")
    lines.append("- location")
    lines.append("- crops")
    lines.append("- village")
    lines.append("- district")
    lines.append("- benefit_history")
    lines.append("- aadhaar_number")
    lines.append("- phone_number")
    lines.append("- email")
    lines.append("- bank_details")
    lines.append("- registration_date")
    lines.append("")
    lines.append("--------------------------------------------------")
    lines.append("grievance")
    lines.append("--------------------------------------------------")
    lines.append("REQUIRED:")
    lines.append("- complaint_subject")
    lines.append("")
    lines.append("OPTIONAL:")
    lines.append("- applicant_name")
    lines.append("- grievance_text")
    lines.append("- department")
    lines.append("- urgency")
    lines.append("- location")
    lines.append("- contact_number")
    lines.append("- aadhaar_number")
    lines.append("- reference_number")
    lines.append("- submission_date")
    lines.append("- expected_resolution")
    lines.append("")
    lines.append("--------------------------------------------------")
    lines.append("insurance_claim")
    lines.append("--------------------------------------------------")
    lines.append("REQUIRED:")
    lines.append("- farmer_name")
    lines.append("- policy_number")
    lines.append("- claim_amount")
    lines.append("")
    lines.append("OPTIONAL:")
    lines.append("- aadhaar_number")
    lines.append("- location")
    lines.append("- village")
    lines.append("- district")
    lines.append("- crop_type")
    lines.append("- season")
    lines.append("- incident_date")
    lines.append("- claim_reason")
    lines.append("- insurer_name")
    lines.append("- contact_number")
    lines.append("- application_id")
    lines.append("")
    lines.append("--------------------------------------------------")
    lines.append("subsidy_claim")
    lines.append("--------------------------------------------------")
    lines.append("REQUIRED:")
    lines.append("- farmer_name")
    lines.append("- subsidy_type")
    lines.append("- requested_amount")
    lines.append("")
    lines.append("OPTIONAL:")
    lines.append("- aadhaar_number")
    lines.append("- location")
    lines.append("- village")
    lines.append("- district")
    lines.append("- land_size")
    lines.append("- crop_type")
    lines.append("- season")
    lines.append("- department")
    lines.append("- subsidy_reason")
    lines.append("- contact_number")
    lines.append("- application_id")
    lines.append("- submission_date")
    lines.append("")
    lines.append("--------------------------------------------------")
    lines.append("supporting_document")
    lines.append("--------------------------------------------------")
    lines.append("REQUIRED:")
    lines.append("- document_reference")
    lines.append("")
    lines.append("OPTIONAL:")
    lines.append("- farmer_name")
    lines.append("- aadhaar_number")
    lines.append("- location")
    lines.append("- document_type_detail")
    lines.append("- issuing_authority")
    lines.append("- issue_date")
    lines.append("- contact_number")
    lines.append("- application_id")
    lines.append("")
    lines.append("❗ RULES:")
    lines.append("- DO NOT rename required fields")
    lines.append("- DO NOT replace required fields with similar-looking fields")
    lines.append("- DO NOT introduce new primary fields unless explicitly requested")
    lines.append("- DO NOT copy field contracts from other handlers")
    lines.append("- If a handler example conflicts with this section, this section wins")
    lines.append("")
    return lines


def render_reasoning_contract() -> List[str]:
    lines: List[str] = []
    lines.append("# Reasoning Contract (Locked Style)")
    lines.append("")
    lines.append("Handlers MUST use summary-style reasoning only.")
    lines.append("")
    lines.append("Allowed reasoning patterns:")
    lines.append("- Missing required fields: ...")
    lines.append("- Fields extracted: ...")
    lines.append("- Core fields identified successfully")
    lines.append("")
    lines.append("Reasoning must be:")
    lines.append("- minimal")
    lines.append("- summary-only")
    lines.append("- consistent across all handlers")
    lines.append("")
    lines.append("NOT ALLOWED:")
    lines.append("- per-field logs")
    lines.append("- extraction-step narration")
    lines.append("- regex explanations")
    lines.append("- verbose debugging text")
    lines.append("- one reasoning line per extracted field")
    lines.append("")
    lines.append("If a future handler prompt suggests per-field reasoning, ignore that and follow this section.")
    lines.append("")
    return lines


def render_anti_drift_rules() -> List[str]:
    lines: List[str] = []
    lines.append("# Anti-Drift Rules")
    lines.append("")
    lines.append("When generating or editing handlers:")
    lines.append("")
    lines.append("- DO NOT mix document domains")
    lines.append("  - insurance_claim ≠ subsidy_claim ≠ scheme_application ≠ grievance")
    lines.append("")
    lines.append("- DO NOT reuse primary fields from another handler unless they are explicitly part of the field contract")
    lines.append("")
    lines.append("Examples of forbidden drift:")
    lines.append("- using scheme_name as the required field in subsidy_claim")
    lines.append("- using claim_amount instead of requested_amount in subsidy_claim")
    lines.append("- using grievance_type instead of complaint_subject in grievance")
    lines.append("- using policy_number in scheme_application")
    lines.append("")
    lines.append("Priority order when generating handlers:")
    lines.append("1. Handler Field Contract (Strict)")
    lines.append("2. BaseHandler contract")
    lines.append("3. Locked handler coding style")
    lines.append("4. Existing handler examples")
    lines.append("")
    lines.append("If any example conflicts with the strict field contract:")
    lines.append("- ignore the example")
    lines.append("- follow the strict field contract")
    lines.append("")
    lines.append("Future chats should treat this section as binding guidance, not optional commentary.")
    lines.append("")
    return lines


def render_summary(items: List[Dict[str, Any]]) -> str:
    lines: List[str] = []
    lines.append("# Document Processing Code Context")
    lines.append("")
    lines.append("Auto-generated developer context for workflow, pipeline, and file responsibilities.")
    lines.append("")
    
    lines.extend(render_current_source_of_truth(items))
    lines.extend(render_live_pipeline(items))
    lines.extend(render_locked_files(items))
    lines.extend(render_legacy_files(items))
    lines.extend(render_auxiliary_files(items))
    lines.extend(render_next_work_items(items))
    lines.extend(render_handler_contract())
    lines.extend(render_handler_field_contract())
    lines.extend(render_reasoning_contract())
    lines.extend(render_anti_drift_rules())
    lines.append("")
    
    lines.append("---")
    lines.append("")

    for item in items:
        rel_path = item["path"].relative_to(ROOT).as_posix()
        lines.append(f"## `{rel_path}`")
        lines.append("")
        if "error" in item:
            lines.append(f"**Parse error:** {item['error']}")
            lines.append("")
            continue

        lines.append(f"**Role:** {item['role']}")
        lines.append("")
        purpose = short_doc(item['module_doc'])
        if purpose == "-":
            # Fallback: try to get purpose from class docstring or role
            if item['classes']:
                purpose = short_doc(item['classes'][0]['doc'])
            elif item['functions']:
                purpose = short_doc(item['functions'][0]['doc'])
            else:
                purpose = item['role']
        
        lines.append(f"**Purpose:** {purpose}")
        lines.append("")

        if item["connections"]:
            lines.append("**Likely pipeline connections:**")
            for conn in item["connections"]:
                lines.append(f"- {conn}")
            lines.append("")

        if item["imports"]:
            lines.append("**Imports:**")
            for imp in item["imports"][:25]:
                lines.append(f"- `{imp}`")
            if len(item["imports"]) > 25:
                lines.append(f"- ... ({len(item['imports']) - 25} more)")
            lines.append("")

        if item["classes"]:
            lines.append("**Classes:**")
            for cls in item["classes"]:
                bases = ", ".join(cls["bases"]) if cls["bases"] else "-"
                lines.append(f"- `{cls['name']}` (bases: {bases}) — {short_doc(cls['doc'])}")
                if cls["methods"]:
                    for method in cls["methods"]:
                        lines.append(f"  {render_method(method)}")
            lines.append("")

        if item["functions"]:
            lines.append("**Top-level functions:**")
            for fn in item["functions"]:
                lines.append(render_function(fn))
            lines.append("")

    return "\n".join(lines)


def main() -> None:
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    files = walk_python_files()
    items = [summarize_file(path) for path in files]
    content = render_summary(items)
    OUTPUT_FILE.write_text(content, encoding="utf-8")
    print(f"Generated: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()