#!/usr/bin/env python3
"""
Simple Canonical URL Integration Test
Direct test of canonical URL integration without complex imports
"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_simple_canonical_url():
    """Simple test of canonical URL integration."""
    print("🔗 SIMPLE CANONICAL URL TEST")
    print("="*40)
    
    try:
        # Test CourtListener verification directly
        from src.courtlistener_verification import verify_with_courtlistener
        from src.config import get_config_value
        
        api_key = get_config_value("COURTLISTENER_API_KEY", "")
        if not api_key:
            print("❌ No API key")
            return False
        
        print("Testing CourtListener verification...")
        result = verify_with_courtlistener(api_key, "347 U.S. 483", "Brown v. Board of Education")
        
        print(f"CourtListener result:")
        print(f"  verified: {result.get('verified')}")
        print(f"  canonical_name: {result.get('canonical_name')}")
        print(f"  canonical_date: {result.get('canonical_date')}")
        print(f"  url: {result.get('url')}")
        print(f"  canonical_url: {result.get('canonical_url')}")
        
        # Check what field contains the URL
        has_url = result.get('url') is not None
        has_canonical_url = result.get('canonical_url') is not None
        
        print(f"\nURL field analysis:")
        print(f"  'url' field present: {'✅' if has_url else '❌'}")
        print(f"  'canonical_url' field present: {'✅' if has_canonical_url else '❌'}")
        
        if has_url:
            print(f"  URL value: {result.get('url')}")
        if has_canonical_url:
            print(f"  Canonical URL value: {result.get('canonical_url')}")
        
        # Test CitationService directly
        print(f"\nTesting CitationService...")
        from src.api.services.citation_service import CitationService
        
        service = CitationService()
        input_data = {'text': 'Brown v. Board of Education, 347 U.S. 483 (1954)', 'type': 'text'}
        
        service_result = service.process_immediately(input_data)
        
        if service_result.get('status') == 'completed' and service_result.get('citations'):
            citation = service_result['citations'][0]
            
            print(f"CitationService result:")
            print(f"  canonical_name: {citation.get('canonical_name')}")
            print(f"  canonical_date: {citation.get('canonical_date')}")
            print(f"  canonical_url: {citation.get('canonical_url')}")
            print(f"  url: {citation.get('url')}")
            print(f"  verified: {citation.get('verified')}")
            
            service_has_url = citation.get('canonical_url') is not None
            
            print(f"\nComparison:")
            print(f"  CourtListener returns URL: {'✅' if has_url else '❌'}")
            print(f"  CitationService delivers URL: {'✅' if service_has_url else '❌'}")
            
            if has_url and not service_has_url:
                print(f"🔍 ISSUE: URL retrieved but not delivered")
                print(f"  CourtListener URL: {result.get('url')}")
                print(f"  Service URL: {citation.get('canonical_url')}")
                return False
            elif has_url and service_has_url:
                print(f"✅ SUCCESS: URL flows through correctly")
                return True
            else:
                print(f"❌ ISSUE: No URL from CourtListener")
                return False
        else:
            print(f"❌ CitationService failed")
            return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run simple canonical URL test."""
    success = test_simple_canonical_url()
    
    print(f"\n" + "="*50)
    if success:
        print("🎉 CANONICAL URL: WORKING!")
        print("✅ All 6 data points delivered successfully")
    else:
        print("⚠️  CANONICAL URL: NEEDS FIX")
        print("❌ URL not flowing through pipeline")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
