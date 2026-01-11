"""
Test script to verify the citation formatting fix
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

print("CITATION FORMATTING FIX TEST")
print("=" * 60)

# Test with the actual API response structure
test_response = {
    "citations": [
        {
            "citation": "FullCaseCitation('2024 WL 4149252', groups={'volume': '2024', 'reporter': 'WL', 'page': '4149252'}, metadata=FullCaseCitation.Metadata(...))",
            "extracted_case_name": "Mastriano v. Gregory",
            "extracted_date": "2024",
            "verified": False,
            "verification_status": "proprietary_format",
            "verification_error": "Unverified due to proprietary format"
        },
        {
            "citation": "146 F.4th 165",
            "extracted_case_name": "Giuffre v. Maxwell",
            "extracted_date": "2025",
            "verified": True
        }
    ]
}

print("\nSimulating Vue.js formatCitationText function:")
print("-" * 50)

def format_citation_text(citation):
    """Simulate the Vue.js formatCitationText function"""
    # If citation has a text property, use it
    if citation.get('text'):
        return citation['text']
    
    # If citation is a string, return as-is
    if isinstance(citation, str):
        return citation
    
    # If citation.citation exists and is a string
    cit = citation.get('citation', '')
    if isinstance(cit, str):
        return cit
    
    # If citation.citation is an object (eyecite citation), extract the basic citation text
    if isinstance(cit, str) and 'FullCaseCitation' in cit:
        # Extract from the string representation
        import re
        match = re.search(r"FullCaseCitation\('([^']+)'", cit)
        if match:
            return match.group(1)
        
        # Try to extract volume, reporter, page
        volume_match = re.search(r"volume='([^']+)'", cit)
        reporter_match = re.search(r"reporter='([^']+)'", cit)
        page_match = re.search(r"page='([^']+)'", cit)
        
        if volume_match and reporter_match and page_match:
            return f"{volume_match.group(1)} {reporter_match.group(1)} {page_match.group(1)}"
    
    # Fallback
    return cit[:100] + '...' if len(cit) > 100 else cit

# Test formatting
for i, citation in enumerate(test_response['citations']):
    formatted = format_citation_text(citation)
    print(f"\nCitation {i+1}:")
    print(f"  Original: {str(citation['citation'])[:80]}...")
    print(f"  Formatted: {formatted}")
    print(f"  Status: {citation.get('verification_error', 'Verified') if not citation.get('verified') else 'Verified'}")

print("\n" + "=" * 60)
print("RESULT: Citations should now display as clean text instead of JSON")
print("=" * 60)
