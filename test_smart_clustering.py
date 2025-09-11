#!/usr/bin/env python3
"""
Test smart clustering approach: proximity-based grouping + metadata propagation.
"""

import sys
import os
import re

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from standalone_citation_parser import CitationParser

def detect_parallel_citations_by_proximity(text: str, citations: list, proximity_threshold: int = 100):
    """
    Phase 1: Group citations by proximity in text.
    This catches parallel citations regardless of reporter type.
    """
    print(f"🔍 Phase 1: Detecting parallel citations by proximity (threshold: {proximity_threshold} chars)")
    
    # Find positions of all citations
    citation_positions = []
    for citation in citations:
        pos = text.find(citation)
        if pos != -1:
            citation_positions.append((citation, pos))
    
    # Sort by position
    citation_positions.sort(key=lambda x: x[1])
    
    # Group by proximity
    groups = []
    current_group = []
    
    for i, (citation, pos) in enumerate(citation_positions):
        if not current_group:
            current_group = [(citation, pos)]
        else:
            # Check if this citation is close to the last one in current group
            last_pos = current_group[-1][1]
            if pos - last_pos <= proximity_threshold:
                current_group.append((citation, pos))
            else:
                # Start new group
                if len(current_group) > 1:  # Only keep groups with multiple citations
                    groups.append(current_group)
                current_group = [(citation, pos)]
    
    # Don't forget the last group
    if len(current_group) > 1:
        groups.append(current_group)
    
    print(f"Found {len(groups)} parallel citation groups:")
    for i, group in enumerate(groups):
        citations_in_group = [c[0] for c in group]
        print(f"  Group {i+1}: {citations_in_group}")
    
    return groups

def extract_and_propagate_metadata(text: str, groups: list):
    """
    Phase 2: Extract case name from first citation, year from last citation,
    then propagate to all citations in the group.
    """
    print(f"\n🔧 Phase 2: Extracting and propagating metadata")
    
    parser = CitationParser()
    enhanced_citations = []
    
    for group in groups:
        citations_in_group = [c[0] for c in group]
        print(f"\n--- Processing group: {citations_in_group} ---")
        
        # Extract case name from FIRST citation
        first_citation = citations_in_group[0]
        first_result = parser.extract_from_text(text, first_citation)
        case_name = first_result.get('case_name')
        print(f"  First citation '{first_citation}' -> case name: {case_name}")
        
        # Extract year from LAST citation  
        last_citation = citations_in_group[-1]
        last_result = parser.extract_from_text(text, last_citation)
        year = last_result.get('year')
        print(f"  Last citation '{last_citation}' -> year: {year}")
        
        # Propagate to all citations in this group
        for citation in citations_in_group:
            enhanced_citation = {
                'citation': citation,
                'extracted_case_name': case_name,
                'extracted_date': year,
                'confidence_score': 0.8 if case_name and year else 0.4,
                'extraction_method': 'proximity_propagation',
                'parallel_group': citations_in_group
            }
            enhanced_citations.append(enhanced_citation)
            print(f"  Enhanced '{citation}' -> case: {case_name}, year: {year}")
    
    return enhanced_citations

def cluster_by_propagated_data(enhanced_citations: list):
    """
    Phase 3: Re-cluster citations using the propagated case names and years.
    """
    print(f"\n🎯 Phase 3: Clustering by propagated metadata")
    
    # Group by (case_name, year)
    clusters = {}
    for citation in enhanced_citations:
        case_name = citation.get('extracted_case_name')
        year = citation.get('extracted_date')
        
        if case_name and year:
            key = (case_name, year)
            if key not in clusters:
                clusters[key] = []
            clusters[key].append(citation)
    
    # Convert to final format
    final_clusters = []
    for (case_name, year), citations in clusters.items():
        cluster = {
            'cluster_id': f"{case_name.replace(' ', '_')}_{year}",
            'case_name': case_name,
            'year': year,
            'size': len(citations),
            'citations': [c['citation'] for c in citations],
            'citation_objects': citations,
            'cluster_type': 'proximity_propagation'
        }
        final_clusters.append(cluster)
        print(f"  Cluster: {case_name} ({year}) - {len(citations)} citations")
    
    return final_clusters

def test_smart_clustering():
    """Test the complete smart clustering approach."""
    print("🧪 Testing Smart Clustering: Proximity + Propagation")
    
    # Test text with parallel citations
    test_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)"""
    
    # All citations found by our enhanced extraction
    all_citations = [
        '200 Wn.2d 72',
        '514 P.3d 643',  # Parallel to 200 Wn.2d 72
        '171 Wn.2d 486', 
        '256 P.3d 321',  # Parallel to 171 Wn.2d 486
        '146 Wn.2d 1',
        '43 P.3d 4'      # Parallel to 146 Wn.2d 1
    ]
    
    print(f"Test text: {test_text[:100]}...")
    print(f"Citations found: {all_citations}")
    print()
    
    # Phase 1: Detect parallel citations by proximity
    groups = detect_parallel_citations_by_proximity(test_text, all_citations)
    
    # Phase 2: Extract and propagate metadata
    enhanced_citations = extract_and_propagate_metadata(test_text, groups)
    
    # Phase 3: Cluster by propagated data
    final_clusters = cluster_by_propagated_data(enhanced_citations)
    
    print(f"\n🎉 Final Results:")
    print(f"  Expected: 3 clusters with 2 citations each")
    print(f"  Actual: {len(final_clusters)} clusters")
    
    for i, cluster in enumerate(final_clusters):
        print(f"  Cluster {i+1}: {cluster['case_name']} ({cluster['year']}) - {cluster['size']} citations")
        for citation in cluster['citations']:
            print(f"    - {citation}")
    
    print("\n✅ Smart clustering test completed!")

if __name__ == "__main__":
    test_smart_clustering()
