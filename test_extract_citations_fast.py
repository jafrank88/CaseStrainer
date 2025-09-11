#!/usr/bin/env python3
"""
Test the _extract_citations_fast function directly to see what's happening.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.enhanced_sync_processor import EnhancedSyncProcessor, ProcessingOptions

def test_extract_citations_fast():
    # Test text
    test_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)."""

    try:
        # Create processor
        options = ProcessingOptions()
        processor = EnhancedSyncProcessor(options)
        
        print("Testing _extract_citations_fast...")
        citations = processor._extract_citations_fast(test_text)
        
        print(f"Found {len(citations)} citations:")
        for i, citation in enumerate(citations, 1):
            if hasattr(citation, 'citation'):
                print(f"  {i}. {citation.citation} -> {getattr(citation, 'extracted_case_name', 'N/A')}")
            else:
                print(f"  {i}. {citation}")
                
    except Exception as e:
        print(f"Exception in _extract_citations_fast: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_extract_citations_fast()

