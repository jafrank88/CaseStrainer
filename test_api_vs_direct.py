#!/usr/bin/env python3
"""
Compare API processing vs direct processing to identify the difference.
"""

import sys
import os
import requests
import uuid
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_api_vs_direct():
    """Compare API processing vs direct processing."""
    
    # Test document with known citations
    test_text = """
    Legal Test Document
    
    Important cases:
    1. State v. Johnson, 160 Wn.2d 500, 158 P.3d 677 (2007)
    2. City of Seattle v. Williams, 170 Wn.2d 200, 240 P.3d 1055 (2010)
    3. Brown v. State, 180 Wn.2d 300, 320 P.3d 800 (2014)
    """ + "\n\nAdditional content. " * 1000  # Make it large (15KB+)
    
    print("🧪 Comparing API vs Direct Processing")
    print("=" * 60)
    print(f"📄 Document size: {len(test_text)} characters ({len(test_text)/1024:.1f} KB)")
    print()
    
    # Test 1: Direct processing
    print("🔧 Test 1: Direct Processing")
    direct_result = test_direct_processing(test_text)
    
    # Test 2: API processing  
    print("\n🌐 Test 2: API Processing")
    api_result = test_api_processing(test_text)
    
    # Compare results
    print("\n" + "=" * 60)
    print("📊 COMPARISON")
    print("=" * 60)
    
    print(f"Direct Processing:")
    print(f"  Success: {direct_result['success']}")
    print(f"  Citations: {direct_result['citations']}")
    print(f"  Mode: {direct_result['mode']}")
    
    print(f"\nAPI Processing:")
    print(f"  Success: {api_result['success']}")
    print(f"  Citations: {api_result['citations']}")
    print(f"  Mode: {api_result['mode']}")
    
    if direct_result['success'] and not api_result['success']:
        print("\n❌ ISSUE: Direct processing works but API processing fails")
        return False
    elif direct_result['citations'] > 0 and api_result['citations'] == 0:
        print("\n❌ ISSUE: Direct processing finds citations but API processing doesn't")
        return False
    elif direct_result['citations'] > 0 and api_result['citations'] > 0:
        print("\n✅ Both processing methods are working!")
        return True
    else:
        print("\n⚠️ Both processing methods have issues")
        return False

def test_direct_processing(text):
    """Test direct processing using UnifiedInputProcessor."""
    try:
        from src.unified_input_processor import process_text_input
        
        request_id = str(uuid.uuid4())
        result = process_text_input(text, request_id)
        
        citations = result.get('citations', [])
        processing_mode = result.get('metadata', {}).get('processing_mode', 'unknown')
        
        print(f"  📊 Direct result: {len(citations)} citations")
        print(f"  🔧 Processing mode: {processing_mode}")
        
        if len(citations) > 0:
            print(f"  📋 Sample citations:")
            for i, citation in enumerate(citations[:2]):
                if isinstance(citation, dict):
                    citation_text = citation.get('citation', 'N/A')
                else:
                    citation_text = str(citation)
                print(f"    {i+1}. {citation_text}")
        
        return {
            'success': result.get('success', False),
            'citations': len(citations),
            'mode': processing_mode
        }
        
    except Exception as e:
        print(f"  💥 Direct processing failed: {e}")
        return {'success': False, 'citations': 0, 'mode': 'error'}

def test_api_processing(text):
    """Test API processing."""
    try:
        response = requests.post(
            "http://localhost:8080/casestrainer/api/analyze",
            json={"text": text},
            timeout=30
        )
        
        print(f"  📊 API status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            citations = data.get('citations', [])
            processing_mode = data.get('metadata', {}).get('processing_mode', 'unknown')
            
            print(f"  📊 API result: {len(citations)} citations")
            print(f"  🔧 Processing mode: {processing_mode}")
            
            if len(citations) > 0:
                print(f"  📋 Sample citations:")
                for i, citation in enumerate(citations[:2]):
                    citation_text = citation.get('citation', 'N/A')
                    print(f"    {i+1}. {citation_text}")
            
            return {
                'success': data.get('success', False),
                'citations': len(citations),
                'mode': processing_mode
            }
        else:
            print(f"  ❌ API request failed: {response.text}")
            return {'success': False, 'citations': 0, 'mode': 'api_error'}
            
    except Exception as e:
        print(f"  💥 API processing failed: {e}")
        return {'success': False, 'citations': 0, 'mode': 'error'}

if __name__ == "__main__":
    success = test_api_vs_direct()
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}: API vs Direct comparison")
