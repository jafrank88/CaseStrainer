#!/usr/bin/env python3
"""
Focused Canonical URL Fix Test
Test specifically for canonical URL delivery after fix
"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_canonical_url_fix():
    """Test canonical URL delivery specifically."""
    print("🔗 CANONICAL URL FIX VERIFICATION")
    print("="*40)
    
    # Test with Brown v. Board - should have canonical data
    test_text = "Brown v. Board of Education, 347 U.S. 483 (1954)"
    
    try:
        from src.api.services.citation_service import CitationService
        
        service = CitationService()
        input_data = {'text': test_text, 'type': 'text'}
        
        print(f"Testing: {test_text}")
        result = service.process_immediately(input_data)
        
        if result.get('status') != 'completed':
            print(f"❌ Processing failed: {result.get('message', 'Unknown error')}")
            return False
        
        citations = result.get('citations', [])
        
        if not citations:
            print("❌ No citations found")
            return False
        
        citation = citations[0]
        
        # Check all URL-related fields
        print(f"\n🔗 URL FIELD ANALYSIS:")
        url_fields = {
            'canonical_url': citation.get('canonical_url'),
            'url': citation.get('url'),
            'canonical_name': citation.get('canonical_name'),
            'canonical_date': citation.get('canonical_date'),
            'verified': citation.get('verified')
        }
        
        for field, value in url_fields.items():
            status = "✅" if value is not None else "❌"
            print(f"  {status} {field}: {value}")
        
        # Test CourtListener directly to compare
        print(f"\n🧪 DIRECT COURTLISTENER TEST:")
        try:
            from src.courtlistener_verification import verify_with_courtlistener
            from src.config import get_config_value
            
            api_key = get_config_value("COURTLISTENER_API_KEY", "")
            if api_key:
                direct_result = verify_with_courtlistener(api_key, "347 U.S. 483", "Brown v. Board of Education")
                print(f"  Direct CourtListener result:")
                print(f"    verified: {direct_result.get('verified')}")
                print(f"    canonical_name: {direct_result.get('canonical_name')}")
                print(f"    canonical_date: {direct_result.get('canonical_date')}")
                print(f"    url: {direct_result.get('url')}")
                
                # Compare with service result
                url_match = citation.get('canonical_url') == direct_result.get('url')
                print(f"  URL Match: {'✅' if url_match else '❌'}")
                
                if not url_match:
                    print(f"    Service URL: {citation.get('canonical_url')}")
                    print(f"    Direct URL: {direct_result.get('url')}")
            else:
                print("  ❌ No API key for direct test")
        
        except Exception as e:
            print(f"  ❌ Direct test failed: {e}")
        
        # Success criteria
        has_canonical_url = citation.get('canonical_url') is not None
        has_canonical_data = citation.get('canonical_name') is not None
        is_verified = citation.get('verified') is True
        
        success = has_canonical_url and has_canonical_data and is_verified
        
        print(f"\n🎯 CANONICAL URL FIX ASSESSMENT:")
        print(f"  Has canonical URL: {'✅' if has_canonical_url else '❌'}")
        print(f"  Has canonical data: {'✅' if has_canonical_data else '❌'}")
        print(f"  Is verified: {'✅' if is_verified else '❌'}")
        print(f"  Overall: {'✅ SUCCESS' if success else '❌ FAILED'}")
        
        return success
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run canonical URL fix verification."""
    success = test_canonical_url_fix()
    
    print(f"\n" + "="*50)
    if success:
        print("🎉 CANONICAL URL FIX: SUCCESS!")
        print("✅ Canonical URL is now being delivered to frontend")
        print("✅ All 6 data points should be available")
    else:
        print("⚠️  CANONICAL URL FIX: NEEDS ATTENTION")
        print("❌ Canonical URL is not being delivered properly")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
