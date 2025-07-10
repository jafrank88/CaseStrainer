#!/usr/bin/env python3
"""
Test script for improved complex citation extraction.
Tests the specific parallel citation patterns mentioned:
1. name, citation citation, citation (date)
2. name, citation, page, citation, page, citation, page (date)
"""

import sys
import os

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# DEPRECATED: # DEPRECATED: from src.complex_citation_integration import ComplexCitationIntegrator

def test_complex_citation_patterns():
    """Test the improved complex citation extraction patterns."""
    
    integrator = ComplexCitationIntegrator()
    
    # Test cases from the original paragraph
    test_cases = [
        # Pattern 1: name, citation citation, citation (date)
        {
            'text': 'John Doe A v. Washington State Patrol, 185 Wn.2d 363, 374 P.3d 63 (2016)',
            'expected_citations': ['185 Wn.2d 363', '374 P.3d 63'],
            'expected_case_name': 'John Doe A v. Washington State Patrol',
            'expected_year': '2016'
        },
        
        # Pattern 2: name, citation, page, citation, page (date) - with pinpoint pages
        {
            'text': 'John Doe P v. Thurston County, 199 Wn. App. 280, 283, 399 P.3d 1195 (2017)',
            'expected_citations': ['199 Wn. App. 280', '399 P.3d 1195'],
            'expected_case_name': 'John Doe P v. Thurston County',
            'expected_year': '2017'
        },
        
        # Pattern 3: name, citation, page, citation, page (date) - 2 citations with pinpoint pages
        {
            'text': 'State v. Lewis, 115 Wn.2d 294, 298-99, 797 P.2d 1141 (1990)',
            'expected_citations': ['115 Wn.2d 294', '797 P.2d 1141'],
            'expected_case_name': 'State v. Lewis',
            'expected_year': '1990'
        },
        
        # Pattern 4: name, citation, citation, citation (date) - 3 citations
        {
            'text': 'Cohen v. Everett City Council, 85 Wn.2d 385, 388, 535 P.2d 801 (1975)',
            'expected_citations': ['85 Wn.2d 385', '535 P.2d 801'],
            'expected_case_name': 'Cohen v. Everett City Council',
            'expected_year': '1975'
        },
        
        # Additional test cases
        {
            'text': 'Seattle Times Co. v. Ishikawa, 97 Wn.2d 30, 640 P.2d 716 (1982)',
            'expected_citations': ['97 Wn.2d 30', '640 P.2d 716'],
            'expected_case_name': 'Seattle Times Co. v. Ishikawa',
            'expected_year': '1982'
        },
        
        {
            'text': 'Allied Daily Newspapers v. Eikenberry, 121 Wn.2d 205, 211, 848 P.2d 1258 (1993)',
            'expected_citations': ['121 Wn.2d 205', '848 P.2d 1258'],
            'expected_case_name': 'Allied Daily Newspapers v. Eikenberry',
            'expected_year': '1993'
        }
    ]
    
    print("Testing Improved Complex Citation Extraction")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"Input: {test_case['text']}")
        
        # Parse the complex citation
        complex_data = integrator.parse_complex_citation(test_case['text'])
        
        print(f"Extracted Case Name: {complex_data.case_name}")
        print(f"Primary Citation: {complex_data.primary_citation}")
        print(f"Parallel Citations: {complex_data.parallel_citations}")
        print(f"All Citations: {complex_data.primary_citation and [complex_data.primary_citation] + complex_data.parallel_citations or []}")
        print(f"Year: {complex_data.year}")
        print(f"Is Complex: {complex_data.is_complex}")
        
        # Check results
        all_citations = []
        if complex_data.primary_citation:
            all_citations.append(complex_data.primary_citation)
        all_citations.extend(complex_data.parallel_citations)
        
        # Verify citations
        citations_match = set(all_citations) == set(test_case['expected_citations'])
        case_name_match = complex_data.case_name == test_case['expected_case_name']
        year_match = complex_data.year == test_case['expected_year']
        
        print(f"Citations Match: {'✓' if citations_match else '✗'}")
        print(f"Case Name Match: {'✓' if case_name_match else '✗'}")
        print(f"Year Match: {'✓' if year_match else '✗'}")
        
        if not citations_match:
            print(f"Expected: {test_case['expected_citations']}")
            print(f"Got: {all_citations}")
        
        if not case_name_match:
            print(f"Expected: {test_case['expected_case_name']}")
            print(f"Got: {complex_data.case_name}")
        
        if not year_match:
            print(f"Expected: {test_case['expected_year']}")
            print(f"Got: {complex_data.year}")
        
        print("-" * 40)

