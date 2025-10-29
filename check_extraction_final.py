import requests

task_id = "ebbfed49-770c-447d-871f-bde4808777aa"
url = f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}"

try:
    response = requests.get(url)
    status = response.json()
    
    print(f"Status: {status.get('status')}")
    print(f"Progress: {status.get('verification_status', {}).get('progress_percent', 0)}%")
    
    if status.get('status') == 'completed':
        print("\n✅ EXTRACTION COMPLETED!")
        if 'result' in status:
            result = status['result']
            citations = result.get('citations', [])
            clusters = result.get('clusters', [])
            
            print(f"\n📊 FINAL RESULTS:")
            print(f"Citations extracted: {len(citations)}")
            print(f"Expected (manual): 34")
            print(f"Clusters created: {len(clusters)}")
            
            print(f"\n📋 All citations extracted:")
            for i, cit in enumerate(citations):
                print(f"  {i+1}. {cit.get('citation', 'N/A')}")
                if cit.get('extracted_case_name'):
                    case_name = cit.get('extracted_case_name')
                    if len(case_name) > 60:
                        case_name = case_name[:57] + "..."
                    print(f"     Case: {case_name}")
                    
            print(f"\n🎯 ACCURACY ASSESSMENT:")
            accuracy = len(citations) / 34 * 100
            print(f"Extraction accuracy: {accuracy:.1f}% ({len(citations)}/34)")
            
            with_names = sum(1 for c in citations if c.get('extracted_case_name'))
            print(f"Case name extraction: {with_names}/{len(citations)} ({with_names/len(citations)*100:.1f}%)")
            
            if accuracy >= 90:
                print("✅ EXTRACTION: EXCELLENT")
            elif accuracy >= 70:
                print("✅ EXTRACTION: GOOD")
            elif accuracy >= 50:
                print("⚠️  EXTRACTION: FAIR")
            else:
                print("❌ EXTRACTION: POOR")
                
    elif status.get('status') == 'failed':
        print(f"\n❌ Failed: {status.get('error', 'Unknown error')}")
    else:
        print(f"\n⏳ Status: {status.get('status')}")
        
except Exception as e:
    print(f"Error: {e}")
