#!/usr/bin/env python3
"""
Test case name extraction patterns on failed examples to understand why they're failing.
"""

import re
import json
import os
from collections import defaultdict

def load_adaptive_results():
    """Load the adaptive learning results."""
    results_file = "adaptive_results/adaptive_processing_results.json"
    if not os.path.exists(results_file):
        print(f"Results file not found: {results_file}")
        return []
    
    with open(results_file, 'r') as f:
        return json.load(f)

def test_case_name_patterns():
    """Test case name extraction patterns on failed examples."""
    results = load_adaptive_results()
    
    if not results:
        print("No results to analyze")
        return
    
    # Collect failed extractions
    failed_extractions = []
    
    for doc_result in results:
        filename = doc_result.get('filename', 'Unknown')
        comparison_results = doc_result.get('comparison_results', [])
        
        for comp in comparison_results:
            extracted = comp.get('extracted', {})
            
            case_name = extracted.get('case_name', '').strip()
            citation = extracted.get('citation', '').strip()
            year = extracted.get('year', '').strip()
            
            if not case_name:  # Failed extraction
                failed_extractions.append({
                    'filename': filename,
                    'citation': citation,
                    'year': year
                })
    
    print("=" * 80)
    print("CASE NAME EXTRACTION PATTERN TESTING")
    print("=" * 80)
    
    # Test patterns from the actual extraction code
    patterns = [
        # Pattern 1: Standard v. cases with citation
        r'([A-Z][A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Z][A-Za-z\s,\.\'-]+?)\s*,\s*',
        # Pattern 2: Standard v. cases with year
        r'([A-Z][A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Z][A-Za-z\s,\.\'-]+?)\s*\(\d{4}\)',
        # Pattern 3: In re cases
        r'(In\s+re\s+[A-Za-z\s,\.\'-]+?)\s*,\s*',
        # Pattern 4: State v. cases
        r'(State\s+v\.\s+[A-Za-z\s,\.\'-]+?)\s*,\s*',
        # Pattern 5: More flexible pattern
        r'([A-Z][A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Z][A-Za-z\s,\.\'-]+?)(?=\s*,|\s*$|\s*\d)',
    ]
    
    # Test on a sample of failed extractions
    sample_size = min(20, len(failed_extractions))
    test_samples = failed_extractions[:sample_size]
    
    print(f"Testing {len(test_samples)} failed extractions:")
    print("-" * 50)
    
    for i, extraction in enumerate(test_samples):
        print(f"\n{i+1}. Citation: {extraction['citation']}")
        print(f"   Year: {extraction['year']}")
        print(f"   File: {extraction['filename']}")
        
        # Create a mock context (this is what the extraction would see)
        # In real extraction, this would be the text before the citation
        mock_context = f"Some legal text here. Case Name v. Defendant Name, {extraction['citation']}"
        
        print(f"   Mock context: '{mock_context}'")
        
        # Test each pattern
        for j, pattern in enumerate(patterns):
            matches = list(re.finditer(pattern, mock_context, re.IGNORECASE))
            if matches:
                print(f"   Pattern {j+1} ✓: Found {len(matches)} matches")
                for match in matches:
                    print(f"     Match: '{match.group(1)}'")
            else:
                print(f"   Pattern {j+1} ✗: No matches")
    
    # Now test with real context from the documents
    print(f"\n" + "=" * 80)
    print("TESTING WITH REAL DOCUMENT CONTEXT")
    print("=" * 80)
    
    # Look for actual document text to test with
    # Since we don't have the original documents, let's create realistic test cases
    test_cases = [
        {
            'context': "The court held in Smith v. Jones, 200 Wn.2d 72, 73, 514 P.3d 643 (2022) that...",
            'citation': "200 Wn.2d 72",
            'expected': "Smith v. Jones"
        },
        {
            'context': "As established in Department of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)...",
            'citation': "146 Wn.2d 1",
            'expected': "Department of Ecology v. Campbell & Gwinn, LLC"
        },
        {
            'context': "In re Estate of Smith, 170 Wn.2d 614, 316 P.3d 1020 (2010)...",
            'citation': "170 Wn.2d 614",
            'expected': "In re Estate of Smith"
        },
        {
            'context': "State v. Johnson, 93 Wn.2d 31, 604 P.2d 1293 (2002)...",
            'citation': "93 Wn.2d 31",
            'expected': "State v. Johnson"
        }
    ]
    
    print("Testing patterns on realistic legal text:")
    print("-" * 50)
    
    for i, test_case in enumerate(test_cases):
        print(f"\nTest Case {i+1}:")
        print(f"  Context: '{test_case['context']}'")
        print(f"  Citation: '{test_case['citation']}'")
        print(f"  Expected: '{test_case['expected']}'")
        
        # Test each pattern
        for j, pattern in enumerate(patterns):
            matches = list(re.finditer(pattern, test_case['context'], re.IGNORECASE))
            if matches:
                print(f"  Pattern {j+1} ✓: Found {len(matches)} matches")
                for match in matches:
                    extracted = match.group(1).strip()
                    print(f"    Extracted: '{extracted}'")
                    if extracted == test_case['expected']:
                        print(f"    ✓ MATCH!")
                    else:
                        print(f"    ✗ MISMATCH")
            else:
                print(f"  Pattern {j+1} ✗: No matches")
    
    # Analyze the patterns that work vs don't work
    print(f"\n" + "=" * 80)
    print("PATTERN ANALYSIS")
    print("=" * 80)
    
    working_patterns = defaultdict(int)
    failing_patterns = defaultdict(int)
    
    for test_case in test_cases:
        for j, pattern in enumerate(patterns):
            matches = list(re.finditer(pattern, test_case['context'], re.IGNORECASE))
            if matches:
                # Check if any match is close to expected
                for match in matches:
                    extracted = match.group(1).strip()
                    if extracted == test_case['expected']:
                        working_patterns[j] += 1
                        break
                else:
                    failing_patterns[j] += 1
            else:
                failing_patterns[j] += 1
    
    print("Pattern Performance:")
    print("-" * 30)
    for j in range(len(patterns)):
        working = working_patterns[j]
        failing = failing_patterns[j]
        total = working + failing
        success_rate = working / total * 100 if total > 0 else 0
        print(f"Pattern {j+1}: {working}/{total} ({success_rate:.1f}% success)")
    
    # Recommendations
    print(f"\nRECOMMENDATIONS:")
    print("-" * 30)
    
    # Find the best performing patterns
    best_patterns = sorted(working_patterns.items(), key=lambda x: x[1], reverse=True)
    
    if best_patterns:
        print("Best performing patterns:")
        for pattern_idx, count in best_patterns[:2]:
            print(f"  - Pattern {pattern_idx + 1}: {count} successful matches")
    
    print("\nSuggested improvements:")
    print("1. Focus on patterns that require exact citation matching")
    print("2. Add more flexible spacing around 'v.' and 'vs.'")
    print("3. Improve handling of business entities (LLC, Inc., Corp.)")
    print("4. Add better validation for case name quality")

if __name__ == "__main__":
    test_case_name_patterns() 