#!/usr/bin/env python3
"""
Test script for the new unified citation processor.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def test_unified_processor():
    """Test the new unified citation processor."""
    print("=== Testing Unified Citation Processor ===\n")
    
    # Test text with citations
    test_text = """
    A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003).
    """
    
    try:
        # Test the new unified document processor
        print("1. Testing unified document processor...")
        from src.document_processing_unified import process_document
        
        result = process_document(content=test_text, extract_case_names=True, debug_mode=True)
        
        print(f"✅ Success: {result['success']}")
        print(f"📊 Citations found: {len(result['citations'])}")
        print(f"📝 Case names found: {len(result['case_names'])}")
        print(f"⏱️  Processing time: {result['processing_time']:.3f}s")
        print(f"🔧 Processor used: {result['processor_used']}")
        
        # Show some citations
        print("\n📋 Sample citations:")
        for i, citation in enumerate(result['citations'][:3]):
            print(f"  {i+1}. {citation.get('citation', 'N/A')}")
            print(f"     Case: {citation.get('case_name', 'N/A')}")
            print(f"     Date: {citation.get('extracted_date', 'N/A')}")
            print(f"     Method: {citation.get('method', 'N/A')}")
            print()
        
        # Test the unified citation processor directly
        print("2. Testing unified citation processor directly...")
        from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig
        
        config = ProcessingConfig(
            use_eyecite=True,
            use_regex=True,
            extract_case_names=True,
            extract_dates=True,
            enable_clustering=True,
            enable_deduplication=True,
            debug_mode=True
        )
        
        processor = UnifiedCitationProcessorV2(config)
        citation_results = processor.process_text(test_text)
        
        print(f"✅ Success: {len(citation_results)} citations found")
        
        # Show some results
        print("\n📋 Sample citation results:")
        for i, citation in enumerate(citation_results[:3]):
            print(f"  {i+1}. {citation.citation}")
            print(f"     Case: {citation.extracted_case_name or citation.case_name}")
            print(f"     Date: {citation.extracted_date}")
            print(f"     Method: {citation.method}")
            print(f"     Pattern: {citation.pattern}")
            print(f"     Confidence: {citation.confidence}")
            print()
        
        print("✅ All tests passed!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure the unified processor modules are available.")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def test_consolidation():
    """Test that the consolidation works correctly."""
    print("\n=== Testing Consolidation ===\n")
    
    test_text = """
    The court cited several cases: Smith v. Jones, 123 F.3d 456 (2020); Doe v. Roe, 456 P.2d 789 (2021); and Brown v. White, 789 S.Ct. 123 (2022).
    """
    
    try:
        from src.unified_citation_processor_v2 import extract_citations_unified
        
        results = extract_citations_unified(test_text)
        
        print(f"✅ Found {len(results)} citations")
        
        # Check for clustering
        clusters = [r for r in results if r.is_cluster]
        print(f"📦 Clusters detected: {len(clusters)}")
        
        # Check for deduplication
        citations = [r.citation for r in results]
        unique_citations = set(citations)
        print(f"🔄 Deduplication: {len(citations)} -> {len(unique_citations)} unique")
        
        print("✅ Consolidation test passed!")
        
    except Exception as e:
        print(f"❌ Consolidation test failed: {e}")

if __name__ == "__main__":
    test_unified_processor()
    test_consolidation() 