#!/usr/bin/env python3
"""
Minimal test to debug the quote function issue.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_quote_function():
    """Test the quote function directly."""
    print("🧪 Testing Quote Function")
    print("=" * 40)
    
    try:
        # Test 1: Import and check quote function
        from urllib.parse import quote
        print(f"✅ Imported quote from: {quote.__module__}")
        print(f"✅ Quote function name: {quote.__name__}")
        
        # Test 2: Test with simple string
        test_string = "200 Wn.2d 72"
        result = quote(test_string)
        print(f"✅ quote('{test_string}') = '{result}'")
        
        # Test 3: Test with query-like string
        test_query = '"200 Wn.2d 72" court decision'
        result = quote(test_query)
        print(f"✅ quote('{test_query}') = '{result}'")
        
        # Test 4: Test with site-specific query
        test_site_query = 'site:caselaw.findlaw.com/court/wa-supreme-court "200 Wn.2d 72"'
        result = quote(test_site_query)
        print(f"✅ quote('{test_site_query}') = '{result}'")
        
        print("\n🎉 All quote tests passed!")
        
    except Exception as e:
        print(f"❌ Quote test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_quote_function()
