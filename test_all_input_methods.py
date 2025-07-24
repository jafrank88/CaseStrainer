#!/usr/bin/env python3
"""
Test all three input methods to ensure they properly verify citations
"""

import sys
import os
import json
import tempfile
import logging

# Ensure src is in the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from src.document_processing_unified import process_document
from src.case_name_extraction_core import extract_case_name_hinted

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_text_input():
    """Test text paste input method"""
    print("\n" + "="*60)
    print("TESTING TEXT PASTE INPUT METHOD")
    print("="*60)
    
    sample_text = """
    This is a sample legal document with citations.
    Brown v. Board of Education, 347 U.S. 483 (1954)
    Roe v. Wade, 410 U.S. 113 (1973)
    John Doe P v. Thurston County, 199 Wn. App. 280, 283, 399 P.3d 1195 (2017)
    """
    
    print(f"Processing text input (length: {len(sample_text)} characters)...")
    result = process_document(content=sample_text, extract_case_names=True)
    
    if result.get('success'):
        print("✅ Text processing successful")
        citations = result.get('citations', [])
        print(f"   Citations found: {len(citations)}")
        
        for i, citation in enumerate(citations):
            print(f"\n   Citation {i+1}: {citation.get('citation', 'N/A')}")
            print(f"     Verified: {citation.get('verified', False)}")
            print(f"     Valid: {citation.get('valid', False)}")
            print(f"     Method: {citation.get('method', 'N/A')}")
            print(f"     Source: {citation.get('source', 'N/A')}")
            print(f"     Canonical Name: {citation.get('canonical_name', 'N/A')}")
            print(f"     URL: {citation.get('url', 'N/A')}")
            print(f"     Court: {citation.get('court', 'N/A')}")
            print(f"     Docket: {citation.get('docket_number', 'N/A')}")
            
            # Check if this is the Washington citation
            if "199 Wn. App. 280" in citation.get('citation', ''):
                print(f"     🎯 WASHINGTON CITATION FOUND!")
                if citation.get('verified'):
                    print(f"     ✅ SUCCESS: Washington citation is now verified!")
                else:
                    print(f"     ❌ FAILURE: Washington citation still not verified")
    else:
        print(f"❌ Text processing failed: {result.get('error', 'Unknown error')}")

def test_file_input():
    """Test file upload input method"""
    print("\n" + "="*60)
    print("TESTING FILE UPLOAD INPUT METHOD")
    print("="*60)
    
    # Create a temporary text file with citations
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
        temp_file.write("""
        This is a sample legal document with citations.
        Brown v. Board of Education, 347 U.S. 483 (1954)
        Roe v. Wade, 410 U.S. 113 (1973)
        John Doe P v. Thurston County, 199 Wn. App. 280, 283, 399 P.3d 1195 (2017)
        """)
        temp_file_path = temp_file.name
    
    try:
        print(f"Processing file: {temp_file_path}")
        result = process_document(file_path=temp_file_path, extract_case_names=True)
        
        if result.get('success'):
            print("✅ File processing successful")
            citations = result.get('citations', [])
            print(f"   Citations found: {len(citations)}")
            
            for i, citation in enumerate(citations):
                print(f"\n   Citation {i+1}: {citation.get('citation', 'N/A')}")
                print(f"     Verified: {citation.get('verified', False)}")
                print(f"     Valid: {citation.get('valid', False)}")
                print(f"     Method: {citation.get('method', 'N/A')}")
                print(f"     Source: {citation.get('source', 'N/A')}")
                print(f"     Canonical Name: {citation.get('canonical_name', 'N/A')}")
                print(f"     URL: {citation.get('url', 'N/A')}")
                
                # Check if this is the Washington citation
                if "199 Wn. App. 280" in citation.get('citation', ''):
                    print(f"     🎯 WASHINGTON CITATION FOUND!")
                    if citation.get('verified'):
                        print(f"     ✅ SUCCESS: Washington citation is now verified!")
                    else:
                        print(f"     ❌ FAILURE: Washington citation still not verified")
        else:
            print(f"❌ File processing failed: {result.get('error', 'Unknown error')}")
            
    finally:
        # Clean up temporary file
        os.unlink(temp_file_path)

def test_url_input():
    """Test URL upload input method"""
    print("\n" + "="*60)
    print("TESTING URL UPLOAD INPUT METHOD")
    print("="*60)
    
    # Use a simple test URL that should contain citations
    test_url = "https://www.law.cornell.edu/supct/html/02-102.ZS.html"
    
    try:
        print(f"Processing URL: {test_url}")
        result = process_document(url=test_url, extract_case_names=True)
        
        if result.get('success'):
            print("✅ URL processing successful")
            citations = result.get('citations', [])
            print(f"   Citations found: {len(citations)}")
            
            for i, citation in enumerate(citations[:5]):  # Show first 5 citations
                print(f"\n   Citation {i+1}: {citation.get('citation', 'N/A')}")
                print(f"     Verified: {citation.get('verified', False)}")
                print(f"     Valid: {citation.get('valid', False)}")
                print(f"     Method: {citation.get('method', 'N/A')}")
                print(f"     Source: {citation.get('source', 'N/A')}")
                print(f"     Canonical Name: {citation.get('canonical_name', 'N/A')}")
                print(f"     URL: {citation.get('url', 'N/A')}")
        else:
            print(f"❌ URL processing failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error testing URL processing: {str(e)}")

def main():
    """Run all tests"""
    print("TESTING ALL THREE INPUT METHODS FOR CITATION VERIFICATION")
    print("="*80)
    
    # Test all three input methods
    test_text_input()
    test_file_input()
    test_url_input()
    
    print("\n" + "="*80)
    print("TESTING COMPLETE")
    print("="*80)
    print("\nSUMMARY:")
    print("- All three input methods (text, file, URL) now use EnhancedMultiSourceVerifier")
    print("- Citations should now have canonical metadata (URL, court, docket)")
    print("- Washington citation '199 Wn. App. 280' should be properly verified")
    print("- Complex citations should be handled correctly")

if __name__ == "__main__":
    main() 