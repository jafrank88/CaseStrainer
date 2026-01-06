#!/usr/bin/env python3
"""
Test and fix WL extraction with various docket formats
"""

import re

def test_wl_docket_patterns():
    """Test different docket number patterns in WL citations"""
    
    test_cases = [
        # Original failing case
        "Doe, Inc. v. Roe, No. MC 21-43 (BAH), 2021 WL 3622166, at *3 (D.D.C. June 3, 2021).",
        
        # Variations
        "Smith v. Jones, No. 2:18-CV-00348-SMJ, 2019 WL 2066127",
        "Brown v. Board, No. MC-2021-123, 2021 WL 1234567",
        "Acme Corp. v. XYZ Inc., No. 21-1234, 2021 WL 987654",
        "Case name, No. 2021-CA-00123, 2021 WL 456789",
    ]
    
    print("=" * 80)
    print("TESTING WL DOCKET PATTERNS")
    print("=" * 80)
    print()
    
    # Current pattern from the code
    current_pattern = r"([A-Z][^,]{10,150}?),\s*(?:LLC|Inc\.|Corp\.|Co\.|Ltd\.)?,?\s*No\.?\s+[\w:/-]+"
    
    # Improved pattern that handles more docket formats
    improved_pattern = r"([A-Z][^,]{10,150}?),\s*(?:LLC|Inc\.|Corp\.|Co\.|Ltd\.)?,?\s*No\.?\s+[\w:/\-\s\(\)]+?"
    
    # Even more flexible pattern
    flexible_pattern = r"([A-Z][^,]{10,150}?(?:v\.\s+[\w\s&\-\.',]+|In\s+re\s+[\w\s&\-\.',]+))[^,]*,\s*No\.?\s+[^,]+,\s*\d{4}\s+WL\s+\d+"
    
    # Best pattern - extract case name directly before WL
    best_pattern = r"([A-Z][\w\s&\-\.',]*v\.[\w\s&\-\.',]*?),\s*(?:No\.\s+[^,]+,\s*)?\d{4}\s+WL\s+\d+"
    
    patterns = [
        ("Current (broken)", current_pattern),
        ("Improved", improved_pattern),
        ("Flexible", flexible_pattern),
        ("Best", best_pattern),
    ]
    
    for test_text in test_cases:
        print(f"\nTesting: {test_text[:60]}...")
        
        for name, pattern in patterns:
            match = re.search(pattern, test_text, re.IGNORECASE)
            if match:
                case_name = match.group(1).strip()
                print(f"  {name:12}: ✓ '{case_name}'")
            else:
                print(f"  {name:12}: ✗ No match")
    
    print("\n" + "="*80)
    print("PATTERN ANALYSIS")
    print("="*80)
    print()
    print("The issue with the original citation:")
    print("  'Doe, Inc. v. Roe, No. MC 21-43 (BAH), 2021 WL 3622166'")
    print()
    print("Problems:")
    print("1. Current pattern expects docket like '2:18-CV-00348-SMJ'")
    print("2. Your docket 'MC 21-43 (BAH)' has spaces and parentheses")
    print("3. The pattern stops at first comma after 'Inc.'")
    print()
    print("Solution:")
    print("- Use 'Best' pattern that looks for 'v.' then stops at WL")
    print("- This handles any docket format between case name and WL")

if __name__ == "__main__":
    test_wl_docket_patterns()
