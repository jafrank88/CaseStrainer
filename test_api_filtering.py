#!/usr/bin/env python3
"""
Test script to verify citation filtering via API endpoint
"""
import requests
import time
import json

API_BASE = "https://wolf.law.uw.edu/casestrainer/api"
PDF_PATH = r"D:\dev\casestrainer\trumpvbarbaracertpet.pdf"

def test_filtering_via_api():
    print("="*80)
    print("TESTING CITATION FILTERING VIA API")
    print("="*80)
    print(f"API Base: {API_BASE}")
    print(f"PDF: {PDF_PATH}")
    print()
    
    # Step 1: Upload PDF
    print("Step 1: Uploading PDF...")
    start_time = time.time()
    
    with open(PDF_PATH, 'rb') as f:
        files = {'file': ('trumpvbarbaracertpet.pdf', f, 'application/pdf')}
        data = {'type': 'file'}
        
        response = requests.post(f"{API_BASE}/analyze", files=files, data=data, timeout=600)
    
    if response.status_code != 200:
        print(f"❌ Upload failed: {response.status_code}")
        print(f"Response: {response.text}")
        return
    
    result = response.json()
    task_id = result.get('task_id')
    
    if not task_id:
        print(f"❌ No task_id in response")
        print(f"Response: {json.dumps(result, indent=2)}")
        return
    
    print(f"✅ Upload successful, task_id: {task_id}")
    print()
    
    # Step 2: Poll for results
    print("Step 2: Polling for results...")
    poll_count = 0
    max_polls = 60  # 5 minutes max
    
    while poll_count < max_polls:
        poll_count += 1
        time.sleep(5)
        
        status_response = requests.get(f"{API_BASE}/task_status/{task_id}", timeout=30)
        
        if status_response.status_code != 200:
            print(f"❌ Status check failed: {status_response.status_code}")
            continue
        
        status_data = status_response.json()
        status = status_data.get('status')
        message = status_data.get('message', '')
        
        elapsed = time.time() - start_time
        print(f"[{poll_count}] Status: {status}, Elapsed: {elapsed:.1f}s - {message}")
        
        if status == 'completed':
            print()
            print("✅ Processing completed!")
            print(f"Total time: {elapsed:.1f}s ({elapsed/60:.1f} minutes)")
            print()
            
            # Step 3: Analyze results
            print("Step 3: Analyzing results...")
            
            citations = status_data.get('citations', [])
            clusters = status_data.get('clusters', [])
            
            print(f"Total citations: {len(citations)}")
            print(f"Total clusters: {len(clusters)}")
            print()
            
            # Check for filtered types
            short_forms = []
            id_cites = []
            supra_cites = []
            unknown_cites = []
            statute_cites = []
            
            for cite in citations:
                ct = cite.get('citation', '')
                if ' at ' in ct:
                    short_forms.append(ct)
                elif ct.lower() in ['id.', 'ibid.']:
                    id_cites.append(ct)
                elif 'supra' in ct.lower():
                    supra_cites.append(ct)
                elif 'UnknownCitation' in ct:
                    unknown_cites.append(ct)
                elif any(p in ct for p in ['Stat.', 'U.S.C.', 'C.F.R.', 'Fed. Reg.', 'Pub. L.']):
                    statute_cites.append(ct)
            
            print("FILTERING RESULTS:")
            print(f"  Short-form (at): {len(short_forms)}")
            print(f"  Id./Ibid.: {len(id_cites)}")
            print(f"  Supra: {len(supra_cites)}")
            print(f"  Unknown: {len(unknown_cites)}")
            print(f"  Statutes: {len(statute_cites)}")
            print()
            
            if short_forms:
                print(f"❌ SHORT-FORM CITATIONS FOUND:")
                for s in short_forms[:5]:
                    print(f"  - {s}")
                if len(short_forms) > 5:
                    print(f"  ... and {len(short_forms) - 5} more")
                print()
            
            if id_cites:
                print(f"❌ ID CITATIONS FOUND:")
                for s in id_cites[:5]:
                    print(f"  - {s}")
                print()
            
            if supra_cites:
                print(f"❌ SUPRA CITATIONS FOUND:")
                for s in supra_cites[:5]:
                    print(f"  - {s}")
                print()
            
            if unknown_cites:
                print(f"❌ UNKNOWN CITATIONS FOUND:")
                for s in unknown_cites[:5]:
                    print(f"  - {s}")
                print()
            
            if statute_cites:
                print(f"❌ STATUTE CITATIONS FOUND:")
                for s in statute_cites[:5]:
                    print(f"  - {s}")
                print()
            
            # Show valid citations
            valid = len(citations) - len(short_forms) - len(id_cites) - len(supra_cites) - len(unknown_cites) - len(statute_cites)
            print(f"✅ VALID CASE CITATIONS: {valid}")
            
            if valid > 0:
                print("\nSample valid citations:")
                count = 0
                for cite in citations:
                    ct = cite.get('citation', '')
                    if ' at ' not in ct and ct.lower() not in ['id.', 'ibid.'] and 'supra' not in ct.lower() and 'UnknownCitation' not in ct and not any(p in ct for p in ['Stat.', 'U.S.C.', 'C.F.R.']):
                        print(f"  - {ct}")
                        count += 1
                        if count >= 10:
                            break
            
            print()
            print("="*80)
            if short_forms or id_cites or supra_cites or unknown_cites or statute_cites:
                print("⚠️  FILTERING NOT WORKING - Non-case citations present")
            else:
                print("✅ FILTERING WORKING CORRECTLY")
            print("="*80)
            
            return
        
        elif status == 'failed':
            print(f"❌ Processing failed: {message}")
            return
    
    print(f"❌ Timeout after {max_polls} polls")

if __name__ == "__main__":
    test_filtering_via_api()
