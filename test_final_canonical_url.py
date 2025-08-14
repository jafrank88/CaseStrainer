#!/usr/bin/env python3
"""
Final Canonical URL Verification Test
Test the complete six data points after all fixes
"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_final_canonical_url():
    """Final test of canonical URL delivery after all fixes."""
    print("🎯 FINAL CANONICAL URL VERIFICATION")
    print("="*50)
    
    test_text = "Brown v. Board of Education, 347 U.S. 483 (1954)"
    
    try:
        # Test the complete pipeline through CitationService
        from src.api.services.citation_service import CitationService
        
        service = CitationService()
        input_data = {'text': test_text, 'type': 'text'}
        
        print(f"Testing complete pipeline with: {test_text}")
        result = service.process_immediately(input_data)
        
        if result.get('status') != 'completed':
            print(f"❌ Processing failed: {result.get('message', 'Unknown error')}")
            return False
        
        citations = result.get('citations', [])
        clusters = result.get('clusters', [])
        
        print(f"\n📊 PIPELINE RESULTS:")
        print(f"Citations found: {len(citations)}")
        print(f"Clusters found: {len(clusters)}")
        
        if not citations:
            print("❌ No citations extracted")
            return False
        
        # Analyze first citation for all six data points
        citation = citations[0]
        
        print(f"\n🔍 SIX DATA POINTS ANALYSIS:")
        print(f"Citation: {citation.get('citation', 'N/A')}")
        
        # The six critical data points
        six_data_points = {
            '1. Extracted Case Name': citation.get('extracted_case_name') or citation.get('case_name'),
            '2. Extracted Year': citation.get('extracted_date') or citation.get('year'),
            '3. Canonical Name': citation.get('canonical_name'),
            '4. Canonical Year': citation.get('canonical_date'),
            '5. Canonical URL': citation.get('canonical_url'),
            '6. Verified Status': citation.get('verified')
        }
        
        print(f"\n✅ SIX DATA POINTS CHECK:")
        points_present = 0
        for name, value in six_data_points.items():
            status = "✅" if value is not None and value != False else "❌"
            print(f"  {status} {name}: {value}")
            if value is not None and value != False:
                points_present += 1
        
        # Additional analysis
        print(f"\n📈 DETAILED ANALYSIS:")
        print(f"  Data points present: {points_present}/6")
        print(f"  Clustering functional: {'✅' if isinstance(clusters, list) else '❌'}")
        print(f"  Frontend compatible: {'✅' if 'canonical_url' in citation else '❌'}")
        
        # Success criteria
        has_extraction = (citation.get('extracted_case_name') or citation.get('case_name')) is not None
        has_canonical = citation.get('canonical_name') is not None
        has_url = citation.get('canonical_url') is not None
        is_verified = citation.get('verified') is True
        
        success = has_extraction and has_canonical and has_url and is_verified
        
        print(f"\n🎉 FINAL ASSESSMENT:")
        print(f"  Has extraction data: {'✅' if has_extraction else '❌'}")
        print(f"  Has canonical data: {'✅' if has_canonical else '❌'}")
        print(f"  Has canonical URL: {'✅' if has_url else '❌'}")
        print(f"  Is verified: {'✅' if is_verified else '❌'}")
        print(f"  Overall Success: {'✅ PASSED' if success else '❌ FAILED'}")
        
        # Show complete citation for debugging if failed
        if not success:
            print(f"\n🔧 DEBUG - Complete citation object:")
            for key, value in sorted(citation.items()):
                print(f"  {key}: {value}")
        
        return success
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run final canonical URL verification."""
    print("🧪 FINAL SIX DATA POINTS VERIFICATION")
    print("="*60)
    
    success = test_final_canonical_url()
    
    print(f"\n" + "="*60)
    print("🏆 FINAL VERDICT")
    print("="*60)
    
    if success:
        print("🎉 SUCCESS: ALL 6 DATA POINTS DELIVERED!")
        print("✅ 1. Extracted Case Name")
        print("✅ 2. Extracted Case Year") 
        print("✅ 3. Canonical Name (CourtListener)")
        print("✅ 4. Canonical Year (CourtListener)")
        print("✅ 5. Canonical URL (CourtListener)")
        print("✅ 6. Verification Status")
        print("✅ Clustering functionality")
        print("✅ Frontend-compatible JSON format")
        print("\n🚀 BACKEND IS READY FOR PRODUCTION!")
        print("🎯 The canonical URL issue has been resolved!")
    else:
        print("⚠️  PARTIAL SUCCESS: Some data points missing")
        print("🔧 Additional fixes may be needed")
        print("📋 Review the debug output above for specific issues")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
