"""
Investigate how to properly distinguish parallel citations from series citations
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

from eyecite import get_citations

# Test cases
test_cases = [
    ("Parallel citations (same case)", "Smith v. Jones, 123 F.3d 456, 456 F. Supp. 2d 789 (9th Cir. 2020)."),
    ("Series citations (different cases)", "Smith v. Jones, 123 F.3d 456; Doe v. Roe, 789 F.2d 123 (9th Cir. 2020)."),
    ("Mixed case", "See Smith v. Jones, 123 F.3d 456, 456 F. Supp. 2d 789; Doe v. Roe, 987 F.3d 456 (2020).")
]

print("DISTINGUISHING PARALLEL vs SERIES CITATIONS")
print("=" * 80)

for desc, text in test_cases:
    print(f"\n{desc}:")
    print("-" * 60)
    print(f"Text: {text}")
    
    citations = get_citations(text)
    
    print(f"\nFound {len(citations)} citations:")
    
    for i, cit in enumerate(citations):
        print(f"\n{i+1}. {cit}")
        
        # Check metadata for clues
        if hasattr(cit, 'metadata'):
            metadata = cit.metadata
            plaintiff = getattr(metadata, 'plaintiff', None)
            defendant = getattr(metadata, 'defendant', None)
            extra = getattr(metadata, 'extra', None)
            
            print(f"   Plaintiff: {plaintiff}")
            print(f"   Defendant: {defendant}")
            print(f"   Extra: {extra}")
            
            # Check if this is a parallel citation
            if extra and ('F.' in extra or 'U.S.' in extra or 'S. Ct.' in extra):
                print(f"   *** LIKELY PARALLEL CITATION (extra contains other reporter) ***")
    
    # Analyze relationships
    print(f"\nAnalysis:")
    if len(citations) > 1:
        # Check if they have same parties
        first = citations[0]
        if hasattr(first, 'metadata'):
            first_plaintiff = getattr(first.metadata, 'plaintiff', None)
            first_defendant = getattr(first.metadata, 'defendant', None)
            
            all_same = True
            for cit in citations[1:]:
                if hasattr(cit, 'metadata'):
                    cit_plaintiff = getattr(cit.metadata, 'plaintiff', None)
                    cit_defendant = getattr(cit.metadata, 'defendant', None)
                    
                    if cit_plaintiff != first_plaintiff or cit_defendant != first_defendant:
                        all_same = False
                        break
            
            if all_same and first_plaintiff:
                print("   → All citations have same parties: LIKELY PARALLEL CITATIONS")
            else:
                print("   → Citations have different parties: LIKELY SERIES CITATIONS")
    
    print("\n" + "=" * 80)

print("\nRECOMMENDATION:")
print("-" * 60)
print("To distinguish parallel from series citations:")
print("1. Check if citations have the same plaintiff and defendant")
print("2. If same parties → Parallel citation (same case)")
print("3. If different parties → Series citation (different cases)")
print("4. Also check for semicolons which often separate different cases")
