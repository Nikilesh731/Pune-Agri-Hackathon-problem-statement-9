#!/usr/bin/env python3
"""Check single application details"""

import requests

def check_application():
    app_id = 'a11cd7a4-c11e-4195-9d20-13e60d0df381'
    response = requests.get(f'http://localhost:3001/api/applications/{app_id}')
    app = response.json()

    print('Application Details:')
    print(f'Status: {app.get("status")}')
    print(f'AI Processing Status: {app.get("aiProcessingStatus")}')
    print(f'Has Extracted Data: {"Yes" if app.get("extractedData") else "No"}')

    extracted_data = app.get('extractedData', {})
    if extracted_data:
        print(f'Document Type: {extracted_data.get("document_type")}')
        print(f'Summary: {extracted_data.get("summary")}')
        print(f'Case Insight: {extracted_data.get("case_insight")}')
        print(f'Decision Support: {extracted_data.get("decision_support")}')
    else:
        print('No extracted data found')

if __name__ == "__main__":
    check_application()
