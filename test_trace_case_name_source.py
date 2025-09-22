#!/usr/bin/env python3

def test_trace_case_name_source():
    """Trace exactly where the case_name field is being added."""
    
    print("🔍 TRACING CASE_NAME SOURCE")
    print("=" * 50)
    
    try:
        # Test 1: Direct UnifiedCitationProcessorV2
        print("\n📊 TEST 1: Direct UnifiedCitationProcessorV2")
        from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
        import asyncio
        
        test_text = "In Bostain v. Food Express, Inc., 159 Wash.2d 700, 153 P.3d 846 (2007), the court held..."
        
        processor = UnifiedCitationProcessorV2()
        result = asyncio.run(processor.process_text(test_text))
        
        citations = result.get('citations', [])
        if citations:
            citation = citations[0]
            print(f"   Citation: {citation.citation}")
            print(f"   Has case_name attr: {hasattr(citation, 'case_name')}")
            print(f"   to_dict() has case_name: {'case_name' in citation.to_dict()}")
            
        # Test 2: UnifiedInputProcessor
        print("\n📊 TEST 2: UnifiedInputProcessor")
        from src.unified_input_processor import UnifiedInputProcessor
        
        input_processor = UnifiedInputProcessor()
        input_result = input_processor.process_any_input(
            input_data={'text': test_text},
            input_type='text',
            request_id='test_trace'
        )
        
        input_citations = input_result.get('citations', [])
        if input_citations:
            input_citation = input_citations[0]
            print(f"   Citation: {input_citation.get('citation', 'N/A')}")
            print(f"   Has case_name: {'case_name' in input_citation}")
            if 'case_name' in input_citation:
                print(f"   case_name value: '{input_citation['case_name']}'")
        
        # Test 3: API Call
        print("\n📊 TEST 3: API Call")
        import requests
        import json
        
        api_data = {
            'text': test_text
        }
        
        try:
            response = requests.post(
                'http://127.0.0.1:5000/casestrainer/api/analyze',
                json=api_data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                api_result = response.json()
                api_citations = api_result.get('citations', [])
                if api_citations:
                    api_citation = api_citations[0]
                    print(f"   Citation: {api_citation.get('citation', 'N/A')}")
                    print(f"   Has case_name: {'case_name' in api_citation}")
                    if 'case_name' in api_citation:
                        print(f"   case_name value: '{api_citation['case_name']}'")
                        
                    # Show all case name related fields
                    case_name_fields = {k: v for k, v in api_citation.items() if 'case_name' in k.lower()}
                    print(f"   All case_name fields: {case_name_fields}")
            else:
                print(f"   API call failed: {response.status_code}")
        except Exception as e:
            print(f"   API call error: {e}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_trace_case_name_source()
