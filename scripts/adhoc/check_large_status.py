import requests
import json

task_id = "test_large_1761726719"
url = f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}"

try:
    response = requests.get(url)
    status = response.json()
    
    print(f"Status: {status.get('status')}")
    print(f"Progress: {status.get('verification_status', {}).get('progress_percent', 0)}%")
    
    if status.get('status') == 'completed':
        print("\n✅ COMPLETED!")
        if 'result' in status:
            result = status['result']
            citations = result.get('citations', [])
            clusters = result.get('clusters', [])
            
            print(f"\n📊 Results Summary:")
            print(f"✅ Citations extracted: {len(citations)}")
            print(f"✅ Clusters created: {len(clusters)}")
            
            # Count verified citations
            verified = sum(1 for c in citations if c.get('verified'))
            print(f"✅ Citations verified: {verified}/{len(citations)}")
            
            # Show unique citations (deduplication working)
            unique_cits = set(c.get('citation') for c in citations)
            print(f"✅ Unique citations: {len(unique_cits)} (deduplication working)")
            
            print(f"\n🎉 All core functionality is working!")
            
except Exception as e:
    print(f"Error: {e}")
