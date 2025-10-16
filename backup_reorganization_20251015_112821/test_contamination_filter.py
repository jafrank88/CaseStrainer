"""
Test the contamination filter logic to see why it's not catching contamination
"""

import re

def normalize_for_comparison(name):
    """Same as in the code"""
    normalized = name.lower()
    normalized = re.sub(r'[,\.\s]+', ' ', normalized)
    normalized = normalized.strip()
    return normalized

# Test data
document_primary = "AJAY THAKORE, an individual, Plaintiffs - Appellants , v. ANDREW MELONE"
contaminated_names = [
    "GOPHER MEDIA LLC v. MELONE Before",
    "Gopher Media LLC v. Melone",
    "MELONE California state court. Id. A decade later, in DC Com",
    "GOPHER MEDIA LLC v. MELONE Pacific Pictures Corp",
    "Id. GOPHER MEDIA LLC v. MELONE",
    "MELONE Railroad Co. v. Tompkins"
]

# Normalize
primary_normalized = normalize_for_comparison(document_primary)
print(f"Primary normalized: '{primary_normalized}'")
print()

# Split primary
primary_parts = primary_normalized.split(' v ')
if len(primary_parts) == 2:
    plaintiff = primary_parts[0].strip()
    defendant = primary_parts[1].strip()
    
    print(f"Plaintiff: '{plaintiff}'")
    print(f"Defendant: '{defendant}'")
    print()
    
    # Test each contaminated name
    for extracted in contaminated_names:
        extracted_normalized = normalize_for_comparison(extracted)
        print(f"\nTesting: '{extracted}'")
        print(f"Normalized: '{extracted_normalized}'")
        
        # Check Strategy 1: Full containment
        if primary_normalized in extracted_normalized:
            print(f"  ✓ Strategy 1: Primary in extracted")
            continue
        
        # Check Strategy 2: Both parties
        if plaintiff in extracted_normalized and defendant in extracted_normalized:
            print(f"  ✓ Strategy 2: Both parties found")
            continue
        
        # Check Strategy 2b: Plaintiff words
        common_parties = ['united states', 'state', 'county', 'city', 'government', 'people']
        plaintiff_words = [word for word in plaintiff.split() if len(word) > 5]
        print(f"  Plaintiff words (>{5} chars): {plaintiff_words}")
        found_plaint = False
        for plaint_word in plaintiff_words:
            if plaint_word not in common_parties and plaint_word in extracted_normalized:
                print(f"  ✓ Strategy 2b: Plaintiff word '{plaint_word}' found!")
                found_plaint = True
                break
        if found_plaint:
            continue
        
        # Check Strategy 2c: Defendant words
        defendant_words = [word for word in defendant.split() if len(word) > 4]
        print(f"  Defendant words (>{4} chars): {defendant_words}")
        found_def = False
        for def_word in defendant_words:
            if def_word not in common_parties and def_word in extracted_normalized:
                print(f"  ✓ Strategy 2c: Defendant word '{def_word}' found!")
                found_def = True
                break
        if found_def:
            continue
        
        print(f"  ✗ NOT DETECTED - This is a bug!")
