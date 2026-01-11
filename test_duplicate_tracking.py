"""
Add duplicate citation tracking to help with UI grouping
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

from src.clean_extraction_pipeline import extract_citations_clean

print("TESTING DUPLICATE CITATION TRACKING")
print("=" * 60)

# Test with duplicate citations
text = """Doe v. Teachers Council, Inc., 2024 WL 1232082. Another case. 
Doe v. Teachers Council, Inc., 2024 WL 1232082 appears again."""

print(f"Text: {text}")
print()

citations = extract_citations_clean(text)

print("\nExtracted citations:")
for i, cit in enumerate(citations):
    print(f"{i+1}. {cit.citation}")
    print(f"   Case name: '{cit.extracted_case_name}'")
    print(f"   Start: {cit.start_index}, End: {cit.end_index}")
    
    # Add duplicate tracking metadata
    if hasattr(cit, 'metadata'):
        if cit.metadata is None:
            cit.metadata = {}
        
        # Count occurrences of this citation
        citation_text = cit.citation
        occurrence_count = sum(1 for c in citations if c.citation == citation_text)
        
        if occurrence_count > 1:
            cit.metadata['is_duplicate'] = True
            cit.metadata['occurrence_count'] = occurrence_count
            cit.metadata['duplicate_group'] = citation_text
            print(f"   Duplicate: YES (group: {citation_text})")
        else:
            cit.metadata['is_duplicate'] = False
            print(f"   Duplicate: NO")

print("\n" + "=" * 60)
print("IMPLEMENTATION SUGGESTION:")
print("-" * 60)
print("1. Add duplicate tracking metadata in the clustering phase")
print("2. Frontend can group by 'duplicate_group' field")
print("3. Show occurrence count to user")
print("4. Allow expanding/collapsing duplicate groups")
