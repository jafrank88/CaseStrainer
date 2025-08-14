#!/usr/bin/env python3
"""
Canonical URL Data Flow Trace
Trace the canonical URL through the entire pipeline to find where it gets lost
"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_canonical_url_data_flow():
    """Trace canonical URL through the entire data flow."""
    print("🔍 CANONICAL URL DATA FLOW TRACE")
    print("="*50)
    
    test_text = "Brown v. Board of Education, 347 U.S. 483 (1954)"
    
    try:
        # Step 1: Test CourtListener verification directly
        print("STEP 1: Direct CourtListener Verification")
        print("-" * 40)
        
        from src.courtlistener_verification import verify_with_courtlistener
        from src.config import get_config_value
        
        api_key = get_config_value("COURTLISTENER_API_KEY", "")
        if not api_key:
            print("❌ No API key found")
            return False
        
        direct_result = verify_with_courtlistener(api_key, "347 U.S. 483", "Brown v. Board of Education")
        print(f"Direct verification result:")
        print(f"  verified: {direct_result.get('verified')}")
        print(f"  canonical_name: {direct_result.get('canonical_name')}")
        print(f"  canonical_date: {direct_result.get('canonical_date')}")
        print(f"  url: {direct_result.get('url')}")
        print(f"  canonical_url: {direct_result.get('canonical_url')}")
        
        if not direct_result.get('verified'):
            print("❌ Direct verification failed")
            return False
        
        # Step 2: Test unified citation extraction
        print(f"\nSTEP 2: Unified Citation Extraction")
        print("-" * 40)
        
        from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
        
        processor = UnifiedCitationProcessorV2()
        citations = processor.extract_citations_from_text_enhanced(test_text)
        
        print(f"Extracted {len(citations)} citations")
        if citations:
            citation = citations[0]
            print(f"First citation object attributes:")
            for attr in dir(citation):
                if not attr.startswith('_'):
                    value = getattr(citation, attr, None)
                    if not callable(value):
                        print(f"  {attr}: {value}")
        
        # Step 3: Test unified clustering with verification
        print(f"\nSTEP 3: Unified Clustering with Verification")
        print("-" * 40)
        
        from src.unified_citation_clustering import UnifiedCitationClusterer
        
        clusterer = UnifiedCitationClusterer()
        clustered_result = clusterer.cluster_citations_unified(citations, test_text, verify=True)
        
        print(f"Clustering result keys: {list(clustered_result.keys())}")
        
        if 'citations' in clustered_result:
            clustered_citations = clustered_result['citations']
            print(f"Clustered citations count: {len(clustered_citations)}")
            
            if clustered_citations:
                citation = clustered_citations[0]
                print(f"First clustered citation attributes:")
                for attr in dir(citation):
                    if not attr.startswith('_'):
                        value = getattr(citation, attr, None)
                        if not callable(value):
                            print(f"  {attr}: {value}")
        
        # Step 4: Test CitationService processing
        print(f"\nSTEP 4: CitationService Processing")
        print("-" * 40)
        
        from src.api.services.citation_service import CitationService
        
        service = CitationService()
        input_data = {'text': test_text, 'type': 'text'}
        
        result = service.process_immediately(input_data)
        
        print(f"CitationService result status: {result.get('status')}")
        print(f"CitationService result keys: {list(result.keys())}")
        
        if result.get('citations'):
            citation_dict = result['citations'][0]
            print(f"First citation dictionary:")
            for key, value in citation_dict.items():
                print(f"  {key}: {value}")
        
        # Analysis
        print(f"\n🎯 CANONICAL URL TRACE ANALYSIS")
        print("="*50)
        
        direct_has_url = direct_result.get('url') is not None
        service_has_url = False
        
        if result.get('citations'):
            service_has_url = result['citations'][0].get('canonical_url') is not None
        
        print(f"Direct CourtListener has URL: {'✅' if direct_has_url else '❌'}")
        print(f"CitationService delivers URL: {'✅' if service_has_url else '❌'}")
        
        if direct_has_url and not service_has_url:
            print("🔍 ROOT CAUSE: URL is retrieved but lost in pipeline")
            print("   Need to trace clustering/verification integration")
        elif not direct_has_url:
            print("🔍 ROOT CAUSE: CourtListener API not returning URL")
        else:
            print("✅ SUCCESS: URL flows through pipeline correctly")
        
        return direct_has_url and service_has_url
        
    except Exception as e:
        print(f"❌ Trace failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run canonical URL data flow trace."""
    success = test_canonical_url_data_flow()
    
    print(f"\n" + "="*60)
    print("📊 CANONICAL URL TRACE RESULTS")
    print("="*60)
    
    if success:
        print("🎉 SUCCESS: Canonical URL flows correctly through pipeline")
        print("✅ All 6 data points should be delivered to frontend")
    else:
        print("⚠️  ISSUE: Canonical URL is lost somewhere in the pipeline")
        print("❌ Need to fix data flow integration")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
