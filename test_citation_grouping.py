#!/usr/bin/env python3
"""
Test script to verify citation grouping and state-reporter mapping functionality.
"""

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2, CitationResult

def test_citation_grouping():
    """Test the citation grouping functionality."""
    
    processor = UnifiedCitationProcessorV2()
    
    # Test citations from different states and reporters
    test_citations = [
        CitationResult(citation="146 Wash.2d 1"),
        CitationResult(citation="146 Wn.2d 1"),
        CitationResult(citation="43 P.3d 4"),
        CitationResult(citation="200 Cal.3d 123"),
        CitationResult(citation="150 P.3d 456"),
        CitationResult(citation="100 N.W.2d 789"),
        CitationResult(citation="75 S.W.3d 321"),
    ]
    
    print("Testing citation grouping functionality:")
    print("=" * 50)
    
    # Test state inference
    print("\n1. State Inference:")
    for citation in test_citations:
        state = processor._infer_state_from_citation(citation.citation)
        print(f"  {citation.citation} -> {state}")
    
    # Test reporter inference
    print("\n2. Reporter Inference:")
    for citation in test_citations:
        reporter = processor._infer_reporter_from_citation(citation.citation)
        print(f"  {citation.citation} -> {reporter}")
    
    # Test citation grouping
    print("\n3. Citation Grouping:")
    groups = processor._group_citations_for_verification(test_citations)
    for group_key, group_citations in groups.items():
        print(f"\n  Group: {group_key}")
        for citation in group_citations:
            print(f"    - {citation.citation}")
    
    # Test state-reporter mapping
    print("\n4. State-Reporter Mapping:")
    test_reporters = ['P.3d', 'N.W.2d', 'S.W.3d']
    for reporter in test_reporters:
        states = processor._get_possible_states_for_reporter(reporter)
        print(f"  {reporter}: {', '.join(states[:5])}{'...' if len(states) > 5 else ''}")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    test_citation_grouping() 