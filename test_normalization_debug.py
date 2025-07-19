#!/usr/bin/env python3

def test_normalization_method():
    print("=== Testing Normalization Method Directly ===\n")
    
    try:
        from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
        
        processor = UnifiedCitationProcessorV2()
        
        test_citations = [
            "200 Wn.2d 72",
            "171 Wn.2d 486", 
            "146 Wn.2d 1",
            "200 Wn.App. 123"
        ]
        
        print("Testing _normalize_citation_for_verification method:")
        for citation in test_citations:
            normalized = processor._normalize_citation_for_verification(citation)
            print(f"  '{citation}' -> '{normalized}'")
            
        print("\nTesting _normalize_citation method:")
        for citation in test_citations:
            normalized = processor._normalize_citation(citation)
            print(f"  '{citation}' -> '{normalized}'")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_normalization_method() 