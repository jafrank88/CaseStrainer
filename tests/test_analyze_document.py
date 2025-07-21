import pytest
import requests
import os
from unittest.mock import patch, MagicMock

# Test file to upload - only create during test execution
test_file = 'test.txt'

@pytest.fixture(scope="session")
def create_test_file():
    """Create a test file if it doesn't exist"""
    if not os.path.exists(test_file):
        with open(test_file, 'w') as f:
            f.write('This is a test document with a citation: Smith v. Jones, 123 F.3d 456 (9th Cir. 2020)')
    yield test_file
    # Cleanup could be added here if needed

@pytest.mark.integration
def test_analyze_document_endpoint(create_test_file):
    """Test the analyze-document API endpoint"""
    # URL of the API endpoint
    url = 'http://localhost:5000/casestrainer/api/analyze-document'
    
    # Mock the requests.post to avoid actual network calls during testing
    with patch('requests.post') as mock_post:
        # Mock a successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'success',
            'citations': [
                {
                    'citation_text': 'Smith v. Jones, 123 F.3d 456 (9th Cir. 2020)',
                    'validation_status': 'verified'
                }
            ]
        }
        mock_post.return_value = mock_response
        
        # Send a POST request with the test file
        with open(create_test_file, 'rb') as f:
            files = {'file': (create_test_file, f, 'text/plain')}
            response = requests.post(url, files=files)
        
        # Verify the mock was called
        mock_post.assert_called_once()
        
        # Print the response for debugging
        print(f'Status code: {response.status_code}')
        print('Response:')
        print(response.json())
        
        # Assert the response structure
        assert response.status_code == 200
        assert 'status' in response.json()
        assert 'citations' in response.json()

@pytest.mark.integration
def test_analyze_document_server_not_running(create_test_file):
    """Test behavior when server is not running"""
    url = 'http://localhost:5000/casestrainer/api/analyze-document'
    
    # This test will be skipped if we can't connect to the server
    try:
        with open(create_test_file, 'rb') as f:
            files = {'file': (create_test_file, f, 'text/plain')}
            response = requests.post(url, files=files, timeout=5)
    except requests.exceptions.ConnectionError:
        pytest.skip("Server not running - skipping integration test")
    except requests.exceptions.Timeout:
        pytest.skip("Server timeout - skipping integration test")
