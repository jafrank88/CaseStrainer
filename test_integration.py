#!/usr/bin/env python3

# DEPRECATED: # DEPRECATED: from src.complex_citation_integration import ComplexCitationIntegrator

def test_integration():
    integrator = ComplexCitationIntegrator()
    
    # Test with the Washington Supreme Court citation
    test_text = "Seattle Times Co. v. Ishikawa, 97 Wn.2d 30, 640 P.2d 716 (1982)"
    
    print("Testing ComplexCitationIntegrator with EnhancedCitationExtractor...")
    print(f"Input text: {test_text}")
    
    results = integrator.process_text_with_complex_citations_original(test_text)
    
    print(f"\nFound {len(results)} results:")
    
    for i, result in enumerate(results):
        print(f"\nResult {i+1}:")
        print(f"  Citation: {result.get('citation', 'N/A')}")
        print(f"  Case Name: {result.get('case_name', 'N/A')}")
        print(f"  Verified: {result.get('verified', 'N/A')}")
        print(f"  Is Complex: {result.get('is_complex_citation', False)}")
        print(f"  Is Parallel: {result.get('is_parallel_citation', False)}")
        if result.get('parallel_citations'):
            print(f"  Parallel Citations: {result.get('parallel_citations')}")
    
    # Test with a more complex citation that should have parallels
    complex_text = "Seattle Times Co. v. Ishikawa, 97 Wn.2d 30, 640 P.2d 716, 8 Media L. Rep. (BNA) 1041 (1982)"
    
    print(f"\n\nTesting complex citation with more parallels...")
    print(f"Input text: {complex_text}")
    
    complex_results = integrator.process_text_with_complex_citations_original(complex_text)
    
    print(f"\nFound {len(complex_results)} results:")
    
    for i, result in enumerate(complex_results):
        print(f"\nResult {i+1}:")
        print(f"  Citation: {result.get('citation', 'N/A')}")
        print(f"  Case Name: {result.get('case_name', 'N/A')}")
        print(f"  Verified: {result.get('verified', 'N/A')}")
        print(f"  Is Complex: {result.get('is_complex_citation', False)}")
        print(f"  Is Parallel: {result.get('is_parallel_citation', False)}")
        if result.get('parallel_citations'):
            print(f"  Parallel Citations: {result.get('parallel_citations')}")

if __name__ == "__main__":
    test_integration() 