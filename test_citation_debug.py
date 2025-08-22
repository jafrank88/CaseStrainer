#!/usr/bin/env python3
"""
Debug script to examine citation objects and extraction process.
"""

import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def debug_citation_objects():
    """Debug what's happening with citation objects."""
    try:
        from src.enhanced_sync_processor import EnhancedSyncProcessor, ProcessingOptions
        
        # Test text with known citations
        test_text = """
        A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003).
        """
        
        options = ProcessingOptions(
            enable_enhanced_verification=False,  # Disable to avoid API calls
            enable_cross_validation=False,
            enable_false_positive_prevention=False,  # Disable to see all citations
            enable_confidence_scoring=False
        )
        
        processor = EnhancedSyncProcessor(options)
        
        print("🔍 Debugging citation extraction process...")
        print("=" * 60)
        
        # Test the citation extraction step by step
        print("\n1. Testing fast citation extraction...")
        citations = processor._extract_citations_fast(test_text)
        print(f"   Found {len(citations)} citations")
        
        for i, citation in enumerate(citations[:3]):
            print(f"   Citation {i+1}: {citation}")
            print(f"   Type: {type(citation)}")
            if hasattr(citation, '__dict__'):
                print(f"   Attributes: {list(citation.__dict__.keys())}")
                for attr, value in citation.__dict__.items():
                    if attr in ['citation', 'extracted_case_name', 'extracted_date', 'canonical_name', 'canonical_date']:
                        print(f"     {attr}: {value}")
            print()
        
        print("\n2. Testing local normalization...")
        normalized = processor._normalize_citations_local(citations, test_text)
        print(f"   Normalized {len(normalized)} citations")
        
        print("\n3. Testing enhanced local extraction...")
        enhanced = processor._extract_names_years_local(normalized, test_text)
        print(f"   Enhanced {len(enhanced)} citations")
        
        for i, citation in enumerate(enhanced[:3]):
            print(f"   Enhanced Citation {i+1}:")
            if isinstance(citation, dict):
                for key, value in citation.items():
                    if key in ['citation', 'extracted_case_name', 'extracted_date', 'confidence_score']:
                        print(f"     {key}: {value}")
            else:
                print(f"     Type: {type(citation)}")
                # For CitationResult objects, show the actual citation data
                if hasattr(citation, 'citation'):
                    print(f"     citation: {citation.citation}")
                if hasattr(citation, 'extracted_case_name'):
                    print(f"     extracted_case_name: {citation.extracted_case_name}")
                if hasattr(citation, 'extracted_date'):
                    print(f"     extracted_date: {citation.extracted_date}")
                if hasattr(citation, 'confidence_score'):
                    print(f"     confidence_score: {citation.confidence_score}")
                if hasattr(citation, 'extraction_method'):
                    print(f"     extraction_method: {citation.extraction_method}")
            print()
        
        print("\n4. Testing citation conversion...")
        converted = processor._convert_citations_to_dicts(enhanced)
        print(f"   Converted {len(converted)} citations")
        
        for i, citation in enumerate(converted[:3]):
            print(f"   Converted Citation {i+1}:")
            for key, value in citation.items():
                if key in ['citation', 'extracted_case_name', 'extracted_date', 'confidence_score', 'extraction_method']:
                    print(f"     {key}: {value}")
            print()
        
        print("\n5. Testing case name extraction directly...")
        test_citation = "200 Wn.2d 72"
        case_name = processor._extract_case_name_local(test_text, test_citation)
        year = processor._extract_year_local(test_text, test_citation)
        print(f"   Citation: {test_citation}")
        print(f"   Extracted case name: {case_name}")
        print(f"   Extracted year: {year}")
        
        # Show the context around the citation
        pos = test_text.find(test_citation)
        if pos != -1:
            context_start = max(0, pos - 100)
            context_end = min(len(test_text), pos + len(test_citation) + 100)
            context = test_text[context_start:context_end]
            print(f"   Context: ...{context}...")
        else:
            print("   Context: Citation not found in text")
        
        print("\n✅ Debug completed!")
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    debug_citation_objects()
