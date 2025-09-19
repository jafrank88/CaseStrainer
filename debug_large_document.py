#!/usr/bin/env python3
"""
Debug large document processing to see why sync fallback isn't finding citations.
"""

import requests
import json

def test_large_document_debug():
    """Test large document with debugging."""
    
    # Create a large document with known citations
    base_text = """
    In State v. Johnson, 160 Wn.2d 500, 158 P.3d 677 (2007), the court established important precedent.
    The decision in City of Seattle v. Williams, 170 Wn.2d 200, 240 P.3d 1055 (2010) further clarified the law.
    See also Brown v. State, 180 Wn.2d 300, 320 P.3d 800 (2014) and Davis v. County, 190 Wn.2d 400, 400 P.3d 900 (2017).
    """
    
    # Make it large enough to trigger async processing
    large_text = base_text + "\n\nAdditional legal content. " * 2000
    
    print(f"📄 Testing large document ({len(large_text)} characters)")
    print(f"📝 Base citations in text: State v. Johnson, City of Seattle v. Williams, Brown v. State, Davis v. County")
    
    try:
        response = requests.post(
            "http://localhost:8080/casestrainer/api/analyze",
            json={"text": large_text},
            timeout=60
        )
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"🔍 Response keys: {list(data.keys())}")
            print(f"📈 Success: {data.get('success')}")
            print(f"📝 Message: {data.get('message')}")
            print(f"🔧 Processing mode: {data.get('metadata', {}).get('processing_mode')}")
            print(f"📊 Citations found: {len(data.get('citations', []))}")
            print(f"🔗 Clusters found: {len(data.get('clusters', []))}")
            
            if data.get('task_id'):
                print(f"🆔 Task ID: {data['task_id']}")
            
            # Print first few citations if any
            citations = data.get('citations', [])
            if citations:
                print("\n📋 First few citations:")
                for i, citation in enumerate(citations[:3]):
                    print(f"  {i+1}. {citation.get('citation', 'N/A')} - {citation.get('extracted_case_name', 'N/A')}")
            else:
                print("❌ No citations found")
                
                # Check if there's error information
                if 'error' in data:
                    print(f"🚨 Error: {data['error']}")
                
                # Check metadata for clues
                metadata = data.get('metadata', {})
                if metadata:
                    print(f"🔍 Metadata: {json.dumps(metadata, indent=2)}")
        else:
            print(f"❌ Request failed: {response.text}")
            
    except Exception as e:
        print(f"💥 Test failed: {e}")

if __name__ == "__main__":
    test_large_document_debug()
