import requests
import os

# Test file to upload
test_file = 'test.txt'

# Create a test file if it doesn't exist
if not os.path.exists(test_file):
    with open(test_file, 'w') as f:
        f.write('This is a test document with a citation: Smith v. Jones, 123 F.3d 456 (9th Cir. 2020)')

# URL of the API endpoint
url = 'http://localhost:5000/casestrainer/api/analyze-document'

# Send a POST request with the test file
with open(test_file, 'rb') as f:
    files = {'file': (test_file, f, 'text/plain')}
    response = requests.post(url, files=files)

# Print the response
print(f'Status code: {response.status_code}')
print('Response:')
print(response.json())
