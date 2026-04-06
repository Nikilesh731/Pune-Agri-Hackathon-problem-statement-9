#!/usr/bin/env python3
"""
Local smoke test for the document parsing API.

Usage:
  python scripts/test_document_parse_api.py --file path/to/document.pdf

The script calls:
- GET  /api/document-processing/parse-info
- POST /api/document-processing/parse

It prints the core response fields needed for manual validation.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import httpx


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke test the document parse API")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="FastAPI base URL")
    parser.add_argument("--file", required=True, help="Path to a PDF, image, DOCX, or TXT file")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    file_path = Path(args.file)

    if not file_path.exists():
        print(f"File not found: {file_path}")
        return 1

    parse_info_url = f"{args.base_url.rstrip('/')}/api/document-processing/parse-info"
    parse_url = f"{args.base_url.rstrip('/')}/api/document-processing/parse"

    with httpx.Client(timeout=120.0) as client:
        info_response = client.get(parse_info_url)
        print("parse-info status:", info_response.status_code)
        info_response.raise_for_status()
        info = info_response.json()
        print("service_name:", info.get("service_name"))
        print("docling_available:", info.get("docling_available"))
        print("ocr_available:", info.get("ocr_available"))
        print("supported_formats:", info.get("supported_formats"))
        print("ocr_languages_available:", info.get("ocr_languages_available"))

        with file_path.open("rb") as file_handle:
            files = {"file": (file_path.name, file_handle, "application/octet-stream")}
            parse_response = client.post(parse_url, files=files)

        print("parse status:", parse_response.status_code)
        parse_response.raise_for_status()
        result = parse_response.json()

    raw_text = result.get("raw_text") or ""
    preview = raw_text[:200].replace("\n", " ").strip()

    print("success:", result.get("success"))
    print("parser:", result.get("parser"))
    print("ocr_used:", result.get("ocr_used"))
    print("fallback_used:", result.get("fallback_used"))
    print("text_length:", len(raw_text))
    print("preview:", preview)

    errors = result.get("errors") or []
    if errors:
        print("errors:", errors)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
