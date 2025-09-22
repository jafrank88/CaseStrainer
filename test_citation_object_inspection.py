#!/usr/bin/env python3

def test_citation_object_inspection():
    """Test to inspect citation objects and see where case_name is being set."""
    
    print("🔍 CITATION OBJECT INSPECTION")
    print("=" * 50)
    
    try:
        # Test direct processing to see citation objects
        from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
        import asyncio
        
        test_text = """
        In Bostain v. Food Express, Inc., 159 Wash.2d 700, 153 P.3d 846 (2007), the court held...
        """
        
        print(f"📊 Processing test text directly with UnifiedCitationProcessorV2...")
        
        processor = UnifiedCitationProcessorV2()
        result = asyncio.run(processor.process_text(test_text))
        
        citations = result.get('citations', [])
        print(f"   Found {len(citations)} citations")
        
        for i, citation in enumerate(citations):
            print(f"\n📖 Citation {i+1}: {citation.citation}")
            print(f"   Type: {type(citation)}")
            print(f"   Has case_name attr: {hasattr(citation, 'case_name')}")
            
            if hasattr(citation, 'case_name'):
                print(f"   case_name value: '{getattr(citation, 'case_name')}'")
            
            print(f"   extracted_case_name: '{getattr(citation, 'extracted_case_name', 'NOT_SET')}'")
            print(f"   canonical_name: '{getattr(citation, 'canonical_name', 'NOT_SET')}'")
            print(f"   cluster_case_name: '{getattr(citation, 'cluster_case_name', 'NOT_SET')}'")
            
            # Check all attributes
            if hasattr(citation, '__dict__'):
                all_attrs = citation.__dict__.keys()
                case_name_attrs = [attr for attr in all_attrs if 'case_name' in attr.lower()]
                print(f"   All case_name related attrs: {case_name_attrs}")
                
                # Show first few attributes for debugging
                print(f"   All attributes: {list(all_attrs)[:10]}...")
            
            # Test to_dict method
            if hasattr(citation, 'to_dict'):
                dict_result = citation.to_dict()
                print(f"   to_dict() has case_name: {'case_name' in dict_result}")
                if 'case_name' in dict_result:
                    print(f"   to_dict() case_name: '{dict_result['case_name']}'")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_citation_object_inspection()
