#!/usr/bin/env python3
"""
Debug why name extraction works directly but fails via API.
"""

import requests
import json

def test_api_vs_direct_detailed():
    """Compare API vs direct processing in detail."""
    
    test_text = "State v. Johnson, 160 Wn.2d 500, 158 P.3d 677 (2007) was important."
    
    print("🔍 Detailed API vs Direct Comparison")
    print("=" * 60)
    print(f"📄 Test text: {test_text}")
    print()
    
    # Test 1: Direct processing
    print("🔧 Test 1: Direct Processing")
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
        
        from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
        import asyncio
        
        processor = UnifiedCitationProcessorV2()
        direct_result = asyncio.run(processor.process_text(test_text))
        
        direct_citations = direct_result.get('citations', [])
        print(f"  Citations found: {len(direct_citations)}")
        
        if len(direct_citations) > 0:
            citation = direct_citations[0]
            if hasattr(citation, '__dict__'):
                citation_dict = citation.__dict__
                print(f"  Citation object type: {type(citation)}")
                print(f"  Citation dict keys: {list(citation_dict.keys())}")
                print(f"  Extracted name: {citation_dict.get('extracted_case_name', 'N/A')}")
                print(f"  Citation text: {citation_dict.get('citation', 'N/A')}")
            else:
                print(f"  Citation is already dict: {citation}")
        
    except Exception as e:
        print(f"  💥 Direct processing failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: API processing (small document for immediate processing)
    print(f"\n🌐 Test 2: API Processing (Small Document)")
    try:
        response = requests.post(
            "http://localhost:8080/casestrainer/api/analyze",
            json={"text": test_text},  # Small text should trigger immediate processing
            timeout=30
        )
        
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            processing_mode = data.get('metadata', {}).get('processing_mode', 'unknown')
            citations = data.get('citations', [])
            
            print(f"  Processing mode: {processing_mode}")
            print(f"  Citations found: {len(citations)}")
            
            if len(citations) > 0:
                citation = citations[0]
                print(f"  Citation type: {type(citation)}")
                print(f"  Citation keys: {list(citation.keys()) if isinstance(citation, dict) else 'Not a dict'}")
                print(f"  Extracted name: {citation.get('extracted_case_name', 'N/A')}")
                print(f"  Citation text: {citation.get('citation', 'N/A')}")
                
                # Check all fields
                print(f"  All citation fields:")
                for key, value in citation.items():
                    if value:  # Only show non-empty fields
                        print(f"    {key}: {value}")
        else:
            print(f"  ❌ API failed: {response.status_code}")
            print(f"  Response: {response.text}")
            
    except Exception as e:
        print(f"  💥 API test failed: {e}")
    
    # Test 3: Large document (async processing)
    print(f"\n🌐 Test 3: API Processing (Large Document - Async)")
    large_text = test_text + "\n\nPadding content. " * 1000
    
    try:
        response = requests.post(
            "http://localhost:8080/casestrainer/api/analyze",
            json={"text": large_text},
            timeout=30
        )
        
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            processing_mode = data.get('metadata', {}).get('processing_mode', 'unknown')
            citations = data.get('citations', [])
            task_id = data.get('task_id')
            job_id = data.get('metadata', {}).get('job_id')
            
            print(f"  Processing mode: {processing_mode}")
            print(f"  Task ID: {task_id}")
            print(f"  Job ID: {job_id}")
            print(f"  Citations found: {len(citations)}")
            
            if processing_mode == 'sync_fallback' and len(citations) > 0:
                citation = citations[0]
                print(f"  Extracted name: {citation.get('extracted_case_name', 'N/A')}")
                print(f"  Citation text: {citation.get('citation', 'N/A')}")
            elif task_id or job_id:
                print("  🔄 Async processing - would need to poll for results")
        
    except Exception as e:
        print(f"  💥 Large document test failed: {e}")

def check_processing_paths():
    """Check which processing paths are being used."""
    
    print(f"\n🛤️ Processing Path Analysis")
    print("=" * 60)
    
    # Check what the Vue API endpoint is actually calling
    print("📋 Vue API Endpoint Analysis:")
    print("  The API should be calling UnifiedInputProcessor")
    print("  Which should call UnifiedCitationProcessorV2 for immediate processing")
    print("  Or queue to process_citation_task_direct for async processing")
    print()
    
    # Check if there are any conversion issues
    print("🔄 Potential Issues:")
    print("  1. CitationResult objects not being converted to dicts properly")
    print("  2. Name extraction happening but being lost in conversion")
    print("  3. Different processing paths using different processors")
    print("  4. Async processing using different logic than direct processing")

def main():
    """Run detailed API vs direct comparison."""
    test_api_vs_direct_detailed()
    check_processing_paths()

if __name__ == "__main__":
    main()
