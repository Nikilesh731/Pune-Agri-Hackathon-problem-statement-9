import requests
import hashlib
import time
import random
import string

def generate_unique_content():
    random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    timestamp = int(time.time())
    return f'Test content {random_str} at {timestamp}'

# Create test file
content = generate_unique_content()
file_content = content.encode('utf-8')
file_hash = hashlib.sha256(file_content).hexdigest()
print(f'File hash: {file_hash[:16]}...')

# First upload
files = {'file': ('subsidy_claim.pdf', file_content, 'application/pdf')}
data = {'applicantId': 'test-farmer-002', 'documentType': 'subsidy_claim'}
response = requests.post('http://localhost:3001/api/applications/with-file', files=files, data=data)
print(f'1. First upload: {response.status_code}')
if response.status_code == 201:
    app_id = response.json()['application']['id']
    print(f'   Application ID: {app_id}')
    
    # Wait for AI processing to complete
    time.sleep(3)
    
    # Use the correct approve endpoint
    approve_response = requests.patch(f'http://localhost:3001/api/applications/{app_id}/approve')
    print(f'   Status update (approve endpoint): {approve_response.status_code}')
    
    # Check the actual status
    check_response = requests.get(f'http://localhost:3001/api/applications/{app_id}')
    if check_response.status_code == 200:
        actual_status = check_response.json()['status']
        print(f'   Actual status after approval: {actual_status}')
    
    # Second upload
    response2 = requests.post('http://localhost:3001/api/applications/with-file', files=files, data=data)
    print(f'2. Second upload: {response2.status_code}')
    if response2.status_code == 201:
        print('   ✅ Re-upload allowed!')
        result = response2.json()
        print(f'   New app ID: {result.get("application", {}).get("id")}')
        print(f'   Is re-upload: {result.get("isReupload", False)}')
    else:
        print('   ❌ Re-upload blocked:', response2.json().get('message'))
else:
    print('   First upload failed:', response.json())
