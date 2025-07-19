#!/usr/bin/env python3
"""
Test the /analyze endpoint (the one the frontend actually calls)
"""

import requests
import json
import difflib
import sys

# Import the unified processor for direct module call
sys.path.insert(0, './src')
from unified_citation_processor_v2 import extract_citations_unified

def test_analyze_endpoint():
    """Test the /analyze endpoint that the frontend calls"""
    
    url = "http://localhost:5000/casestrainer/api/analyze"
    
    # Test data with Washington citation
    test_data = {
        "type": "text",
        "text": "Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions",
        "citations": ["200 Wn.2d 72, 514 P.3d 643"]
    }
    
    print("[TEST] Testing /analyze endpoint (frontend endpoint)...")
    print(f"URL: {url}")
    print(f"Request data: {json.dumps(test_data, indent=2)}")
    print("-" * 60)
    
    try:
        response = requests.post(url, json=test_data, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS! API Response:")
            print(json.dumps(result, indent=2))
            
            # Check if we got real extracted data
            if 'citations' in result and result['citations']:
                citation_result = result['citations'][0]
                print("[ANALYSIS] EXTRACTION ANALYSIS:")
                print(f"Extracted case name: '{citation_result.get('extracted_case_name', 'N/A')}'")
                print(f"Extracted date: '{citation_result.get('extracted_date', 'N/A')}'")
                print(f"Canonical name: '{citation_result.get('canonical_name', 'N/A')}'")
                print(f"Canonical date: '{citation_result.get('canonical_date', 'N/A')}'")
                print(f"Case name: '{citation_result.get('case_name', 'N/A')}'")
                print(f"Verified: '{citation_result.get('verified', 'N/A')}'")
                print(f"Source: '{citation_result.get('source', 'N/A')}'")
                print(f"Method: '{citation_result.get('method', 'N/A')}'")
                
                # Check if we got real extraction vs N/A
                extracted_name = citation_result.get('extracted_case_name', 'N/A')
                extracted_date = citation_result.get('extracted_date', 'N/A')
                
                if extracted_name != 'N/A' and extracted_date != 'N/A':
                    print("[SUCCESS] /analyze ENDPOINT NOW WORKING WITH EXTRACTED FIELDS!")
                else:
                    print("[WARN] Extraction still returned N/A - may need investigation")
            else:
                print("[WARN] No citations found in response")
        else:
            print(f"[ERROR] {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("[ERROR] CONNECTION ERROR: Flask server not running or not accessible")
        print("Make sure the Flask server is running on localhost:5000")
    except Exception as e:
        print(f"❌ ERROR: {e}")

def ab_compare_analyze():
    """Compare backend API and direct module output for the same input."""
    url = "http://localhost:5001/casestrainer/api/analyze"
    test_data = {
        "type": "text",
        "text": "A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep’t of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)",
        "citations": []
    }
    print("\n=== [A] Backend API ===")
    try:
        response = requests.post(url, json=test_data, timeout=30)
        api_result = response.json() if response.status_code == 200 else response.text
        with open("api_result.json", "w", encoding="utf-8") as f:
            json.dump(api_result, f, indent=2, ensure_ascii=False)
        print("API result saved to api_result.json")
    except Exception as e:
        print(f"API call failed: {e}")
        api_result = None

    print("\n=== [B] Direct Module ===")
    try:
        from unified_citation_processor_v2 import ProcessingConfig
        # Use eyecite with Ahocorasick tokenizer, do not use hyperscan/hypertokenizer
        config = ProcessingConfig(use_eyecite=True)
        # If the processor supports tokenizer selection, set it here (pseudo-code):
        # config.tokenizer = 'ahocorasick'
        module_result = extract_citations_unified(test_data["text"], config=config)
        # Convert dataclass objects to dicts for JSON
        module_result_dict = [r.__dict__ for r in module_result]
        with open("module_result.json", "w", encoding="utf-8") as f:
            json.dump(module_result_dict, f, indent=2, ensure_ascii=False)
        print("Module result saved to module_result.json")
    except Exception as e:
        print(f"Module call failed: {e}")
        module_result_dict = None

    # Print diff if both succeeded
    if api_result and module_result_dict:
        api_str = json.dumps(api_result, indent=2, ensure_ascii=False)
        module_str = json.dumps(module_result_dict, indent=2, ensure_ascii=False)
        diff = list(difflib.unified_diff(api_str.splitlines(), module_str.splitlines(), fromfile='API', tofile='Module', lineterm=''))
        print("\n=== Unified Diff (API vs Module) ===")
        if diff:
            for line in diff:
                print(line)
        else:
            print("No differences found!")

if __name__ == "__main__":
    test_analyze_endpoint()
    ab_compare_analyze() 