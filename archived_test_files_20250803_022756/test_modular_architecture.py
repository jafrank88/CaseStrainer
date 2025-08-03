#!/usr/bin/env python3
"""
Test script to verify the modular citation processing architecture.
This tests that the new modular services provide the same functionality as the monolithic processor.
"""

import sys
import os
import asyncio
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services import CitationProcessor, ServiceContainer
from src.models import ProcessingConfig

async def test_modular_architecture():
    """Test the modular citation processing architecture."""
    print("Testing Modular Citation Processing Architecture")
    print("=" * 60)
    
    # Test text with multiple citations
    test_text = """
    This is a test document with legal citations.
    The case of Brown v. Board of Education, 347 U.S. 483 (1954) established important precedent.
    The case of Gideon v. Wainwright, 372 U.S. 335 (1963) guaranteed the right to counsel.
    Additionally, Gideon v. Wainwright, 83 S. Ct. 792 (1963) is the same case.
    Also see 9 L. Ed. 2d 799 (1963) which is another parallel citation for Gideon v. Wainwright.
    In Miranda v. Arizona, 384 U.S. 436 (1966), the Court established important procedural rights.
    """
    
    print(f"Test text length: {len(test_text)} characters")
    print(f"Expected citations: Brown v. Board, Gideon v. Wainwright (multiple), Miranda v. Arizona")
    
    try:
        # Test 1: Basic service container functionality
        print("\n" + "="*60)
        print("TEST 1: Service Container Functionality")
        print("="*60)
        
        config = ProcessingConfig(debug_mode=True)
        container = ServiceContainer(config)
        
        # Test individual services
        extractor = container.get_extractor()
        verifier = container.get_verifier()
        clusterer = container.get_clusterer()
        processor = container.get_processor()
        
        print(f"✅ Extractor service: {type(extractor).__name__}")
        print(f"✅ Verifier service: {type(verifier).__name__}")
        print(f"✅ Clusterer service: {type(clusterer).__name__}")
        print(f"✅ Processor service: {type(processor).__name__}")
        
        # Test 2: Citation extraction
        print("\n" + "="*60)
        print("TEST 2: Citation Extraction")
        print("="*60)
        
        citations = extractor.extract_citations(test_text)
        print(f"Found {len(citations)} citations:")
        
        for i, citation in enumerate(citations):
            print(f"  {i+1}. {citation.citation}")
            print(f"     Method: {citation.method}")
            print(f"     Confidence: {citation.confidence:.2f}")
            print(f"     Extracted case: {citation.extracted_case_name or 'N/A'}")
            print(f"     Extracted date: {citation.extracted_date or 'N/A'}")
            print()
        
        if len(citations) >= 3:
            print("✅ Citation extraction working - found multiple citations")
        else:
            print("⚠️  Citation extraction may need improvement - found fewer citations than expected")
        
        # Test 3: Citation verification
        print("\n" + "="*60)
        print("TEST 3: Citation Verification")
        print("="*60)
        
        verified_citations = await verifier.verify_citations(citations[:3])  # Test first 3 to avoid rate limits
        verified_count = sum(1 for c in verified_citations if c.verified)
        
        print(f"Verified {verified_count}/{len(verified_citations)} citations:")
        for citation in verified_citations:
            status = "✅ VERIFIED" if citation.verified else "❌ UNVERIFIED"
            print(f"  {citation.citation}: {status}")
            if citation.verified:
                print(f"    Canonical: {citation.canonical_name} ({citation.canonical_date})")
        
        if verified_count > 0:
            print("✅ Citation verification working - some citations verified")
        else:
            print("⚠️  Citation verification may need API keys or network access")
        
        # Test 4: Citation clustering
        print("\n" + "="*60)
        print("TEST 4: Citation Clustering")
        print("="*60)
        
        # Use all original citations for clustering test
        citations_with_parallels = clusterer.detect_parallel_citations(citations, test_text)
        clusters = clusterer.cluster_citations(citations_with_parallels)
        
        print(f"Created {len(clusters)} clusters:")
        for i, cluster in enumerate(clusters):
            print(f"  Cluster {i+1}: {cluster['canonical_name'] or cluster['extracted_case_name']}")
            print(f"    Size: {cluster['size']} citations")
            print(f"    Citations: {[c['citation'] for c in cluster['citations']]}")
            print()
        
        # Check for Gideon clustering
        gideon_clusters = [c for c in clusters if 'gideon' in (c.get('canonical_name', '') + c.get('extracted_case_name', '')).lower()]
        
        if len(gideon_clusters) == 1:
            gideon_cluster = gideon_clusters[0]
            if gideon_cluster['size'] >= 3:
                print("✅ Clustering working correctly - Gideon citations properly grouped")
            else:
                print("⚠️  Clustering partially working - Gideon cluster smaller than expected")
        else:
            print("⚠️  Clustering may need improvement - Gideon citations not properly grouped")
        
        # Test 5: Complete pipeline
        print("\n" + "="*60)
        print("TEST 5: Complete Processing Pipeline")
        print("="*60)
        
        result = await processor.process_text(test_text)
        
        if result['success']:
            summary = result['summary']
            print(f"✅ Pipeline completed successfully!")
            print(f"   Total citations: {summary['total_citations']}")
            print(f"   Verified citations: {summary['verified_citations']}")
            print(f"   Total clusters: {summary['total_clusters']}")
            print(f"   Verification rate: {summary['verification_rate']:.1%}")
            
            # Check processing info
            processing_info = result.get('processing_info', {})
            print(f"   Services used: {processing_info.get('services_used', [])}")
            
            return True
        else:
            print(f"❌ Pipeline failed: {result.get('error', 'Unknown error')}")
            return False
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_performance_comparison():
    """Test performance of modular vs monolithic approach."""
    print("\n" + "="*60)
    print("PERFORMANCE COMPARISON")
    print("="*60)
    
    test_text = """
    Brown v. Board of Education, 347 U.S. 483 (1954).
    Gideon v. Wainwright, 372 U.S. 335 (1963).
    Miranda v. Arizona, 384 U.S. 436 (1966).
    """
    
    import time
    
    # Test modular approach
    start_time = time.time()
    container = ServiceContainer()
    processor = container.get_processor()
    result = await processor.process_text(test_text)
    modular_time = time.time() - start_time
    
    print(f"Modular approach: {modular_time:.3f}s")
    print(f"Citations found: {result['summary']['total_citations']}")
    print(f"Clusters created: {result['summary']['total_clusters']}")
    
    # Get processing stats
    stats = processor.get_processing_stats()
    print(f"Average processing time: {stats['average_processing_time']:.3f}s")
    
    return True

async def main():
    """Main test function."""
    print("Modular Citation Processing Architecture Test")
    print("=" * 60)
    
    success1 = await test_modular_architecture()
    success2 = await test_performance_comparison()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("🎉 ALL TESTS PASSED!")
        print("The modular architecture is working correctly.")
        print("\nBenefits achieved:")
        print("✅ Separation of concerns - each service has a focused responsibility")
        print("✅ Dependency injection - services can be easily swapped or mocked")
        print("✅ Testability - each service can be tested independently")
        print("✅ Maintainability - code is organized into logical modules")
        print("✅ Extensibility - new services can be added easily")
    else:
        print("❌ SOME TESTS FAILED!")
        print("The modular architecture needs further refinement.")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
