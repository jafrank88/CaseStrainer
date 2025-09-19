#!/usr/bin/env python3
"""
Debug API processing to see what's happening
"""

import sys
from pathlib import Path
import requests
import json

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

def main():
    print("🔍 Debugging API Processing")
    print("=" * 50)
    
    # Simple test text with WL citation
    test_text = "In Wyoming v. U.S. Dep't of Interior, 2006 WL 3801910 (D. Wyo. 2006), the court ruled."
    
    print(f"📝 Test text: {test_text}")
    print(f"📏 Text length: {len(test_text)} bytes")
    print()
    
    # Test API call with detailed response
    try:
        print("🌐 Making API call...")
        response = requests.post(
            'http://localhost:5000/casestrainer/api/analyze', 
            data={'text': test_text, 'type': 'text'}, 
            timeout=60
        )
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📊 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"📊 Response JSON:")
                print(json.dumps(result, indent=2))
                
                # Check if citations are in nested result structure
                citations = result.get('citations', [])
                if not citations and 'result' in result:
                    citations = result['result'].get('citations', [])
                
                print(f"\n📋 Citations Analysis:")
                print(f"  Total citations: {len(citations)}")
                
                if citations:
                    for i, citation in enumerate(citations, 1):
                        print(f"  Citation {i}:")
                        print(f"    Text: {citation.get('citation', 'N/A')}")
                        print(f"    Source: {citation.get('source', 'N/A')}")
                        print(f"    Method: {citation.get('method', 'N/A')}")
                else:
                    print("  ❌ No citations found")
                    
                # Check for errors in response
                if 'error' in result:
                    print(f"  ❌ Error in response: {result['error']}")
                    
                # Check metadata
                metadata = result.get('metadata', {})
                if metadata:
                    print(f"\n📊 Metadata:")
                    for key, value in metadata.items():
                        print(f"    {key}: {value}")
                        
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error: {e}")
                print(f"Raw response: {response.text}")
                
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Request error: {e}")
        import traceback
        traceback.print_exc()
    
    # Also test direct processing
    print(f"\n" + "=" * 50)
    print("🧪 Testing Direct Processing")
    print("=" * 50)
    
    try:
        from unified_sync_processor import UnifiedSyncProcessor
        
        processor = UnifiedSyncProcessor()
        result = processor.process_text_unified(test_text)
        
        print(f"📊 Direct Processing Result:")
        print(f"  Success: {result.get('success', False)}")
        print(f"  Citations: {len(result.get('citations', []))}")
        
        citations = result.get('citations', [])
        if citations:
            for i, citation in enumerate(citations, 1):
                citation_text = citation.get('citation') if isinstance(citation, dict) else str(citation)
                print(f"    {i}. {citation_text}")
        else:
            print("  ❌ No citations found in direct processing")
            
        if 'error' in result:
            print(f"  ❌ Error: {result['error']}")
            
    except Exception as e:
        print(f"❌ Direct processing error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
