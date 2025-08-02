#!/usr/bin/env python3
"""
Simple test of case name extraction patterns.
"""
import re

def extract_case_names(text):
    """Extract case names from text using improved patterns."""
    # Common signal words that might precede case names
    signal_words = r'(?:See|See,?\s+e\.?g\.?,?|See,?\s+generally|Cf\.?|But\s+see|Compare|But\s+cf\.?|See\s+also|Accord|But\s+cf\.?|But\s+see,?\s+e\.?g\.?|See\s+generally|E\.g\.?,?|I\.e\.?,?|But\s+see,?\s+generally|Cf\.?\s+e\.?g\.?|But\s+cf\.?\s+e\.?g\.?)?\s*'
    
    # Pattern for case names with years in parentheses
    year_pattern = f'({signal_words}[A-Z][A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Z][A-Za-z\s,\.\'-]+?)\s*\(\d{{4}}\)'
    
    found = set()
    
    # First pass: Look for case names with years, including signal words
    for match in re.finditer(year_pattern, text, re.IGNORECASE):
        case_name = match.group(1).strip()
        # Clean up the case name
        case_name = re.sub(r'^[^A-Za-z]*', '', case_name)  # Remove leading non-letters
        case_name = re.sub(r'[\s,;:.]+$', '', case_name)  # Remove trailing punctuation
        # Extract just the case name part (after any signal words)
        case_name = re.sub(r'^.*?(?=[A-Z][a-z])', '', case_name)
        if _is_valid_case_name(case_name):
            found.add(case_name)
    
    # If we didn't find any, try more general patterns
    if not found:
        patterns = [
            # Pattern for standard case names (e.g., "Smith v. Jones")
            f'({signal_words}[A-Z][A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Z][A-Za-z\s,\.\'-]+?)(?=\s*[,;]|\s*\d+\s+[A-Z]|\s*$)',
            # Pattern for State v. cases
            f'({signal_words}State\s+v\.\s+[A-Z][A-Za-z\s,\.\'-]+?)(?=\s*[,;]|\s*\d+\s+[A-Z]|\s*$)',
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                case_name = match.group(1).strip()
                # Clean up the case name
                case_name = re.sub(r'^[^A-Za-z]*', '', case_name)  # Remove leading non-letters
                case_name = re.sub(r'[\s,;:.]+$', '', case_name)  # Remove trailing punctuation
                # Extract just the case name part (after any signal words)
                case_name = re.sub(r'^.*?(?=[A-Z][a-z])', '', case_name)
                if _is_valid_case_name(case_name):
                    found.add(case_name)
    
    # If we still haven't found anything, try a more permissive pattern
    if not found:
        permissive_pattern = r'([A-Z][A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Z][A-Za-z\s,\.\'-]+?)(?=\s*[(,]|\s*\d|\s*$)'
        for match in re.finditer(permissive_pattern, text):
            case_name = match.group(1).strip()
            if _is_valid_case_name(case_name):
                found.add(case_name)
    
    return sorted(found)

def _is_valid_case_name(name):
    """Check if a string looks like a valid case name."""
    if not name or len(name) < 8:  # Minimum length for a valid case name (e.g., "A v. B")
        return False
    # Must contain ' v. ' or ' vs. '
    if not re.search(r'\s+v\.?\s+', name, re.IGNORECASE):
        return False
    # Must start with a capital letter
    if not name[0].isupper():
        return False
    return True

def run_tests():
    """Run test cases for case name extraction."""
    test_cases = [
        {
            "input": "State v. Gentry (1995)",
            "expected": ["State v. Gentry"],
            "description": "Basic case with year in parentheses"
        },
        {
            "input": "In State v. Gentry (1995), the court held...",
            "expected": ["State v. Gentry"],
            "description": "Case in middle of sentence with year"
        },
        {
            "input": "See State v. Gentry (1995), 11 Cal.4th 1",
            "expected": ["State v. Gentry"],
            "description": "Case with citation after year"
        },
        {
            "input": "State v. Gentry, 11 Cal.4th 1 (1995)",
            "expected": ["State v. Gentry"],
            "description": "Case with citation before year"
        },
        {
            "input": "As established in Smith v. Jones (1990) and later in State v. Gentry (1995)",
            "expected": ["Smith v. Jones", "State v. Gentry"],
            "description": "Multiple cases in one sentence"
        },
        {
            "input": "The court in State v. Gentry, 11 Cal.4th 1 (1995), held that...",
            "expected": ["State v. Gentry"],
            "description": "Case with citation in middle of sentence"
        },
        {
            "input": "See, e.g., State v. Gentry (1995) 11 Cal.4th 1, 900 P.2d 1",
            "expected": ["State v. Gentry"],
            "description": "Case with signal and parallel citations"
        },
        {
            "input": "The case of State v. Gentry (1995) established important precedent.",
            "expected": ["State v. Gentry"],
            "description": "Case with surrounding text"
        },
        {
            "input": "See State v. Gentry (1995) (discussing the importance of proper citations).",
            "expected": ["State v. Gentry"],
            "description": "Case with parenthetical explanation"
        }
    ]
    
    print("Testing case name extraction...\n")
    all_passed = True
    
    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}: {test['description']}")
        print(f"  Input:    {test['input']}")
        
        found = extract_case_names(test['input'])
        print(f"  Found:    {found}")
        print(f"  Expected: {test['expected']}")
        
        if set(found) == set(test['expected']):
            print("  ✅ PASSED")
        else:
            missing = set(test['expected']) - set(found)
            extra = set(found) - set(test['expected'])
            if missing:
                print(f"  ❌ FAILED - Missing: {missing}")
            if extra:
                print(f"  ❌ FAILED - Extra matches: {extra}")
            all_passed = False
        print()
    
    if all_passed:
        print("\n✅ ALL TESTS PASSED!")
    else:
        print("\n❌ SOME TESTS FAILED")
    
    return all_passed

if __name__ == "__main__":
    run_tests()
