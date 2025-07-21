import pytest
import json
import requests
from unittest.mock import patch, MagicMock

# Import the new unified processor instead of deprecated CitationVerifier
from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2


def test_citation():
    """Test citation verification using the unified processor"""
    # Initialize the processor
    processor = UnifiedCitationProcessorV2()
    
    # Test the citation
    citation = "339 U.S. 629"
    
    # Mock the verification to avoid actual API calls during testing
    with patch.object(processor, 'verify_citation_unified_workflow') as mock_verify:
        mock_verify.return_value = {
            'citation': citation,
            'status': 'verified',
            'canonical_name': 'United States v. United Mine Workers',
            'canonical_date': '1947'
        }
        
        result = processor.verify_citation_unified_workflow(citation)
        
        # Print the result
        print("\nVerification Result:")
        print(json.dumps(result, indent=2))
        
        # Assert the result structure
        assert 'citation' in result
        assert 'status' in result
        assert result['citation'] == citation


def test_citation_with_api_key():
    """Test citation verification with API key"""
    import os
    
    api_key = os.environ.get("COURTLISTENER_API_KEY")
    if not api_key:
        pytest.skip("COURTLISTENER_API_KEY environment variable not set")
    
    processor = UnifiedCitationProcessorV2()
    
    # Test the citation
    citation = "339 U.S. 629"
    result = processor.verify_citation_unified_workflow(citation)
    
    # Print the result
    print("\nVerification Result:")
    print(json.dumps(result, indent=2))
    
    # Basic assertions
    assert 'citation' in result
    assert result['citation'] == citation


def test_post_citation():
    """Test posting citation to API endpoint"""
    url = "http://localhost:5000/api/validate_citations"
    data = {"text": "92 U.S. 214"}
    headers = {"Content-Type": "application/json"}
    
    # Mock the requests.post to avoid actual network calls
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'success',
            'citations': [
                {
                    'citation_text': '92 U.S. 214',
                    'validation_status': 'verified'
                }
            ]
        }
        mock_post.return_value = mock_response
        
        response = requests.post(url, json=data, headers=headers)
        
        print(response.status_code)
        print(response.json())
        
        assert response.status_code == 200
        assert 'status' in response.json()


if __name__ == "__main__":
    test_citation()
    test_post_citation()
