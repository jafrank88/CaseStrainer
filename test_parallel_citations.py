#!/usr/bin/env python3
"""
Test script to verify parallel citation clustering functionality.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from unified_citation_processor_v2 import UnifiedCitationProcessorV2 as UnifiedCitationProcessor

def test_parallel_citation_clustering():
    """Test parallel citation clustering with various scenarios."""
    
    processor = UnifiedCitationProcessor()
    
    # Test case 1: Multiple citations for the same case in same context
    test_text_1 = """
    In Smith v. Jones, 123 F.3d 456 (9th Cir. 2020), 456 F. Supp. 789 (D. Cal. 2020), 
    the court held that parallel citations should be grouped together. The case 
    established important precedent.
    """
    
    print("=== Test 1: Same case name, multiple citations ===")
    results_1 = processor.process_text(test_text_1)
    print(f"Found {len(results_1['citations'])} citations")
    
    for i, citation in enumerate(results_1['citations']):
        print(f"Citation {i+1}: {citation['citation']}")
        print(f"  Case name: {citation.get('case_name', 'N/A')}")
        print(f"  Parallel citations: {citation.get('parallel_citations', [])}")
        print(f"  Is parallel: {citation.get('is_parallel', False)}")
        print()
    
    # Test case 2: Citations separated by punctuation
    test_text_2 = """
    The Supreme Court in Brown v. Board of Education, 347 U.S. 483 (1954), 
    74 S. Ct. 686, 98 L. Ed. 873, established the principle of desegregation.
    """
    
    print("=== Test 2: Citations with punctuation separation ===")
    results_2 = processor.process_text(test_text_2)
    print(f"Found {len(results_2['citations'])} citations")
    
    for i, citation in enumerate(results_2['citations']):
        print(f"Citation {i+1}: {citation['citation']}")
        print(f"  Case name: {citation.get('case_name', 'N/A')}")
        print(f"  Parallel citations: {citation.get('parallel_citations', [])}")
        print(f"  Is parallel: {citation.get('is_parallel', False)}")
        print()
    
    # Test case 3: Different cases (should not be grouped)
    test_text_3 = """
    In Smith v. Jones, 123 F.3d 456 (9th Cir. 2020), the court held one thing.
    In Johnson v. Smith, 456 F.3d 789 (8th Cir. 2021), the court held another.
    """
    
    print("=== Test 3: Different cases (should not be grouped) ===")
    results_3 = processor.process_text(test_text_3)
    print(f"Found {len(results_3['citations'])} citations")
    
    for i, citation in enumerate(results_3['citations']):
        print(f"Citation {i+1}: {citation['citation']}")
        print(f"  Case name: {citation.get('case_name', 'N/A')}")
        print(f"  Parallel citations: {citation.get('parallel_citations', [])}")
        print(f"  Is parallel: {citation.get('is_parallel', False)}")
        print()
    
    # Test case 4: Complex parallel citation pattern
    test_text_4 = """
    The landmark case of Miranda v. Arizona, 384 U.S. 436 (1966), 
    86 S. Ct. 1602, 16 L. Ed. 2d 694, 10 A.L.R.3d 974, established 
    the Miranda rights that police must read to suspects.
    """
    
    print("=== Test 4: Complex parallel citation pattern ===")
    results_4 = processor.process_text(test_text_4)
    print(f"Found {len(results_4['citations'])} citations")
    
    for i, citation in enumerate(results_4['citations']):
        print(f"Citation {i+1}: {citation['citation']}")
        print(f"  Case name: {citation.get('case_name', 'N/A')}")
        print(f"  Parallel citations: {citation.get('parallel_citations', [])}")
        print(f"  Is parallel: {citation.get('is_parallel', False)}")
        print()
    
    # Test case 5: Real-world example from legal brief
    test_text_5 = """
    In the case of Roe v. Wade, 410 U.S. 113 (1973), 93 S. Ct. 705, 
    35 L. Ed. 2d 147, the Supreme Court established a woman's right 
    to choose. This was later modified in Planned Parenthood v. Casey, 
    505 U.S. 833 (1992), 112 S. Ct. 2791, 120 L. Ed. 2d 674.
    """
    
    print("=== Test 5: Real-world legal brief example ===")
    results_5 = processor.process_text(test_text_5)
    print(f"Found {len(results_5['citations'])} citations")
    
    for i, citation in enumerate(results_5['citations']):
        print(f"Citation {i+1}: {citation['citation']}")
        print(f"  Case name: {citation.get('case_name', 'N/A')}")
        print(f"  Parallel citations: {citation.get('parallel_citations', [])}")
        print(f"  Is parallel: {citation.get('is_parallel', False)}")
        print()

if __name__ == "__main__":
    test_parallel_citation_clustering() 