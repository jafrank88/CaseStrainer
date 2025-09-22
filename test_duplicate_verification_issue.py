#!/usr/bin/env python3
"""
Test script to reproduce the duplicate citation verification issue.
User reports: 183 Wash.2d 649 appears as both verified and unverified in different sections.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def test_duplicate_citation_verification():
    """Test if duplicate citations get different verification statuses"""
    
    print("🔍 Testing Duplicate Citation Verification Issue")
    print("=" * 60)
    
    # Create test text with the same citation appearing multiple times
    test_text = """
    Section 1: In Lopez Demetrio v. Sakuma Bros. Farms, 183 Wash.2d 649, the court held...
    
    Section 2: The plaintiff argued that 183 Wash.2d 649 established precedent...
    
    Section 4: As established in Lopez Demetrio v. Sakuma Bros. Farms, 183 Wash.2d 649, the principle...
    """
    
    print(f"📄 Test text length: {len(test_text)} characters")
    print(f"📄 Citation appears 3 times: '183 Wash.2d 649'")
    print()
    
    try:
        from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
        from src.models import ProcessingConfig
        
        # Create processor with verification enabled
        config = ProcessingConfig(
            enable_verification=True,
            enable_clustering=True,
            enable_deduplication=True,
            debug_mode=True
        )
        
        processor = UnifiedCitationProcessorV2(config)
        
        print("🔄 Processing text with UnifiedCitationProcessorV2...")
        import asyncio
        result = asyncio.run(processor.process_text(test_text))
        
        print(f"📊 Results:")
        print(f"   Citations found: {len(result.get('citations', []))}")
        print(f"   Clusters found: {len(result.get('clusters', []))}")
        print()
        
        # Analyze citations for duplicates and verification status
        citations = result.get('citations', [])
        wash_citations = []
        
        for i, citation in enumerate(citations):
            citation_text = citation.get('citation', '')
            if '183 Wash.2d 649' in citation_text:
                wash_citations.append({
                    'index': i,
                    'citation': citation_text,
                    'verified': citation.get('verified', False),
                    'canonical_name': citation.get('canonical_name', 'N/A'),
                    'start_index': citation.get('start_index', 'N/A'),
                    'end_index': citation.get('end_index', 'N/A'),
                    'cluster_id': citation.get('cluster_id', 'N/A')
                })
        
        print(f"🔍 Found {len(wash_citations)} instances of '183 Wash.2d 649':")
        print("-" * 50)
        
        for i, cite in enumerate(wash_citations, 1):
            status = "✅ VERIFIED" if cite['verified'] else "❌ UNVERIFIED"
            print(f"   Instance {i}: {status}")
            print(f"      Citation: {cite['citation']}")
            print(f"      Canonical: {cite['canonical_name']}")
            print(f"      Position: {cite['start_index']}-{cite['end_index']}")
            print(f"      Cluster: {cite['cluster_id']}")
            print()
        
        # Check for verification inconsistency
        verified_statuses = [cite['verified'] for cite in wash_citations]
        if len(set(verified_statuses)) > 1:
            print("🚨 ISSUE CONFIRMED: Same citation has different verification statuses!")
            print(f"   Verified instances: {sum(verified_statuses)}")
            print(f"   Unverified instances: {len(verified_statuses) - sum(verified_statuses)}")
        else:
            print("✅ No verification inconsistency found - all instances have same status")
            
        # Check clustering
        cluster_ids = [cite['cluster_id'] for cite in wash_citations]
        unique_clusters = set(cluster_ids)
        if len(unique_clusters) > 1:
            print(f"🔍 Citations appear in {len(unique_clusters)} different clusters: {unique_clusters}")
        else:
            print(f"✅ All citations in same cluster: {unique_clusters}")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main execution"""
    test_duplicate_citation_verification()

if __name__ == "__main__":
    main()
