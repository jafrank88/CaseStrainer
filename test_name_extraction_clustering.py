#!/usr/bin/env python3
"""
Test name extraction and clustering to identify why names are missing.
"""

import requests
import json

def test_name_extraction_and_clustering():
    """Test name extraction and clustering with detailed analysis."""
    
    # Test document with clear case names
    test_text = """
    Legal Document for Name Extraction Testing
    
    Important cases with clear names:
    1. State v. Johnson, 160 Wn.2d 500, 158 P.3d 677 (2007) - This case established precedent
    2. City of Seattle v. Williams, 170 Wn.2d 200, 240 P.3d 1055 (2010) - Important ruling
    3. Brown v. State of Washington, 180 Wn.2d 300, 320 P.3d 800 (2014) - Recent decision
    4. Miller v. Jones, 190 Wn.2d 400, 350 P.3d 900 (2015) - Landmark case
    5. Davis v. County of King, 200 Wn.2d 500, 400 P.3d 1000 (2018) - Current law
    
    These cases show clear patterns and should have extractable case names.
    The clustering should group parallel citations together.
    """
    
    print("🧪 Testing Name Extraction and Clustering")
    print("=" * 60)
    print(f"📄 Document size: {len(test_text)} characters")
    print()
    
    # Submit for processing
    print("📤 Submitting test document...")
    try:
        response = requests.post(
            "http://localhost:8080/casestrainer/api/analyze",
            json={"text": test_text},
            timeout=30
        )
        
        print(f"  Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"  ❌ Failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
            
        data = response.json()
        
        # Analyze the response
        citations = data.get('citations', [])
        clusters = data.get('clusters', [])
        processing_mode = data.get('metadata', {}).get('processing_mode', 'unknown')
        
        print(f"  ✅ Processing completed")
        print(f"  Processing mode: {processing_mode}")
        print(f"  Citations found: {len(citations)}")
        print(f"  Clusters found: {len(clusters)}")
        print()
        
        # Detailed citation analysis
        print("📋 Citation Analysis:")
        print("-" * 40)
        
        if len(citations) == 0:
            print("  ❌ No citations found!")
            return False
        
        for i, citation in enumerate(citations[:10], 1):  # Limit to first 10
            print(f"  Citation {i}:")
            print(f"    Text: {citation.get('citation', 'N/A')}")
            print(f"    Extracted Name: {citation.get('extracted_case_name', 'N/A')}")
            print(f"    Canonical Name: {citation.get('canonical_name', 'N/A')}")
            print(f"    Extracted Date: {citation.get('extracted_date', 'N/A')}")
            print(f"    Canonical Date: {citation.get('canonical_date', 'N/A')}")
            print(f"    Verified: {citation.get('verified', False)}")
            print(f"    Method: {citation.get('method', 'N/A')}")
            print(f"    Confidence: {citation.get('confidence', 0.0)}")
            print()
        
        # Check for missing names
        citations_with_extracted_names = [c for c in citations if c.get('extracted_case_name')]
        citations_with_canonical_names = [c for c in citations if c.get('canonical_name')]
        
        print("📊 Name Extraction Summary:")
        print(f"  Total citations: {len(citations)}")
        print(f"  With extracted names: {len(citations_with_extracted_names)} ({len(citations_with_extracted_names)/len(citations)*100:.1f}%)")
        print(f"  With canonical names: {len(citations_with_canonical_names)} ({len(citations_with_canonical_names)/len(citations)*100:.1f}%)")
        print()
        
        # Detailed cluster analysis
        print("🔗 Cluster Analysis:")
        print("-" * 40)
        
        if len(clusters) == 0:
            print("  ⚠️ No clusters found")
        else:
            for i, cluster in enumerate(clusters, 1):
                print(f"  Cluster {i}:")
                print(f"    Citations in cluster: {len(cluster.get('citations', []))}")
                print(f"    Cluster type: {cluster.get('type', 'N/A')}")
                print(f"    Representative citation: {cluster.get('representative_citation', 'N/A')}")
                
                # Check names in cluster citations
                cluster_citations = cluster.get('citations', [])
                cluster_extracted_names = [c.get('extracted_case_name') for c in cluster_citations if c.get('extracted_case_name')]
                cluster_canonical_names = [c.get('canonical_name') for c in cluster_citations if c.get('canonical_name')]
                
                print(f"    Extracted names in cluster: {cluster_extracted_names}")
                print(f"    Canonical names in cluster: {cluster_canonical_names}")
                print()
        
        # Overall assessment
        print("🎯 Assessment:")
        if len(citations_with_extracted_names) == 0:
            print("  ❌ CRITICAL: No extracted case names found!")
            print("     This suggests name extraction is not working")
        elif len(citations_with_extracted_names) < len(citations) * 0.5:
            print("  ⚠️ WARNING: Low extracted name rate")
            print("     Name extraction may have issues")
        else:
            print("  ✅ Extracted names look good")
        
        if len(citations_with_canonical_names) == 0:
            print("  ⚠️ No canonical names found")
            print("     This is expected if verification is disabled or failing")
        else:
            print("  ✅ Some canonical names found")
        
        if len(clusters) == 0:
            print("  ⚠️ No clusters found")
            print("     This suggests clustering is not working or no parallel citations")
        else:
            print("  ✅ Clustering is working")
        
        return len(citations_with_extracted_names) > 0
        
    except Exception as e:
        print(f"  💥 Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_direct_processor():
    """Test the processor directly to see if it's an API issue."""
    
    print("\n🔧 Testing Direct Processor")
    print("=" * 60)
    
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
        
        from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
        import asyncio
        
        test_text = """
        State v. Johnson, 160 Wn.2d 500, 158 P.3d 677 (2007) was a landmark case.
        City of Seattle v. Williams, 170 Wn.2d 200, 240 P.3d 1055 (2010) followed this precedent.
        """
        
        print("📄 Testing with direct processor...")
        processor = UnifiedCitationProcessorV2()
        result = asyncio.run(processor.process_text(test_text))
        
        citations = result.get('citations', [])
        print(f"  Citations found: {len(citations)}")
        
        for i, citation in enumerate(citations, 1):
            if hasattr(citation, '__dict__'):
                citation_dict = citation.__dict__
            else:
                citation_dict = citation
                
            print(f"  Citation {i}:")
            print(f"    Text: {citation_dict.get('citation', 'N/A')}")
            print(f"    Extracted Name: {citation_dict.get('extracted_case_name', 'N/A')}")
            print(f"    Canonical Name: {citation_dict.get('canonical_name', 'N/A')}")
            print()
        
        extracted_names = [c.__dict__.get('extracted_case_name') if hasattr(c, '__dict__') else c.get('extracted_case_name') for c in citations]
        extracted_names = [name for name in extracted_names if name]
        
        print(f"  Extracted names: {extracted_names}")
        
        if len(extracted_names) > 0:
            print("  ✅ Direct processor extracts names correctly")
            return True
        else:
            print("  ❌ Direct processor also missing names")
            return False
            
    except Exception as e:
        print(f"  💥 Direct processor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run name extraction and clustering tests."""
    
    print("🚀 Name Extraction and Clustering Investigation")
    print("=" * 60)
    
    # Test via API
    api_success = test_name_extraction_and_clustering()
    
    # Test direct processor
    direct_success = test_direct_processor()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 INVESTIGATION SUMMARY")
    print("=" * 60)
    
    print(f"API Processing: {'✅ PASS' if api_success else '❌ FAIL'}")
    print(f"Direct Processing: {'✅ PASS' if direct_success else '❌ FAIL'}")
    
    if not api_success and not direct_success:
        print("\n❌ ISSUE: Name extraction is broken in the core processor")
    elif not api_success and direct_success:
        print("\n⚠️ ISSUE: Name extraction works directly but fails via API")
    elif api_success:
        print("\n✅ Name extraction is working correctly")
    
    return api_success or direct_success

if __name__ == "__main__":
    main()
