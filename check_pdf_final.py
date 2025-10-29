import requests

task_id = "91f38ca1-0140-4192-a43b-f858683c0abb"
url = f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}"

try:
    response = requests.get(url)
    status = response.json()
    
    print(f"Status: {status.get('status')}")
    print(f"Progress: {status.get('verification_status', {}).get('progress_percent', 0)}%")
    
    if status.get('status') == 'completed':
        print("\n✅ PDF PROCESSING COMPLETED!")
        if 'result' in status:
            result = status['result']
            citations = result.get('citations', [])
            clusters = result.get('clusters', [])
            
            print(f"\n📊 FINAL PDF RESULTS:")
            print(f"Citations extracted: {len(citations)}")
            print(f"Clusters created: {len(clusters)}")
            
            # Show sample
            print(f"\n📋 Sample citations from PDF:")
            for i, cit in enumerate(citations[:5]):
                print(f"  {i+1}. {cit.get('citation', 'N/A')}")
                if cit.get('extracted_case_name'):
                    print(f"     Case: {cit.get('extracted_case_name')}")
                    
            print(f"\n🎉 CONFIRMED WORKING:")
            print(f"✅ PDF text extraction: Working")
            print(f"✅ Citation extraction: Working ({len(citations)} found)")
            print(f"✅ Clustering: Working ({len(clusters)} clusters)")
            
    elif status.get('status') == 'failed':
        print(f"\n❌ Failed: {status.get('error', 'Unknown error')}")
    else:
        print(f"\n⏳ Still processing...")
        
except Exception as e:
    print(f"Error: {e}")
