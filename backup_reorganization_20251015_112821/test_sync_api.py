"""
Test the API directly with 1033940.pdf using force_mode='sync'
"""
import requests
import json
import time

# API endpoint
API_URL = "https://wolf.law.uw.edu/casestrainer/api/analyze"

# PDF file path
PDF_FILE = "1033940.pdf"

print("🔍 Testing API with 1033940.pdf in SYNC mode...")
print(f"API Endpoint: {API_URL}")
print(f"PDF File: {PDF_FILE}")
print("")

try:
    # Read the PDF file
    with open(PDF_FILE, 'rb') as f:
        files = {'file': (PDF_FILE, f, 'application/pdf')}
        
        # Add force_mode parameter
        data = {'force_mode': 'sync'}
        
        print("📤 Sending request...")
        start_time = time.time()
        
        response = requests.post(
            API_URL,
            files=files,
            data=data,
            verify=False,  # Skip SSL verification for local testing
            timeout=300  # 5 minute timeout
        )
        
        elapsed_time = time.time() - start_time
        print(f"✅ Response received in {elapsed_time:.2f} seconds")
        print(f"Status Code: {response.status_code}")
        print("")
        
        if response.status_code == 200:
            result = response.json()
            
            # Save full result to file
            with open('sync_api_test_result.json', 'w', encoding='utf-8') as out:
                json.dump(result, out, indent=2, ensure_ascii=False)
            
            print("✅ SUCCESS! Results saved to: sync_api_test_result.json")
            print("")
            print("📊 SUMMARY:")
            print(f"   Total Citations: {result.get('statistics', {}).get('total_citations', 0)}")
            print(f"   Total Clusters: {result.get('statistics', {}).get('total_clusters', 0)}")
            print(f"   Verified Citations: {result.get('statistics', {}).get('verified_citations', 0)}")
            print(f"   Processing Time: {result.get('statistics', {}).get('processing_time', 0):.2f}s")
            print("")
            
            # Check for Fix #52 diagnostic markers
            print("🔍 Checking for diagnostic markers...")
            citations = result.get('citations', [])
            if citations:
                print(f"   First citation: {citations[0].get('citation', 'N/A')}")
                print(f"   Extracted name: {citations[0].get('extracted_case_name', 'N/A')}")
                print(f"   Canonical name: {citations[0].get('canonical_name', 'N/A')}")
                print(f"   Verified: {citations[0].get('verified', False)}")
            
        else:
            print(f"❌ ERROR: Status {response.status_code}")
            print(response.text)
            
except FileNotFoundError:
    print(f"❌ ERROR: File '{PDF_FILE}' not found!")
    print("Please ensure 1033940.pdf is in the current directory.")
except requests.exceptions.Timeout:
    print("❌ ERROR: Request timed out after 5 minutes")
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

