#!/usr/bin/env python3
"""
Debug script to test canonical field propagation from processor to frontend
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig
from src.api.services.citation_service import CitationService

def test_canonical_field_propagation():
    """Test the full pipeline from processor to frontend formatting"""
    
    print("=" * 60)
    print("Testing Canonical Field Propagation")
    print("=" * 60)
    
    # Test text with known Washington citations
    test_text = """
    A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003).
    """
    
    # Step 1: Test the processor directly
    print("\n1. Testing UnifiedCitationProcessorV2 directly:")
    print("-" * 40)
    
    config = ProcessingConfig(
        use_eyecite=False,
        use_regex=True,
        extract_case_names=True,
        extract_dates=True,
        enable_clustering=True,
        enable_deduplication=True,
        enable_verification=True,  # Enable verification to get canonical data
        context_window=300,
        min_confidence=0.0,
        debug_mode=True
    )
    
    processor = UnifiedCitationProcessorV2(config)
    citations = processor.process_text(test_text)
    
    print(f"Found {len(citations)} citations")
    
    for i, citation in enumerate(citations):
        print(f"\nCitation {i+1}:")
        print(f"  Citation text: {citation.citation}")
        print(f"  Extracted case name: {citation.extracted_case_name}")
        print(f"  Extracted date: {citation.extracted_date}")
        print(f"  Canonical name: {citation.canonical_name}")
        print(f"  Canonical date: {citation.canonical_date}")
        print(f"  URL: {citation.url}")
        print(f"  Verified: {citation.verified}")
        print(f"  Source: {citation.source}")
    
    # Step 2: Test the CitationService formatting
    print("\n\n2. Testing CitationService formatting:")
    print("-" * 40)
    
    service = CitationService()
    
    # Convert citations to dict format for service
    citation_dicts = []
    for citation in citations:
        citation_dict = {
            'citation': citation.citation,
            'verified': citation.verified,
            'extracted_case_name': citation.extracted_case_name,
            'extracted_date': citation.extracted_date,
            'canonical_name': citation.canonical_name,
            'canonical_date': citation.canonical_date,
            'court': citation.court,
            'confidence': citation.confidence,
            'source': citation.source,
            'url': citation.url,
            'parallel_citations': citation.parallel_citations,
            'context': citation.context,
            'method': citation.method,
            'error': citation.error
        }
        citation_dicts.append(citation_dict)
    
    # Format for frontend
    formatted_citations = service._format_citations_for_frontend(citation_dicts)
    
    print(f"Formatted {len(formatted_citations)} citations for frontend")
    
    for i, citation in enumerate(formatted_citations):
        print(f"\nFormatted Citation {i+1}:")
        print(f"  Citation text: {citation.get('citation')}")
        print(f"  Case name: {citation.get('case_name')}")
        print(f"  Extracted case name: {citation.get('extracted_case_name')}")
        print(f"  Canonical name: {citation.get('canonical_name')}")
        print(f"  Extracted date: {citation.get('extracted_date')}")
        print(f"  Canonical date: {citation.get('canonical_date')}")
        print(f"  URL: {citation.get('url')}")
        print(f"  Verified: {citation.get('verified')}")
        print(f"  Source: {citation.get('source')}")
    
    # Step 3: Test the full service pipeline
    print("\n\n3. Testing full CitationService pipeline:")
    print("-" * 40)
    
    input_data = {
        'type': 'text',
        'text': test_text
    }
    
    result = service.process_immediately(input_data)
    
    print(f"Service result status: {result.get('status')}")
    print(f"Citations in result: {len(result.get('citations', []))}")
    
    for i, citation in enumerate(result.get('citations', [])):
        print(f"\nService Citation {i+1}:")
        print(f"  Citation text: {citation.get('citation')}")
        print(f"  Case name: {citation.get('case_name')}")
        print(f"  Extracted case name: {citation.get('extracted_case_name')}")
        print(f"  Canonical name: {citation.get('canonical_name')}")
        print(f"  Extracted date: {citation.get('extracted_date')}")
        print(f"  Canonical date: {citation.get('canonical_date')}")
        print(f"  URL: {citation.get('url')}")
        print(f"  Verified: {citation.get('verified')}")
        print(f"  Source: {citation.get('source')}")

if __name__ == "__main__":
    test_canonical_field_propagation() 