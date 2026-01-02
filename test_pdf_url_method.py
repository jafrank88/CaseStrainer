#!/usr/bin/env python3
"""
Test PDF using URL method (file://) to avoid async issues
"""

import requests
import json
import time
import os

def test_pdf_via_url():
    """Test PDF processing via URL method"""
    
    pdf_path = r"D:\dev\casestrainer\1031351.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return None
    
    # Convert to file:// URL
    file_url = f"file:///{pdf_path.replace('\\', '/')}"
    
    print("=" * 80)
    print("TESTING PDF VIA URL METHOD")
    print("=" * 80)
    print(f"PDF: {os.path.basename(pdf_path)}")
    print(f"URL: {file_url}")
    print()
    
    base_url = "http://localhost:5000/casestrainer/api"
    
    # Wait for service
    print("⏳ Waiting for service...")
    for i in range(30):
        try:
            response = requests.get(f"{base_url}/health", timeout=2)
            if response.status_code == 200:
                print("✅ Service ready")
                break
        except:
            pass
        time.sleep(1)
    
    # Process via URL
    print("\n📤 Processing PDF via URL...")
    try:
        data = {
            'type': 'url',
            'url': file_url,
            'enable_verification': 'true',
            'force_mode': 'sync'
        }
        
        response = requests.post(f"{base_url}/analyze", json=data, timeout=300)
        
        if response.status_code != 200:
            print(f"❌ Failed: {response.status_code}")
            print(response.text[:500])
            return None
        
        result = response.json()
        
        # Extract citations
        citations = result.get('citations', [])
        if 'result' in result:
            citations = result['result'].get('citations', citations)
        
        print(f"\n✅ Found {len(citations)} citations")
        
        # Quick analysis
        header_count = 0
        matches = 0
        mismatches = 0
        
        for cit in citations[:20]:  # First 20
            extracted = cit.get('extracted_case_name', 'N/A')
            canonical = cit.get('canonical_name', '')
            
            if extracted and extracted != 'N/A':
                extracted_upper = extracted.upper()
                has_et_al = 'ET AL' in extracted_upper
                has_role_word = any(role in extracted_upper for role in ['PETITIONER', 'RESPONDENT'])
                has_no = 'NO.' in extracted_upper or ' NO ' in extracted_upper
                
                if (has_et_al and has_role_word) or (has_role_word and has_no):
                    header_count += 1
                    print(f"  🚨 HEADER: {cit.get('citation', '')} → {extracted}")
            
            if canonical:
                if cit.get('name_mismatch', False):
                    mismatches += 1
                else:
                    matches += 1
        
        print(f"\n📊 Quick Stats (first 20):")
        print(f"  Header contamination: {header_count}")
        print(f"  Matches: {matches}")
        print(f"  Mismatches: {mismatches}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    test_pdf_via_url()

