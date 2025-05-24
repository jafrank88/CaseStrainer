#!/usr/bin/env python3
"""
Test script to verify LangSearch API integration.
"""

import os
import sys
from dotenv import load_dotenv
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent / 'src'))

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Loaded environment variables from {env_path}")
else:
    print("⚠️  No .env file found. Using system environment variables.")

def test_langsearch():
    """Test LangSearch API integration."""
    print("\n=== Testing LangSearch Integration ===")
    
    # Check if API key is available
    api_key = os.environ.get('LANGSEARCH_API_KEY')
    if not api_key:
        print("❌ Error: LANGSEARCH_API_KEY not found in environment variables")
        return False
    
    print(f"✅ Found LangSearch API key (first 8 chars): {api_key[:8]}...")
    
    # Import the function to test
    try:
        from langsearch_integration import generate_case_summary_with_langsearch
        print("✅ Successfully imported LangSearch integration")
    except ImportError as e:
        print(f"❌ Error importing LangSearch integration: {e}")
        return False
    
    # Test with a known case citation
    test_citation = "347 U.S. 483"  # Brown v. Board of Education
    print(f"\nTesting with citation: {test_citation}")
    
    try:
        result = generate_case_summary_with_langsearch(test_citation)
        
        print("\n=== Test Results ===")
        print(f"Source: {result.get('source', 'unknown')}")
        print(f"Case Name: {result.get('case_name', 'Not found')}")
        print(f"URL: {result.get('url', 'Not available')}")
        print("\nSummary:")
        print(result.get('summary', 'No summary available'))
        
        if result.get('summary') and 'error' not in result.get('summary', '').lower():
            print("\n✅ LangSearch integration test passed!")
            return True
        else:
            print("\n❌ LangSearch integration test failed - no valid summary returned")
            return False
            
    except Exception as e:
        print(f"\n❌ Error during LangSearch test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_langsearch()
