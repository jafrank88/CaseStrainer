#!/usr/bin/env python3
"""
Test case name contamination cleanup
"""

import re

def clean_case_name_contamination(extracted_name: str, canonical_name: str = None) -> str:
    """
    Clean obvious contamination from extracted case names.
    
    Args:
        extracted_name: The potentially contaminated extracted case name
        canonical_name: The verified canonical case name (optional)
        
    Returns:
        Cleaned case name
    """
    if not extracted_name or extracted_name == "N/A":
        return extracted_name
    
    # Common contamination patterns
    contamination_patterns = [
        r'^(?:this\s+case\s+involves|the\s+case\s+involves|case\s+involves)\s+(.+)$',
        r'^(?:see\s+the\s+case|see\s+case|the\s+case|case)\s+(?:of\s+)?(.+)$',
        r'^(?:in\s+this\s+case|in\s+the\s+case|in\s+case),?\s+(.+)$',
        r'^(?:cf|e\.g\.|i\.e\.|see\s+also|see|compare|accord|but\s+see|but\s+cf|contra)\.?\s+(.+)$',
        r'^(?:if|when|where|while|although|though|unless|until|since|because|as)\s+(?:in\s+)?(.+)$',
    ]
    
    cleaned = extracted_name
    for pattern in contamination_patterns:
        match = re.search(pattern, cleaned, re.IGNORECASE)
        if match:
            cleaned = match.group(1).strip()
            print(f"Removed contamination: '{extracted_name}' → '{cleaned}'")
            break
    
    # If we have a canonical name, use it to validate the cleaned name
    if canonical_name and cleaned:
        # Extract the core case name from canonical (remove long descriptions)
        canonical_core = re.sub(r'^(.+?)\s+v\.\s+.+?$', r'\1', canonical_name, flags=re.IGNORECASE)
        canonical_defendant = re.sub(r'^.+?\s+v\.\s+(.+?)$', r'\1', canonical_name, flags=re.IGNORECASE)
        
        # Check if our cleaned name matches the canonical structure
        if ' v. ' in cleaned:
            cleaned_plaintiff = re.sub(r'^(.+?)\s+v\.\s+.+?$', r'\1', cleaned, flags=re.IGNORECASE)
            cleaned_defendant = re.sub(r'^.+?\s+v\.\s+(.+?)$', r'\1', cleaned, flags=re.IGNORECASE)
            
            # If plaintiff names are very similar, use canonical name
            if (cleaned_plaintiff.lower() in canonical_core.lower() or 
                canonical_core.lower() in cleaned_plaintiff.lower()):
                # Use canonical name but keep our cleaned structure
                return f"{canonical_core} v. {cleaned_defendant}"
    
    return cleaned

# Test the function
test_cases = [
    "This case involves FOSS v. NATIONAL MARINE FISHERIES SERVICE",
    "See the case of Smith v. Jones",
    "In this case, Brown v. Board of Education",
    "Compare Roe v. Wade with other cases",
    "FOSS v. NATIONAL MARINE FISHERIES SERVICE",  # Already clean
]

print("Testing case name contamination cleanup:")
print("=" * 50)

for test_name in test_cases:
    cleaned = clean_case_name_contamination(test_name)
    print(f"'{test_name}' → '{cleaned}'")
    print()
