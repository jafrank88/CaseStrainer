"""
Check how eyecite identifies parallel citations
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

from eyecite import get_citations, resolve_citations

# Test with true parallel citations
parallel_text = "Smith v. Jones, 123 F.3d 456, 456 F. Supp. 2d 789 (9th Cir. 2020)."

print("EYECITE PARALLEL CITATION ANALYSIS")
print("=" * 60)
print(f"Text: {parallel_text}")
print()

# Get raw citations
citations = get_citations(parallel_text)

print(f"Found {len(citations)} citations:")
for i, cit in enumerate(citations):
    print(f"\n{i+1}. {cit}")
    print(f"   Type: {type(cit).__name__}")
    print(f"   Span: {cit.span()}")
    
    # Check if it has metadata
    if hasattr(cit, 'metadata'):
        print(f"   Plaintiff: {getattr(cit.metadata, 'plaintiff', None)}")
        print(f"   Defendant: {getattr(cit.metadata, 'defendant', None)}")
    
    # Check for parallel citation info
    if hasattr(cit, 'parallel_citations'):
        print(f"   Parallel citations: {cit.parallel_citations}")

print("\n" + "=" * 60)
print("RESOLVING CITATIONS:")
print("=" * 60)

# Resolve citations to find matches
resolved = resolve_citations(citations)

print(f"Resolution results:")
for key, value in resolved.items():
    print(f"\n{key}:")
    if isinstance(value, list):
        for v in value:
            print(f"  - {v}")
    else:
        print(f"  {value}")

print("\n" + "=" * 60)
print("TESTING WITH KNOWN PARALLEL CITATION:")
print("=" * 60)

# Test with a clear parallel citation
clear_parallel = "United States v. Nixon, 418 U.S. 683, 94 S. Ct. 2781 (1974)."
print(f"Text: {clear_parallel}")

citations2 = get_citations(clear_parallel)
print(f"\nFound {len(citations2)} citations:")

for i, cit in enumerate(citations2):
    print(f"\n{i+1}. {cit}")
    if hasattr(cit, 'parallel_citations'):
        print(f"   Parallel citations: {cit.parallel_citations}")
    
    # Check if they're marked as parallel
    if hasattr(cit, 'metadata') and cit.metadata:
        print(f"   Full citation: {getattr(cit.metadata, 'full_citation', None)}")

# Check what eyecite considers parallel
print("\n" + "=" * 60)
print("CHECKING EYECITE PARALLEL DETECTION:")
print("=" * 60)

from eyecite.models import FullCaseCitation

for cit in citations2:
    if isinstance(cit, FullCaseCitation):
        print(f"\nCitation: {cit}")
        print(f"  Has parallel_citations: {hasattr(cit, 'parallel_citations')}")
        if hasattr(cit, 'parallel_citations'):
            print(f"  Parallel citations: {cit.parallel_citations}")
        
        # Check if it's a parallel of another
        print(f"  Is parallel: {getattr(cit, 'is_parallel', False)}")
