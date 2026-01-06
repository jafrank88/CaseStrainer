#!/usr/bin/env python3
"""
Test how to properly handle the match groups
"""

def test_citation_creation():
    """Test how to create citations with pinpoint pages"""
    
    # Simulate what the pattern matches
    citation_str = "24 Wn. App. 2d 377, 392, 520 P.3d 470"
    
    # Parse the components
    import re
    pattern = re.compile(
        r"\b(\d+)\s+(?:Wash\.|Wn\.)\s*(?:App\.)\s*2d\s+(\d+)(?:\s*,\s*(\d+))?(?:\s*,\s*(\d+)\s+(?:P\.3d|P\.2d)\s+(\d+))?\s*(?:\(\d{4}\))?\b",
        re.IGNORECASE,
    )
    
    match = pattern.search(citation_str)
    if match:
        volume = match.group(1)
        page = match.group(2)
        pinpoint = match.group(3)  # This would be 392
        parallel_volume = match.group(4)  # This would be 520
        parallel_page = match.group(5)  # This would be 470
        
        print(f"Main citation: {volume} Wn. App. 2d {page}")
        if pinpoint:
            print(f"Pinpoint page: {pinpoint}")
        if parallel_volume and parallel_page:
            print(f"Parallel citation: {parallel_volume} P.3d {parallel_page}")
        
        # Create the citation object structure
        citation_data = {
            "citation": citation_str,
            "volume": volume,
            "reporter": "Wn. App. 2d",
            "page": page,
            "pinpoint_pages": [pinpoint] if pinpoint else [],
            "parallel_citations": [f"{parallel_volume} P.3d {parallel_page}"] if parallel_volume and parallel_page else [],
        }
        
        print("\nCitation data structure:")
        for key, value in citation_data.items():
            print(f"  {key}: {value}")

if __name__ == "__main__":
    test_citation_creation()
