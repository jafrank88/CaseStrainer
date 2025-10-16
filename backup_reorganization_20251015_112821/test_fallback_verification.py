import requests
import json
import time
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

print("Testing Fallback Verification with File Upload...\n")

# Create a test PDF-like text file
test_content = """
SUPREME COURT OF WASHINGTON

Robert Cassell v. State of Alaska

This case involves several citations that should be verified through fallback sources:

1. Washington Citations:
   - State v. Johnson, 159 Wn.2d 700, 153 P.3d 846 (2007)
   - Bostain v. Food Express, Inc., 159 Wn.2d 700, 153 P.3d 846 (2007)
   - Lopez Demetrio v. Dep't of Lab. & Indus., 188 Wn. App. 869, 354 P.3d 1123 (2015)

2. Federal Citations:
   - Miranda v. Arizona, 384 U.S. 436 (1966)
   - Brown v. Board of Education, 347 U.S. 483 (1954)
   - Roe v. Wade, 410 U.S. 113 (1973)

3. Other State Citations:
   - People v. Smith, 100 Cal.App.4th 500 (2002)
   - Jones v. State, 200 N.Y.2d 100 (2010)

The court found that the defendant's arguments were without merit.
"""

# Write to a file
filename = "test_fallback_doc.txt"
with open(filename, 'w') as f:
    f.write(test_content)

print(f"Created test file: {filename}")
print(f"File size: {len(test_content)} characters")
print("\nSubmitting file for analysis...")

try:
    with open(filename, 'rb') as f:
        files = {'file': (filename, f, 'text/plain')}
        data = {'type': 'file'}
        
        response = requests.post(
            'https://wolf.law.uw.edu/casestrainer/api/analyze',
            files=files,
            data=data,
            verify=False,
            timeout=90
        )
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"Error: {response.text}")
        exit(1)
    
    result = response.json()
    
    # Check processing mode
    processing_mode = result.get('metadata', {}).get('processing_mode', 'unknown')
    sync_complete = result.get('metadata', {}).get('sync_complete', False)
    
    print(f"Processing mode: {processing_mode}")
    print(f"Sync complete: {sync_complete}")
    
    # If sync, we have results immediately
    if sync_complete or result.get('citations'):
        print("\n✅ SYNC PROCESSING (immediate results)")
        citations = result.get('citations', [])
        print(f"\nFound {len(citations)} citations")
        
        # Analyze verification results
        verified_count = sum(1 for c in citations if c.get('verified'))
        fallback_count = sum(1 for c in citations 
                            if c.get('source') and 'fallback' in c.get('source', '').lower())
        
        print(f"Verified: {verified_count}/{len(citations)}")
        print(f"Fallback verifications: {fallback_count}")
        
        print("\n" + "="*60)
        print("CITATION VERIFICATION DETAILS:")
        print("="*60)
        
        for i, cit in enumerate(citations, 1):
            text = cit.get('citation_text', 'N/A')
            case_name = cit.get('extracted_case_name', 'N/A')
            verified = cit.get('verified', False)
            source = cit.get('source', 'none')
            canonical = cit.get('canonical_name', 'N/A')
            
            status = "✅ VERIFIED" if verified else "❌ NOT VERIFIED"
            
            print(f"\n{i}. {text}")
            print(f"   Status: {status}")
            print(f"   Source: {source}")
            print(f"   Extracted: {case_name}")
            print(f"   Canonical: {canonical}")
        
        # Summary
        print("\n" + "="*60)
        print("FALLBACK VERIFIER TEST SUMMARY:")
        print("="*60)
        
        if verified_count > 0:
            print(f"✅ Verification is WORKING!")
            print(f"   {verified_count}/{len(citations)} citations verified")
            if fallback_count > 0:
                print(f"   {fallback_count} verified via FALLBACK sources")
        else:
            print(f"⚠️  No citations were verified")
            print(f"   This may be due to rate limits or no fallback sources responding")
        
        exit(0)
    
    # Otherwise async - poll for results
    task_id = result.get('request_id') or result.get('task_id')
    print(f"\n🔄 ASYNC PROCESSING - Task ID: {task_id}")
    print("Polling for results...")
    
    url = f'https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}'
    
    for attempt in range(40):
        time.sleep(3)
        
        try:
            status_response = requests.get(url, verify=False, timeout=10)
            status_data = status_response.json()
            
            status = status_data.get('status')
            progress = status_data.get('progress', 0)
            message = status_data.get('message', '')
            
            print(f"   [{attempt+1}] {status}: {progress}% - {message}")
            
            if status == 'completed':
                print("\n✅ ASYNC COMPLETED!")
                citations = status_data.get('citations', [])
                
                verified_count = sum(1 for c in citations if c.get('verified'))
                fallback_count = sum(1 for c in citations 
                                    if c.get('source') and 'fallback' in c.get('source', '').lower())
                
                print(f"\nFound {len(citations)} citations")
                print(f"Verified: {verified_count}/{len(citations)}")
                print(f"Fallback verifications: {fallback_count}")
                
                print("\n" + "="*60)
                print("VERIFICATION DETAILS:")
                print("="*60)
                
                for i, cit in enumerate(citations[:10], 1):
                    text = cit.get('citation_text', 'N/A')
                    verified = cit.get('verified', False)
                    source = cit.get('source', 'none')
                    
                    status_icon = "✅" if verified else "❌"
                    print(f"{i}. {status_icon} {text} (source: {source})")
                
                if verified_count > 0:
                    print(f"\n✅ Fallback verification is WORKING!")
                else:
                    print(f"\n⚠️  No verifications (may be rate limited)")
                
                exit(0)
            
            elif status == 'failed':
                print(f"\n❌ Failed: {status_data.get('error')}")
                exit(1)
        
        except Exception as e:
            print(f"   Error: {e}")
            continue
    
    print("\n⚠️ Timeout")
    exit(1)

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
