#!/usr/bin/env python3
"""
Test the citation processing fix directly
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_citation_processing_fix():
    """Test that the citation processing fix works"""
    print("Testing Citation Processing Fix")
    print("=" * 40)
    
    try:
        # Import the citation service
        from api.services.citation_service import CitationService
        
        # Create service instance
        service = CitationService()
        
        # Test text
        test_text = "In Roe v. Wade, 410 U.S. 113 (1973), the court held that..."
        
        print(f"Test text: {test_text}")
        
        # Test the fixed method
        result = service.process_citations_from_text(test_text)
        
        print(f"Result status: {result.get('status')}")
        print(f"Citations found: {len(result.get('citations', []))}")
        
        if result.get('status') == 'completed':
            print("✅ Citation processing fix is working!")
            
            # Show citation details
            citations = result.get('citations', [])
            for i, citation in enumerate(citations, 1):
                print(f"  {i}. {citation.get('citation', 'N/A')}")
                print(f"     Case: {citation.get('extracted_case_name', 'N/A')}")
                print(f"     Verified: {citation.get('verified', False)}")
            
            return True
        else:
            print(f"❌ Citation processing failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_citation_processing_fix()
    if success:
        print("\n🎉 Citation processing fix is working correctly!")
    else:
        print("\n❌ Citation processing fix needs more work.")
        sys.exit(1) 