def test_original_paragraph():
    """Test the original paragraph to see if it extracts all citations properly."""
    
    integrator = ComplexCitationIntegrator()
    
    original_paragraph = """Zink filed her first appeal after the trial court granted summary judgment to 
the Does. While the appeal was pending, this court decided John Doe A v. 
Washington State Patrol, which rejected a PRA exemption claim for sex offender 
registration records that was materially identical to one of the Does' claims in this 
case. 185 Wn.2d 363, 374 P.3d 63 (2016). Thus, following John Doe A, the Court 
of Appeals here reversed in part and held "that the registration records must be 
released." John Doe P v. Thurston County, 199 Wn. App. 280, 283, 399 P.3d 1195 
(2017) (Doe I), modified on other grounds on remand, No. 48000-0-II (Wash. Ct. 
App. Oct. 2, 2018) (Doe II) (unpublished),"""
    
    print("\n" + "=" * 60)
    print("Testing Original Paragraph")
    print("=" * 60)
    
    # Extract all potential citation blocks
    citation_blocks = []
    
    # Look for citation patterns in the text
    lines = original_paragraph.split('\n')
    for line in lines:
        if any(pattern in line for pattern in ['Wn.2d', 'Wn. App.', 'P.3d', 'P.2d']):
            citation_blocks.append(line.strip())
    
    print(f"Found {len(citation_blocks)} citation blocks:")
    for i, block in enumerate(citation_blocks, 1):
        print(f"\nBlock {i}: {block}")
        
        # Parse each block
        complex_data = integrator.parse_complex_citation(block)
        
        print(f"  Case Name: {complex_data.case_name}")
        print(f"  Primary Citation: {complex_data.primary_citation}")
        print(f"  Parallel Citations: {complex_data.parallel_citations}")
        print(f"  Year: {complex_data.year}")
        print(f"  Is Complex: {complex_data.is_complex}")

def test_citation_pinpoint_pairing():
    """Test the pairing of citations with their pinpoints (including ranges and singles)."""
    integrator = ComplexCitationIntegrator()
    test_cases = [
        {
            'text': 'State v. Lewis, 115 Wn.2d 294, 298-99, 797 P.2d 1141, 300 (1990)',
            'expected': [('115 Wn.2d 294', '298-99'), ('797 P.2d 1141', '300')]
        },
        {
            'text': 'John Doe A v. Washington State Patrol, 185 Wn.2d 363, 374 P.3d 63 (2016)',
            'expected': [('185 Wn.2d 363', None), ('374 P.3d 63', None)]
        },
        {
            'text': 'Cohen v. Everett City Council, 85 Wn.2d 385, 388, 535 P.2d 801 (1975)',
            'expected': [('85 Wn.2d 385', '388'), ('535 P.2d 801', None)]
        },
        {
            'text': 'Allied Daily Newspapers v. Eikenberry, 121 Wn.2d 205, 211, 848 P.2d 1258, 215 (1993)',
            'expected': [('121 Wn.2d 205', '211'), ('848 P.2d 1258', '215')]
        },
    ]
    print("\nTesting Citation-Pinpoint Pairing")
    print("=" * 60)
    for i, case in enumerate(test_cases, 1):
        pairs = integrator.extract_citations_with_pinpoints(case['text'])
        print(f"Test {i}: {case['text']}")
        print(f"Extracted: {pairs}")
        print(f"Expected:  {case['expected']}")
        print(f"Match: {'✓' if pairs == case['expected'] else '✗'}")
        print("-" * 40)

if __name__ == "__main__":
    test_complex_citation_patterns()
    test_original_paragraph()
    test_citation_pinpoint_pairing() 