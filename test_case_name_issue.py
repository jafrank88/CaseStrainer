#!/usr/bin/env python3
"""
Test script to demonstrate and fix the case name extraction issue.
"""

import re
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_case_name_extraction():
    """Test the current case name extraction logic."""
    
    # Test cases from the problematic response
    test_cases = [
        {
            'context': 'RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022)',
            'citation': '200 Wn.2d 72',
            'expected': 'Convoyant, LLC v. DeepThink, LLC',
            'actual': 'LLC v. DeepThink, LLC'  # What we're getting
        },
        {
            'context': 'Dep\'t of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)',
            'citation': '146 Wn.2d 1',
            'expected': 'Dep\'t of Ecology v. Campbell & Gwinn, LLC',
            'actual': 'Ecology v.\nCampbell & Gwinn, LLC'  # What we're getting
        }
    ]
    
    print("=== TESTING CURRENT CASE NAME EXTRACTION ===")
    
    for i, test_case in enumerate(test_cases):
        print(f"\nTest Case {i+1}:")
        print(f"Context: {test_case['context']}")
        print(f"Citation: {test_case['citation']}")
        print(f"Expected: {test_case['expected']}")
        print(f"Actual (current): {test_case['actual']}")
        
        # Test the current extraction logic
        result = extract_case_name_current(test_case['context'], test_case['citation'])
        print(f"Current result: {result}")
        
        # Test the fixed extraction logic
        fixed_result = extract_case_name_fixed(test_case['context'], test_case['citation'])
        print(f"Fixed result: {fixed_result}")
        
        print("-" * 80)

def extract_case_name_current(context, citation):
    """Current case name extraction logic (problematic)."""
    # This simulates the current logic in UnifiedCitationProcessorV2
    patterns = [
        r'([A-Z][A-Za-z0-9&.,\'\\-]*(?:\s+[A-Za-z0-9&.,\'\\-]+)*\s+(?:v\.|vs\.|versus)\s+[A-Z][A-Za-z0-9&.,\'\\-]*(?:\s+[A-Za-z0-9&.,\'\\-]+)*)',
    ]
    
    for pattern_str in patterns:
        pattern = re.compile(pattern_str, re.IGNORECASE)
        matches = pattern.finditer(context)
        
        for match in matches:
            case_name = match.group(1).strip()
            
            # This is the problematic post-processing logic
            m_case = re.search(r'([A-Z][A-Za-z0-9&.,\'\\-]+(?:\s+[A-Za-z0-9&.,\'\\-]+)*\s+(?:v\.|vs\.|versus).*?)(,\s*(?:LLC|Inc\.|Corp\.|Co\.|Ltd\.|L\.L\.C\.|P\.C\.|LLP|PLLC|PC|LP|PL|PLC|LLC\.|Inc|LLC,|Inc,|LLP,|Ltd,|Co,|Corp,|L\.L\.C\.|P\.C\.|LLP|PLLC|PC|LP|PL|PLC))?(?:,|\(|$)', case_name)
            if m_case:
                case_name = m_case.group(1).strip()
                if m_case.group(2):
                    case_name += m_case.group(2)
            else:
                # fallback to previous logic
                m_leading = re.search(r'([A-Z][A-Za-z0-9&.,\'\\-]*(?:\s+[A-Za-z0-9&.,\'\\-]+)*\s+(?:v\.|vs\.|versus)\s+[A-Z][A-Za-z0-9&.,\'\\-]+(?:\s+[A-Za-z0-9&.,\'\\-]+)*)', case_name)
                if m_leading:
                    case_name = m_leading.group(1)
            
            # Trim any leading context before the actual case name
            m_lead_trim = re.search(r'([A-Z][A-Za-z0-9&.,\'\\-]+\s+(?:v\.|vs\.|versus)\s+[A-Z][A-Za-z0-9&.,\'\\-]+.*)', case_name)
            if m_lead_trim:
                case_name = m_lead_trim.group(1)
            
            case_name = re.sub(r',?\s*\d+\s+[A-Za-z.]+(?:\s+\d+)*.*$', '', case_name)
            case_name = re.sub(r'\(\d{4}\)$', '', case_name)
            case_name = re.sub(r',\s*\d+\s*[A-Za-z.]+.*$', '', case_name)
            case_name = case_name.strip(' ,;')
            case_name = re.sub(r'\s+\d+\s*$', '', case_name)
            case_name = re.sub(r'\s+\d+,\s*\d+\s*$', '', case_name)
            
            return case_name
    
    return None

def extract_case_name_fixed(context, citation):
    """Fixed case name extraction logic."""
    # Find the citation in the context
    citation_index = context.find(citation)
    if citation_index == -1:
        return None
    
    # Get context before the citation (up to 200 chars)
    context_before = context[max(0, citation_index - 200):citation_index]
    
    # Look for case name patterns that end with a comma and the citation
    patterns = [
        # Standard pattern: case name, citation
        r'([A-Z][A-Za-z0-9&.,\'\- ]+(?:v\.|vs\.|versus)\s+[A-Za-z0-9&.,\'\- ]+?),\s*' + re.escape(citation),
        # Pattern with year: case name (year), citation
        r'([A-Z][A-Za-z0-9&.,\'\- ]+(?:v\.|vs\.|versus)\s+[A-Za-z0-9&.,\'\- ]+?)\s*\(\d{4}\),\s*' + re.escape(citation),
        # Pattern for "Dep't of" cases
        r'(Dep\'t\s+of\s+[A-Za-z0-9&.,\'\- ]+(?:v\.|vs\.|versus)\s+[A-Za-z0-9&.,\'\- ]+?),\s*' + re.escape(citation),
        # Pattern for "In re" cases
        r'(In\s+re\s+[A-Za-z0-9&.,\'\- ]+?),\s*' + re.escape(citation),
    ]
    
    for pattern in patterns:
        match = re.search(pattern, context_before, re.IGNORECASE)
        if match:
            case_name = match.group(1).strip()
            
            # Clean up the case name
            case_name = re.sub(r',\s*$', '', case_name)  # Remove trailing comma
            case_name = re.sub(r'\s+', ' ', case_name)   # Normalize whitespace
            case_name = case_name.strip()
            
            # Validate that it looks like a case name
            if re.search(r'(?:v\.|vs\.|versus)', case_name, re.IGNORECASE):
                return case_name
    
    return None

if __name__ == "__main__":
    test_case_name_extraction() 