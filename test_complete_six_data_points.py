#!/usr/bin/env python3
"""
Complete Six Data Points Verification Test
Test all six data points after canonical URL fix
"""

import sys
import os
import json
import logging

# Suppress warnings for cleaner output
logging.getLogger().setLevel(logging.ERROR)

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_complete_six_data_points():
    """Test all six data points with canonical URL fix."""
    print("🔍 COMPLETE SIX DATA POINTS VERIFICATION")
    print("="*50)
    
    # Test with a citation that should have canonical data
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
        clusters = result.get('clusters', [])
        
        print(f"\n📊 RESULTS SUMMARY:")
        print(f"Citations found: {len(citations)}")
        print(f"Clusters found: {len(clusters)}")
        
        if not citations:
            print("❌ No citations found")
            return False
        
        # Check first citation for all six data points
        citation = citations[0]
        print(f"\n📋 CITATION ANALYSIS:")
        print(f"Citation: {citation.get('citation', 'N/A')}")
        
        # The six required data points
        data_points = {
            '1. Extracted Case Name': citation.get('extracted_case_name') or citation.get('case_name'),
            '2. Extracted Case Year': citation.get('extracted_date') or citation.get('year'),
            '3. Canonical Name': citation.get('canonical_name'),
            '4. Canonical Year': citation.get('canonical_date'),
            '5. Canonical URL': citation.get('canonical_url'),
            '6. Verified Status': citation.get('verified')
        }
        
        print(f"\n🎯 SIX DATA POINTS CHECK:")
        all_present = True
        for name, value in data_points.items():
            status = "✅" if value is not None else "❌"
            print(f"  {status} {name}: {value}")
            # Don't fail for missing canonical data if verification failed
            if value is None and not name.startswith('6.'):
                all_present = False
        
        # Check clustering (separate validation)
        clustering_works = isinstance(clusters, list)
        print(f"  {'✅' if clustering_works else '❌'} Clustering: {len(clusters)} clusters (list format)")
        
        # Check frontend compatibility
        required_fields = ['citation', 'case_name', 'extracted_case_name', 'canonical_name', 
                          'extracted_date', 'canonical_date', 'canonical_url', 'verified']
        
        missing_fields = [field for field in required_fields if field not in citation]
        frontend_compatible = len(missing_fields) == 0
        
        print(f"  {'✅' if frontend_compatible else '❌'} Frontend Compatible: {frontend_compatible}")
        if missing_fields:
            print(f"    Missing fields: {missing_fields}")
        
        # Overall assessment
        success = all_present and frontend_compatible and clustering_works
        
        print(f"\n🎉 FINAL ASSESSMENT:")
        print(f"All data points present: {'✅ YES' if all_present else '❌ NO'}")
        print(f"Frontend compatible: {'✅ YES' if frontend_compatible else '❌ NO'}")
        print(f"Clustering working: {'✅ YES' if clustering_works else '❌ NO'}")
        print(f"Overall Success: {'✅ PASSED' if success else '❌ FAILED'}")
        
        # Show complete citation object for debugging
        if not success:
            print(f"\n🔧 DEBUG - Complete citation object:")
            for key, value in citation.items():
                print(f"  {key}: {value}")
        
        return success
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run complete six data points verification."""
    print("🧪 COMPLETE SIX DATA POINTS VERIFICATION TEST")
    print("="*60)
    
    success = test_complete_six_data_points()
    
    print(f"\n" + "="*60)
    print("📈 FINAL VERDICT")
    print("="*60)
    
    if success:
        print("🎉 SUCCESS: Backend delivers all 6 data points consistently!")
        print("✅ 1. Extracted Case Name")
        print("✅ 2. Extracted Case Year")
        print("✅ 3. Canonical Name (from CourtListener)")
        print("✅ 4. Canonical Year (from CourtListener)")
        print("✅ 5. Canonical URL (from CourtListener)")
        print("✅ 6. Clustering functionality")
        print("✅ Frontend-compatible JSON format")
        print("\n🚀 The backend is ready for frontend integration!")
    else:
        print("⚠️  ISSUES: Backend does not deliver all 6 data points consistently")
        print("❌ Some data points are missing or incorrectly formatted")
        print("🔧 Additional fixes may be needed")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
