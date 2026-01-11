"""
Fix for parallel citation handling in clean_extraction_pipeline.py
"""

import re
import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

def is_parallel_citation(current_citation, previous_citation, text):
    """
    Determine if two citations are parallel citations (same case) or series citations (different cases).
    
    Returns:
        True if parallel citation (same case)
        False if series citation (different case)
    """
    # Check if both citations have metadata
    if not (hasattr(current_citation, 'metadata') and hasattr(previous_citation, 'metadata')):
        return False
    
    current_meta = current_citation.metadata
    prev_meta = previous_citation.metadata
    
    # Get plaintiff and defendant from both citations
    current_plaintiff = getattr(current_meta, 'plaintiff', None)
    current_defendant = getattr(current_meta, 'defendant', None)
    prev_plaintiff = getattr(prev_meta, 'plaintiff', None)
    prev_defendant = getattr(prev_meta, 'defendant', None)
    
    # If both have the same plaintiff and defendant, it's a parallel citation
    if (current_plaintiff and current_defendant and 
        current_plaintiff == prev_plaintiff and 
        current_defendant == prev_defendant):
        return True
    
    # Check for semicolon between citations (indicates different cases)
    if hasattr(current_citation, 'span') and hasattr(previous_citation, 'span'):
        current_start = current_citation.span()[0]
        prev_end = previous_citation.span()[1]
        
        if current_start and prev_end:
            between = text[prev_end:current_start]
            if ';' in between:
                return False
    
    # Check if previous citation's extra field contains the current citation
    # (eyecite puts parallel citations in the 'extra' field)
    if hasattr(prev_meta, 'extra') and prev_meta.extra:
        if current_citation.citation in prev_meta.extra:
            return True
    
    return False

# Test the function
from eyecite import get_citations

test_cases = [
    ("Parallel citations", "Smith v. Jones, 123 F.3d 456, 456 F. Supp. 2d 789 (9th Cir. 2020)."),
    ("Series citations", "Smith v. Jones, 123 F.3d 456; Doe v. Roe, 789 F.2d 123 (9th Cir. 2020)."),
    ("Mixed case", "See Smith v. Jones, 123 F.3d 456, 456 F. Supp. 2d 789; Doe v. Roe, 987 F.3d 456 (2020).")
]

print("TESTING PARALLEL CITATION DETECTION")
print("=" * 60)

for desc, text in test_cases:
    print(f"\n{desc}:")
    print("-" * 40)
    print(f"Text: {text}")
    
    citations = get_citations(text)
    
    if len(citations) > 1:
        for i in range(1, len(citations)):
            current = citations[i]
            previous = citations[i-1]
            
            result = is_parallel_citation(current, previous, text)
            
            print(f"\nCitation {i}: {current}")
            print(f"Previous: {previous}")
            print(f"Result: {'PARALLEL' if result else 'SERIES'}")
            
            # Show the reasoning
            if hasattr(current, 'metadata') and hasattr(previous, 'metadata'):
                print(f"  Current parties: {getattr(current.metadata, 'plaintiff', None)} v. {getattr(current.metadata, 'defendant', None)}")
                print(f"  Previous parties: {getattr(previous.metadata, 'plaintiff', None)} v. {getattr(previous.metadata, 'defendant', None)}")
                
                if hasattr(previous.metadata, 'extra'):
                    print(f"  Previous extra: {getattr(previous.metadata, 'extra', None)}")

print("\n" + "=" * 60)
print("CONCLUSION:")
print("-" * 40)
print("This function can distinguish between parallel and series citations")
print("by checking plaintiff/defendant and eyecite's 'extra' field.")
