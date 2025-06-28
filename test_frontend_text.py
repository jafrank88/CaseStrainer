#!/usr/bin/env python3
"""
Test script to check if the frontend text triggers the immediate processing path.
"""

def test_immediate_processing_logic():
    """Test the immediate processing logic from the /analyze endpoint."""
    
    print("=== TESTING IMMEDIATE PROCESSING LOGIC ===")
    
    # Test citations from the frontend results
    test_citations = [
        "97 Wn.2d 30",
        "185 Wn.2d 363", 
        "199 Wn. App. 280",
        "640 P.2d 716",
        "399 P.3d 1195"
    ]
    
    # Patterns from the endpoint
    patterns = ['U.S.', 'F.', 'F.2D', 'F.3D', 'S.CT.', 'L.ED.', 'L.ED.2D', 'L.ED.3D', 'P.2D', 'P.3D', 'A.2D', 'A.3D', 'WL', 'WN.2D', 'WN.APP.', 'WN. APP.', 'WASH.2D', 'WASH.APP.', 'WASH. APP.']
    
    for citation in test_citations:
        text_trimmed = citation.strip()
        text_upper = text_trimmed.upper()
        
        # Check the immediate processing conditions
        condition1 = len(text_trimmed) < 50
        condition2 = any(char.isdigit() for char in text_trimmed)
        condition3 = any(word in text_upper for word in patterns)
        condition4 = len(text_trimmed.split()) <= 10
        
        immediate = condition1 and condition2 and condition3 and condition4
        
        print(f"\nCitation: '{citation}'")
        print(f"  Upper case: '{text_upper}'")
        print(f"  Length < 50: {condition1} ({len(text_trimmed)})")
        print(f"  Contains digits: {condition2}")
        print(f"  Contains patterns: {condition3}")
        
        # Show which patterns match
        matching_patterns = [word for word in patterns if word in text_upper]
        if matching_patterns:
            print(f"    Matching patterns: {matching_patterns}")
        else:
            print(f"    No matching patterns")
            # Show what patterns are in the text
            text_words = text_upper.split()
            print(f"    Words in text: {text_words}")
        
        print(f"  Words <= 10: {condition4} ({len(text_trimmed.split())})")
        print(f"  Immediate processing: {immediate}")
        
        if not immediate:
            print(f"  ❌ Will use async processing")
        else:
            print(f"  ✅ Will use immediate processing")

if __name__ == "__main__":
    test_immediate_processing_logic() 