#!/usr/bin/env python3
"""
Test the comprehensive web search fallback integration
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_web_search_fallback():
    print("=== TESTING WEB SEARCH FALLBACK INTEGRATION ===")
    
    try:
        from src.enhanced_unified_citation_processor import EnhancedUnifiedCitationProcessor, ProcessingConfig
        
        # Create processor with verification enabled
        config = ProcessingConfig(
            enable_verification=True,
            enable_confidence_breakdown=True,
            debug_mode=True
        )
        
        processor = EnhancedUnifiedCitationProcessor(config)
        
        print(f"Processor initialized:")
        print(f"  CourtListener API key: {'✅' if processor.courtlistener_api_key else '❌'}")
        print(f"  Web search engine: {'✅' if processor.web_search_engine else '❌'}")
        
        # Test with a citation that might not be in CourtListener
        # This should trigger the web search fallback
        test_text = """
        This case references several important precedents including Smith v. Jones, 123 Wn.2d 456 (2020),
        and the federal case Brown v. Board, 347 U.S. 483 (1954). These cases establish important principles.
        """
        
        print(f"\n=== PROCESSING TEST TEXT ===")
        print(f"Text: {test_text.strip()}")
        
        citations = processor.process_text(test_text)
        
        print(f"\n=== RESULTS ===")
        print(f"Found {len(citations)} citations:")
        
        for i, citation in enumerate(citations, 1):
            print(f"\nCitation {i}:")
            print(f"  Citation: {citation.citation}")
            print(f"  Extracted case name: {citation.extracted_case_name}")
            print(f"  Extracted date: {citation.extracted_date}")
            print(f"  Verified: {citation.verified}")
            print(f"  Canonical name: {citation.canonical_name}")
            print(f"  Canonical date: {citation.canonical_date}")
            print(f"  Source: {citation.source}")
            print(f"  URL: {citation.url}")
            print(f"  Confidence: {citation.confidence:.3f}" if hasattr(citation, 'confidence') and citation.confidence else "  Confidence: N/A")
            
            # Check if web search fallback was used
            if citation.source and 'web_search' in citation.source:
                print(f"  🎉 WEB SEARCH FALLBACK SUCCESSFUL!")
            elif citation.source and 'CourtListener' in citation.source:
                print(f"  ✅ CourtListener verification successful")
            elif citation.verified:
                print(f"  ✅ Other verification method successful")
            else:
                print(f"  ❌ Citation not verified")
        
        return citations
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_web_search_fallback()
