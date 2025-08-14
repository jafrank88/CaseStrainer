#!/usr/bin/env python3
"""
Focused Backend Diagnostic Test
Diagnose specific issues with citation extraction, clustering, and canonical data
"""

import sys
import os
import json
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_basic_citation_extraction():
    """Test basic citation extraction without clustering or canonical data."""
    print("\n🔍 BASIC CITATION EXTRACTION TEST")
    print("-" * 50)
    
    test_text = """
    In Luis v. United States, 578 U.S. 5, 136 S. Ct. 1083, 194 L. Ed. 2d 256 (2016), 
    the Supreme Court held that the pretrial restraint of a criminal defendant's 
    legitimate, untainted assets needed to pay for counsel violates the Sixth Amendment.
    """
    
    try:
        # Test direct citation extraction using eyecite
        print("Testing direct eyecite extraction...")
        import eyecite
        from eyecite import get_citations
        
        citations_found = get_citations(test_text)
        print(f"✅ Eyecite found {len(citations_found)} citations:")
        for i, citation in enumerate(citations_found):
            print(f"   {i+1}. {citation}")
            print(f"      Type: {type(citation).__name__}")
            print(f"      Groups: {citation.groups if hasattr(citation, 'groups') else 'N/A'}")
        
        return len(citations_found) > 0
        
    except Exception as e:
        print(f"❌ Basic citation extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_unified_processor_direct():
    """Test UnifiedInputProcessor directly with simple text."""
    print("\n🔍 UNIFIED PROCESSOR DIRECT TEST")
    print("-" * 50)
    
    test_text = "In Brown v. Board of Education, 347 U.S. 483 (1954), the Court ruled..."
    
    try:
        from src.unified_input_processor import UnifiedInputProcessor
        processor = UnifiedInputProcessor()
        
        print(f"Processing text: {test_text[:50]}...")
        result = processor.process_any_input(
            input_data=test_text,
            input_type='text',
            request_id='test_direct',
            source_name='diagnostic_test'
        )
        
        print(f"Result type: {type(result)}")
        print(f"Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
        if isinstance(result, dict):
            print(f"Success: {result.get('success', 'N/A')}")
            print(f"Citations: {len(result.get('citations', []))}")
            print(f"Clusters: {len(result.get('clusters', []))}")
            print(f"Error: {result.get('error', 'N/A')}")
            
            if result.get('citations'):
                print("First citation details:")
                first_citation = result['citations'][0]
                for key, value in first_citation.items():
                    print(f"   {key}: {value}")
        
        return result and result.get('success', False)
        
    except Exception as e:
        print(f"❌ Unified processor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_citation_service_immediate():
    """Test CitationService immediate processing."""
    print("\n🔍 CITATION SERVICE IMMEDIATE TEST")
    print("-" * 50)
    
    test_text = "Miranda v. Arizona, 384 U.S. 436 (1966)"
    
    try:
        from src.api.services.citation_service import CitationService
        service = CitationService()
        
        print(f"Testing immediate processing with: {test_text}")
        
        # Test if text should be processed immediately
        input_data = {'text': test_text, 'type': 'text'}
        should_process = service.should_process_immediately(input_data)
        print(f"Should process immediately: {should_process}")
        
        if should_process:
            result = service.process_immediately(input_data)
            print(f"Immediate processing result: {result}")
            return result and result.get('status') == 'completed'
        else:
            print("Text not suitable for immediate processing")
            return False
        
    except Exception as e:
        print(f"❌ Citation service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_courtlistener_simple():
    """Test simple CourtListener API call."""
    print("\n🔍 COURTLISTENER SIMPLE TEST")
    print("-" * 50)
    
    try:
        from src.config import get_config_value
        api_key = get_config_value("COURTLISTENER_API_KEY", "")
        
        if not api_key:
            print("⚠️  No API key found, skipping CourtListener test")
            return True
        
        import requests
        
        # Test simple API call
        url = "https://www.courtlistener.com/api/rest/v4/search/"
        params = {
            'q': '578 U.S. 5',
            'type': 'o',
            'format': 'json'
        }
        headers = {
            'Authorization': f'Token {api_key}'
        }
        
        print(f"Testing CourtListener API call...")
        response = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Results count: {data.get('count', 0)}")
            return True
        else:
            print(f"API call failed: {response.text}")
            return False
        
    except Exception as e:
        print(f"❌ CourtListener API test failed: {e}")
        return False

def main():
    """Run focused diagnostic tests."""
    print("🔍 FOCUSED BACKEND DIAGNOSTIC TESTS")
    print("="*60)
    
    tests = [
        ("Basic Citation Extraction", test_basic_citation_extraction),
        ("Unified Processor Direct", test_unified_processor_direct),
        ("Citation Service Immediate", test_citation_service_immediate),
        ("CourtListener Simple", test_courtlistener_simple)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Test {test_name} crashed: {e}")
            results[test_name] = False
    
    print(f"\n" + "="*60)
    print("📊 DIAGNOSTIC RESULTS")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
