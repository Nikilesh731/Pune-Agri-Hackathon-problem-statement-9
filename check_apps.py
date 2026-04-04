#!/usr/bin/env python3
"""Check applications and their status"""

import requests
import json

def check_applications():
    response = requests.get('http://localhost:3001/api/applications')
    data = response.json()
    
    # Handle different response formats
    apps = data if isinstance(data, list) else data.get('applications', [])
    
    print(f"Found {len(apps)} applications")
    print("=" * 50)
    
    for app in apps:
        print(f'ID: {app["id"]}')
        print(f'Status: {app["status"]}')
        print(f'AI Processing Status: {app.get("aiProcessingStatus", "None")}')
        print(f'Has Extracted Data: {"Yes" if app.get("extractedData") else "No"}')
        print(f'AI Summary: {app.get("aiSummary", "None")}')
        
        extracted_data = app.get("extractedData", {})
        if extracted_data:
            print(f'Document Type: {extracted_data.get("document_type", "Unknown")}')
            print(f'Summary: {extracted_data.get("summary", "No summary")}')
            print(f'Case Insight: {extracted_data.get("case_insight", [])}')
        
        print('---')

if __name__ == "__main__":
    check_applications()
