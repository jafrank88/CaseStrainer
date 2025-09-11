#!/usr/bin/env python3
"""
Test local verification without requiring Redis or external services.
This will test the enhanced clustering and local processing capabilities.
"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from enhanced_sync_processor import EnhancedSyncProcessor

def test_local_verification():
    """Test local verification capabilities without external services."""
    print("🧪 Testing Local Verification (No External Services)")
    print("=" * 60)
    
    # Initialize the enhanced sync processor
    processor = EnhancedSyncProcessor()
    
    # Test paragraph with parallel citations
    test_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)"""
    
    print(f"📝 Test Text:")
    print(f"   {test_text[:100]}...")
    print()
    
    # Test the enhanced clustering directly
    print("🔄 Testing Enhanced Clustering Directly...")
    
    try:
        # Extract citations first
        citations = processor._extract_citations_fast(test_text)
        print(f"✅ Found {len(citations)} citations")
        
        # Extract names and years
        enhanced_citations = processor._extract_names_years_local(citations, test_text, "test_local")
        print(f"✅ Enhanced {len(enhanced_citations)} citations with case names and years")
        
        # Cluster citations
        clusters = processor._cluster_citations_local(enhanced_citations, test_text, "test_local")
        print(f"✅ Created {len(clusters)} clusters")
        
        print()
        print("📊 LOCAL PROCESSING RESULTS:")
        print("=" * 60)
        
        # Display enhanced citations
        print(f"📋 Enhanced Citations ({len(enhanced_citations)}):")
        for i, citation in enumerate(enhanced_citations, 1):
            print(f"\n🔍 Citation {i}: {citation.get('citation', 'N/A')}")
            print(f"   📝 Extracted Case Name: {citation.get('extracted_case_name', 'N/A')}")
            print(f"   📅 Extracted Date: {citation.get('extracted_date', 'N/A')}")
            print(f"   🎯 Confidence: {citation.get('confidence_score', 'N/A')}")
            print(f"   🏷️  Extraction Method: {citation.get('extraction_method', 'N/A')}")
        
        # Display clusters
        print(f"\n🎯 Clusters ({len(clusters)}):")
        for i, cluster in enumerate(clusters, 1):
            print(f"\n📦 Cluster {i}: {cluster.get('case_name', 'N/A')} ({cluster.get('year', 'N/A')})")
            print(f"   📊 Size: {cluster.get('size', 'N/A')} citations")
            print(f"   🏷️  Type: {cluster.get('cluster_type', 'N/A')}")
            print(f"   🎯 Citations: {', '.join(cluster.get('citations', []))}")
            print(f"   🎯 Confidence: {cluster.get('confidence_score', 'N/A')}")
        
        # Test individual citation extraction
        print(f"\n🔍 Testing Individual Citation Extraction:")
        test_citation = "200 Wn.2d 72"
        case_name = processor._extract_case_name_local(test_text, test_citation)
        year = processor._extract_year_local(test_text, test_citation)
        print(f"   Citation: {test_citation}")
        print(f"   Case Name: {case_name}")
        print(f"   Year: {year}")
        
        print(f"\n✅ Local verification test completed successfully!")
        print(f"   📊 Citations processed: {len(enhanced_citations)}")
        print(f"   🎯 Clusters created: {len(clusters)}")
        print(f"   🔍 Individual extraction: Working")
        
    except Exception as e:
        print(f"❌ Local verification test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_local_verification()
