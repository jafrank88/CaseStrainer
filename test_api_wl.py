#!/usr/bin/env python3
"""
Test WL citation detection via API
"""

import requests
import json
import os

def test_wl_via_api():
    """Test WL citation detection using the actual API."""
    
    print("🌐 Testing WL Detection via API")
    print("=" * 50)
    
    # Test with sample text containing WL citations
    test_text = """
    In Wyoming v. U.S. Dep't of Interior, 2006 WL 3801910 (D. Wyo. 2006), the court ruled that evidence 
    regarding the defendant's prior bad acts was inadmissible. See also Johnson v. State, 2018 WL 3037217 
    (Wyo. 2018), where the court held that motions in limine are proper procedural tools.
    """
    
    # Test text analysis endpoint
    try:
        url = "http://localhost:5000/api/analyze"
        
        # Test with text
        print("📝 Testing text analysis...")
        data = {
            'text': test_text,
            'type': 'text'
        }
        
        response = requests.post(url, data=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('citations', [])
            wl_citations = [c for c in citations if 'WL' in c.get('citation', '')]
            
            print(f"✅ API Response: {response.status_code}")
            print(f"   Total citations: {len(citations)}")
            print(f"   WL citations: {len(wl_citations)}")
            
            if wl_citations:
                print("   WL Citations found:")
                for citation in wl_citations:
                    print(f"     - {citation.get('citation')}")
            else:
                print("   ❌ No WL citations found")
                print("   All citations found:")
                for citation in citations:
                    print(f"     - {citation.get('citation')}")
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing API: {e}")

def test_pdf_via_api():
    """Test PDF processing via API."""
    
    print(f"\n📄 Testing PDF via API...")
    
    pdf_path = r"D:\dev\casestrainer\gov.uscourts.wyd.64014.141.0_1.pdf"
    
    if not os.path.exists(pdf_path):
        print("❌ PDF file not found")
        return
    
    try:
        url = "http://localhost:5000/api/analyze"
        
        with open(pdf_path, 'rb') as f:
            files = {'file': ('test.pdf', f, 'application/pdf')}
            data = {'type': 'file'}
            
            response = requests.post(url, files=files, data=data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('citations', [])
            wl_citations = [c for c in citations if 'WL' in c.get('citation', '')]
            
            print(f"✅ PDF API Response: {response.status_code}")
            print(f"   Total citations: {len(citations)}")
            print(f"   WL citations: {len(wl_citations)}")
            
            if wl_citations:
                print("   ✅ PDF processing found WL citations:")
                for citation in wl_citations:
                    print(f"     - {citation.get('citation')}")
            else:
                print("   ❌ PDF processing found NO WL citations")
                print("   All citations found:")
                for citation in citations[:10]:  # Show first 10
                    print(f"     - {citation.get('citation')}")
                if len(citations) > 10:
                    print(f"     ... and {len(citations) - 10} more")
        else:
            print(f"❌ PDF API Error: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing PDF API: {e}")

def main():
    print("🔍 WL Citation API Testing")
    print("=" * 50)
    print("Testing if CaseStrainer API can detect WL citations...")
    print()
    
    test_wl_via_api()
    test_pdf_via_api()
    
    print(f"\n" + "=" * 50)
    print("📋 Summary:")
    print("If the API finds WL citations in text but not in PDF,")
    print("then the issue is in PDF text extraction.")
    print("If it finds neither, the issue is in citation processing.")

if __name__ == "__main__":
    main()
