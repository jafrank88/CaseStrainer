#!/usr/bin/env python3
"""
Debug citation objects to see what's happening with name extraction.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_citation_object_creation():
    """Test how citation objects are created and what fields they have."""
    
    print("🔍 Testing Citation Object Creation")
    print("=" * 60)
    
    try:
        from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
        import asyncio
        
        test_text = "State v. Johnson, 160 Wn.2d 500, 158 P.3d 677 (2007) was important."
        
        print(f"📄 Test text: {test_text}")
        print()
        
        processor = UnifiedCitationProcessorV2()
        result = asyncio.run(processor.process_text(test_text))
        
        citations = result.get('citations', [])
        print(f"📊 Found {len(citations)} citations")
        
        for i, citation in enumerate(citations, 1):
            print(f"\n🔍 Citation {i}:")
            print(f"  Type: {type(citation)}")
            print(f"  Has __dict__: {hasattr(citation, '__dict__')}")
            
            if hasattr(citation, '__dict__'):
                citation_dict = citation.__dict__
                print(f"  Dict keys: {list(citation_dict.keys())}")
                print(f"  Citation text: {citation_dict.get('citation', 'N/A')}")
                print(f"  Extracted name: {citation_dict.get('extracted_case_name', 'N/A')}")
                print(f"  Extracted date: {citation_dict.get('extracted_date', 'N/A')}")
                print(f"  Method: {citation_dict.get('method', 'N/A')}")
                print(f"  Source: {citation_dict.get('source', 'N/A')}")
                
                # Check if name extraction fields are None vs empty string
                extracted_name = citation_dict.get('extracted_case_name')
                if extracted_name is None:
                    print(f"  ⚠️ extracted_case_name is None")
                elif extracted_name == '':
                    print(f"  ⚠️ extracted_case_name is empty string")
                elif extracted_name:
                    print(f"  ✅ extracted_case_name has value: '{extracted_name}'")
                
                # Show all non-None, non-empty fields
                print(f"  Non-empty fields:")
                for key, value in citation_dict.items():
                    if value is not None and value != '' and value != [] and value != {}:
                        print(f"    {key}: {value}")
            
            elif isinstance(citation, dict):
                print(f"  Already a dict with keys: {list(citation.keys())}")
                print(f"  Citation text: {citation.get('citation', 'N/A')}")
                print(f"  Extracted name: {citation.get('extracted_case_name', 'N/A')}")
            else:
                print(f"  Unknown citation type: {citation}")
        
        return len(citations) > 0 and any(
            (hasattr(c, '__dict__') and c.__dict__.get('extracted_case_name')) or 
            (isinstance(c, dict) and c.get('extracted_case_name'))
            for c in citations
        )
        
    except Exception as e:
        print(f"💥 Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_name_extraction_step():
    """Test the name extraction step specifically."""
    
    print(f"\n🔧 Testing Name Extraction Step")
    print("=" * 60)
    
    try:
        # Test the name extraction function directly
        from src.unified_case_name_extractor_v2 import extract_case_name_and_date
        
        test_citation = "State v. Johnson, 160 Wn.2d 500, 158 P.3d 677 (2007)"
        
        print(f"📄 Test citation: {test_citation}")
        
        # Test name extraction
        extracted_name, extracted_date = extract_case_name_and_date(test_citation)
        
        print(f"📊 Name extraction results:")
        print(f"  Extracted name: '{extracted_name}'")
        print(f"  Extracted date: '{extracted_date}'")
        
        if extracted_name:
            print(f"  ✅ Name extraction working correctly")
            return True
        else:
            print(f"  ❌ Name extraction failed")
            return False
            
    except Exception as e:
        print(f"💥 Name extraction test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_citation_result_model():
    """Test the CitationResult model to see its structure."""
    
    print(f"\n📋 Testing CitationResult Model")
    print("=" * 60)
    
    try:
        from src.models import CitationResult
        
        # Create a test citation result
        citation_result = CitationResult(
            citation="State v. Johnson, 160 Wn.2d 500, 158 P.3d 677 (2007)",
            extracted_case_name="State v. Johnson",
            extracted_date="2007"
        )
        
        print(f"📊 CitationResult object:")
        print(f"  Type: {type(citation_result)}")
        print(f"  Has __dict__: {hasattr(citation_result, '__dict__')}")
        
        if hasattr(citation_result, '__dict__'):
            print(f"  Dict: {citation_result.__dict__}")
        
        # Test conversion to dict
        if hasattr(citation_result, 'to_dict'):
            dict_result = citation_result.to_dict()
            print(f"  to_dict() result: {dict_result}")
        else:
            print(f"  No to_dict() method")
        
        return True
        
    except Exception as e:
        print(f"💥 CitationResult test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all citation object tests."""
    
    print("🚀 Citation Object Investigation")
    print("=" * 60)
    
    # Test citation object creation
    objects_ok = test_citation_object_creation()
    
    # Test name extraction step
    extraction_ok = test_name_extraction_step()
    
    # Test citation result model
    model_ok = test_citation_result_model()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 INVESTIGATION SUMMARY")
    print("=" * 60)
    
    print(f"Citation Objects: {'✅ PASS' if objects_ok else '❌ FAIL'}")
    print(f"Name Extraction: {'✅ PASS' if extraction_ok else '❌ FAIL'}")
    print(f"CitationResult Model: {'✅ PASS' if model_ok else '❌ FAIL'}")
    
    if not objects_ok:
        print("\n❌ ISSUE: Citation objects don't have extracted names")
    elif not extraction_ok:
        print("\n❌ ISSUE: Name extraction function is broken")
    elif not model_ok:
        print("\n❌ ISSUE: CitationResult model has problems")
    else:
        print("\n✅ All citation object tests passed")
    
    return objects_ok and extraction_ok and model_ok

if __name__ == "__main__":
    main()
