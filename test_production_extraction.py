#!/usr/bin/env python3
"""
Test script to verify extraction functionality in production environment.
Tests the production deployment at https://wolf.law.uw.edu/casestrainer/
"""

import requests
import json
import time
from typing import Dict, Any

def test_production_extraction():
    """Test extraction functionality in production."""
    
    # Production URL
    base_url = "https://wolf.law.uw.edu/casestrainer/api"
    
    # Test citation that should extract both name and date
    test_citation = "Punx v Smithers, 123 Wash. 2d 456, 789 P.2d 123 (1990)"
    
    print("🧪 Testing Extraction in Production Environment")
    print("=" * 60)
    print(f"Production URL: {base_url}")
    print(f"Test citation: {test_citation}")
    print()
    
    # Test data
    test_data = {
        "type": "text",
        "text": test_citation
    }
    
    try:
        print("📡 Sending request to production...")
        response = requests.post(f"{base_url}/analyze", json=test_data, timeout=30)
        
        print(f"✅ Response Status: {response.status_code}")
        print(f"📊 Response Size: {len(response.text)} characters")
        
        if response.status_code == 200:
            result = response.json()
            
            print("\n📋 Production Response Analysis:")
            print("-" * 40)
            
            # Check if we got citations
            citations = result.get('citations', [])
            print(f"📄 Found {len(citations)} citations")
            
            # Analyze each citation
            for i, citation in enumerate(citations):
                print(f"\n🔍 Citation {i + 1}:")
                print(f"   Citation: {citation.get('citation', 'N/A')}")
                print(f"   Extracted Case Name: {citation.get('extracted_case_name', 'N/A')}")
                print(f"   Extracted Date: {citation.get('extracted_date', 'N/A')}")
                print(f"   Canonical Name: {citation.get('canonical_name', 'N/A')}")
                print(f"   Canonical Date: {citation.get('canonical_date', 'N/A')}")
                print(f"   Verified: {citation.get('verified', 'N/A')}")
                
                # Check if extraction worked
                extracted_name = citation.get('extracted_case_name')
                extracted_date = citation.get('extracted_date')
                
                if extracted_name and extracted_name != 'N/A':
                    print(f"   ✅ Extracted name: {extracted_name}")
                else:
                    print(f"   ❌ No extracted name found")
                    
                if extracted_date and extracted_date != 'N/A':
                    print(f"   ✅ Extracted date: {extracted_date}")
                else:
                    print(f"   ❌ No extracted date found")
            
            # Summary
            print(f"\n📈 Summary:")
            print(f"   Total citations: {len(citations)}")
            print(f"   Citations with extracted names: {sum(1 for c in citations if c.get('extracted_case_name') and c.get('extracted_case_name') != 'N/A')}")
            print(f"   Citations with extracted dates: {sum(1 for c in citations if c.get('extracted_date') and c.get('extracted_date') != 'N/A')}")
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def test_production_frontend():
    """Test if the production frontend is accessible."""
    
    print("\n🌐 Testing Production Frontend Access")
    print("=" * 40)
    
    try:
        response = requests.get("https://wolf.law.uw.edu/casestrainer/", timeout=10)
        print(f"Frontend Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Frontend is accessible")
            print("🌐 You can test extraction manually at: https://wolf.law.uw.edu/casestrainer/")
        else:
            print(f"❌ Frontend error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Frontend access error: {e}")

if __name__ == "__main__":
    test_production_extraction()
    test_production_frontend()
    
    print("\n🎯 Next Steps:")
    print("1. If extraction works in production, the fix is deployed successfully")
    print("2. If extraction doesn't work, we need to deploy the updated code")
    print("3. Test manually at: https://wolf.law.uw.edu/casestrainer/") 