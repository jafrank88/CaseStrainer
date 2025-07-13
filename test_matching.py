#!/usr/bin/env python3
"""Test citation text matching."""

def normalize_citation_for_matching(citation_text: str) -> str:
    """Normalize citation text for matching by removing common variations."""
    if not citation_text:
        return ""
    
    # Remove extra whitespace and newlines
    normalized = ' '.join(citation_text.split())
    
    # Remove common variations in spacing
    normalized = normalized.replace('  ', ' ')
    
    # Normalize common reporter abbreviations
    normalized = normalized.replace('Wn.2d', 'Wn.2d')
    normalized = normalized.replace('Wn. App.', 'Wn.App.')
    normalized = normalized.replace('P.3d', 'P.3d')
    normalized = normalized.replace('P.2d', 'P.2d')
    
    return normalized.strip()

def test_matching():
    """Test citation text matching."""
    # Test cases from our debug output
    citations = [
        '200 Wn.2d',
        '200 Wn.2d 72', 
        '514 P.3d 643',
        '171 Wn.2d 486',
        '256 P.3d 321',
        '146 Wn.2d',
        '146 Wn.2d 1',
        '43 P.3d 4'
    ]
    
    cluster_citations = [
        '514 P.3d 643',
        '256 P.3d 321', 
        '171 Wn.2d 486',
        '200 Wn.2d 72',
        '200 Wn.2d',
        '43 P.3d 4',
        '146 Wn.2d 1',
        '146 Wn.2d'
    ]
    
    print("Testing citation text matching...")
    print()
    
    # Test exact matches
    print("Exact matches:")
    for citation in citations:
        if citation in cluster_citations:
            print(f"✅ '{citation}' matches exactly")
        else:
            print(f"❌ '{citation}' no exact match")
    print()
    
    # Test normalized matches
    print("Normalized matches:")
    for citation in citations:
        norm_citation = normalize_citation_for_matching(citation)
        found_match = False
        
        for cluster_citation in cluster_citations:
            norm_cluster = normalize_citation_for_matching(cluster_citation)
            if norm_citation == norm_cluster:
                print(f"✅ '{citation}' matches '{cluster_citation}' (normalized)")
                found_match = True
                break
        
        if not found_match:
            print(f"❌ '{citation}' no normalized match")
    print()
    
    # Test the actual matching logic from the code
    print("Testing actual matching logic:")
    citation_to_cluster = {}
    for cluster_citation in cluster_citations:
        normalized_text = ' '.join(cluster_citation.split())
        citation_to_cluster[normalized_text] = {'cluster_id': 'test'}
    
    for citation in citations:
        citation_text = citation
        normalized_citation_text = ' '.join(citation_text.split()) if citation_text else ''
        
        if normalized_citation_text in citation_to_cluster:
            print(f"✅ '{citation}' found in cluster mapping")
        else:
            print(f"❌ '{citation}' NOT found in cluster mapping")
            print(f"   Normalized: '{normalized_citation_text}'")
            print(f"   Available keys: {list(citation_to_cluster.keys())}")

if __name__ == "__main__":
    test_matching() 