#!/usr/bin/env python3
"""
Test script to debug citation matching issues in CourtListener verification.
"""

import re

def test_citation_matching():
    """Test the citation matching logic to see why verification is failing."""
    
    print("Testing citation matching logic...")
    print("=" * 60)
    
    # Test citations from our document
    test_citations = [
        "188 Wn.2d 114",
        "392 P.3d 1041",
        "317 P.3d 1068",
        "200 Wn.2d 72",
        "514 P.3d 643"
    ]
    
    # Test the normalization logic
    print("\n1. Testing citation normalization:")
    print("-" * 40)
    
    for citation in test_citations:
        normalized = normalize_citation(citation)
        print(f"  '{citation}' -> '{normalized}'")
    
    # Test citation matching
    print("\n2. Testing citation matching:")
    print("-" * 40)
    
    # Simulate what CourtListener might return
    courtlistener_citations = [
        "188 Wash. 2d 114",  # CourtListener uses "Wash." instead of "Wn."
        "392 P.3d 1041",
        "317 P.3d 1068",
        "200 Wash. 2d 72",
        "514 P.3d 643"
    ]
    
    for i, test_citation in enumerate(test_citations):
        courtlistener_citation = courtlistener_citations[i]
        matches = citations_match(test_citation, courtlistener_citation)
        print(f"  '{test_citation}' vs '{courtlistener_citation}' -> {'✓ MATCH' if matches else '✗ NO MATCH'}")
    
    # Test year extraction
    print("\n3. Testing year extraction:")
    print("-" * 40)
    
    for citation in test_citations:
        year = extract_year_from_citation(citation)
        print(f"  '{citation}' -> year: {year}")
    
    # Test meaningful words matching
    print("\n4. Testing meaningful words matching:")
    print("-" * 40)
    
    test_cases = [
        ("In re Vulnerable Adult Petition for Knight", "Knight v. Knight"),
        ("In re Marriage of Black", "Blackmon v. Blackmon"),
        ("Convoyant, LLC v. DeepThink, LLC", "Convoyant, LLC v. DeepThink, LLC")
    ]
    
    for extracted_name, canonical_name in test_cases:
        has_common = has_meaningful_words_in_common(extracted_name, canonical_name)
        print(f"  '{extracted_name}' vs '{canonical_name}' -> {'✓ COMMON WORDS' if has_common else '✗ NO COMMON WORDS'}")

def normalize_citation(citation: str) -> str:
    """Normalize citation for comparison (same logic as in enhanced_courtlistener_verification.py)."""
    # Remove spaces and convert to lowercase
    norm = citation.replace(' ', '').lower()
    
    # Handle Washington reporter variations
    norm = norm.replace('wn.', 'wn').replace('wash.', 'wn')
    norm = norm.replace('wn2d', 'wn2d').replace('wash2d', 'wn2d')
    norm = norm.replace('wnapp', 'wnapp').replace('washapp', 'wnapp')
    
    # Handle specific Washington reporter patterns
    norm = norm.replace('wash.app.', 'wnapp').replace('wash.app', 'wnapp')
    norm = norm.replace('wash.2d', 'wn2d').replace('wash.2d.', 'wn2d')
    
    # Handle Pacific reporter variations
    norm = norm.replace('p.', 'p').replace('pac.', 'p')
    norm = norm.replace('p2d', 'p2d').replace('pac2d', 'p2d')
    norm = norm.replace('p3d', 'p3d').replace('pac3d', 'p3d')
    
    return norm

def citations_match(citation1: str, citation2: str) -> bool:
    """Check if two citations match (same logic as in enhanced_courtlistener_verification.py)."""
    if not citation1 or not citation2:
        return False
    
    # Normalize citations for comparison
    norm1 = normalize_citation(citation1)
    norm2 = normalize_citation(citation2)
    
    return norm1 == norm2

def extract_year_from_citation(citation: str) -> str:
    """Extract year from citation text (same logic as in enhanced_courtlistener_verification.py)."""
    # Look for 4-digit year in citation
    year_match = re.search(r'(19|20)\d{2}', citation)
    return year_match.group(0) if year_match else None

def has_meaningful_words_in_common(name1: str, name2: str) -> bool:
    """Check if two case names have meaningful words in common (same logic as in enhanced_courtlistener_verification.py)."""
    if not name1 or not name2:
        return False
    
    # Define stopwords (common legal terms that don't distinguish cases)
    stopwords = {
        'in', 're', 'of', 'the', 'and', 'or', 'for', 'to', 'a', 'an', 'v', 'vs', 'versus',
        'petition', 'petitioner', 'respondent', 'appellant', 'appellee', 'plaintiff', 'defendant',
        'state', 'united', 'states', 'county', 'city', 'town', 'village', 'corporation',
        'inc', 'llc', 'ltd', 'co', 'company', 'association', 'foundation', 'trust'
    }
    
    # Extract meaningful words from each name
    words1 = set(extract_meaningful_words(name1, stopwords))
    words2 = set(extract_meaningful_words(name2, stopwords))
    
    # Check for intersection
    common_words = words1.intersection(words2)
    
    # Return True if there's at least one common meaningful word
    return len(common_words) >= 1

def extract_meaningful_words(name: str, stopwords: set) -> list:
    """Extract meaningful words from a case name (same logic as in enhanced_courtlistener_verification.py)."""
    if not name:
        return []
    
    # Split into words and filter out stopwords
    words = re.findall(r'\b\w+\b', name.lower())
    meaningful_words = [word for word in words if word not in stopwords and len(word) > 2]
    
    return meaningful_words

if __name__ == "__main__":
    test_citation_matching()




