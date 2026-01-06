#!/usr/bin/env python3
"""
Debug the containment check
"""

from src.citation_clustering import _is_citation_contained_in_any

def test_containment():
    """Test the containment check function"""
    
    # Test the function
    seen_citations = {"24 Wn. App. 2d 377, 392, 520 P.3d 470"}
    test_citation = "520 P.3d 470"
    
    print(f"Testing containment check:")
    print(f"Seen citations: {seen_citations}")
    print(f"Test citation: {test_citation}")
    print()
    
    result = _is_citation_contained_in_any(test_citation, seen_citations)
    print(f"Result: {result}")
    print()
    
    # Test with the actual logic
    import re
    
    def debug_containment(citation_str: str, existing_citations: set) -> bool:
        norm_citation = citation_str.strip()
        print(f"Normalized citation: '{norm_citation}'")

        for existing in existing_citations:
            norm_existing = existing.strip()
            print(f"\nChecking against: '{norm_existing}'")
            
            # Direct containment check
            if norm_citation in norm_existing and len(norm_existing) > len(norm_citation):
                remaining = norm_existing[len(norm_citation) :].strip()
                print(f"  Direct containment found, remaining: '{remaining}'")
                if remaining and any(c.isdigit() for c in remaining):
                    print(f"  Remaining has digits -> CONTAINED")
                    return True
            
            # Check if citation is a parallel citation within a larger citation
            if ", " in norm_existing and norm_citation.startswith(("P.", "F.")):
                print(f"  Checking parallel citation...")
                parts = norm_existing.split(", ")
                print(f"  Parts: {parts}")
                for part in parts[1:]:  # Skip the first part (main citation)
                    if norm_citation == part.strip():
                        print(f"  Exact match in parts -> CONTAINED")
                        return True
                    # Also check if it's contained within a part (e.g., with year)
                    if norm_citation in part and len(part) > len(norm_citation):
                        print(f"  Partial match in part -> CONTAINED")
                        return True
        
        print("  Not contained")
        return False
    
    print("\nDebug version:")
    result2 = debug_containment(test_citation, seen_citations)
    print(f"\nDebug result: {result2}")

if __name__ == "__main__":
    test_containment()
