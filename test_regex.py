#!/usr/bin/env python3
import re

def test_washington_normalization():
    """Test Washington citation normalization regex patterns."""
    
    test_citations = [
        "115 Wn.2d 294",
        "115 Wn. 2d 294", 
        "115 Wn.3d 456",
        "115 Wn. 3d 456",
        "115 Wn. App. 789",
        "115 Wn. App 789",
        "115 Wn. 123"
    ]
    
    print("=== TESTING WASHINGTON CITATION NORMALIZATION ===")
    
    for citation in test_citations:
        print(f"\nOriginal: '{citation}'")
        
        # Test each regex pattern
        result = citation
        
        # Wn.2d -> Wash. 2d
        pattern1 = r'\bWn\.2d\b'
        result1 = re.sub(pattern1, 'Wash. 2d', result)
        print(f"  Pattern 1 ({pattern1}): {result1}")
        
        # Wn.3d -> Wash. 3d  
        pattern2 = r'\bWn\.3d\b'
        result2 = re.sub(pattern2, 'Wash. 3d', result1)
        print(f"  Pattern 2 ({pattern2}): {result2}")
        
        # Wn. App. -> Wash. App.
        pattern3 = r'\bWn\. App\.\b'
        result3 = re.sub(pattern3, 'Wash. App.', result2)
        print(f"  Pattern 3 ({pattern3}): {result3}")
        
        # Wn. -> Wash. (for any remaining Wn. that aren't part of the above patterns)
        pattern4 = r'\bWn\.\b'
        result4 = re.sub(pattern4, 'Wash.', result3)
        print(f"  Pattern 4 ({pattern4}): {result4}")
        
        print(f"  Final result: '{result4}'")

if __name__ == "__main__":
    test_washington_normalization() 