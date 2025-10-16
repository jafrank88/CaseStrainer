import requests
import json
import time

task_id = "306e263d-8866-45af-a372-5d9b2bef2012"

print(f"Checking status for task: {task_id}")

for i in range(30):  # Check for up to 60 seconds
    response = requests.get(f'http://localhost:5000/casestrainer/api/task/{task_id}/status')
    
    if response.status_code == 200:
        result = response.json()
        status = result.get('status', 'unknown')
        message = result.get('message', '')
        
        print(f"[{i+1}] Status: {status} - {message}")
        
        if status == 'completed':
            # Save full result
            with open('final_result.json', 'w') as f:
                json.dump(result, f, indent=2)
            
            # Print summary
            data = result.get('result', {})
            clusters = data.get('clusters', [])
            citations = data.get('citations', [])
            
            print(f"\n✅ PROCESSING COMPLETE!")
            print(f"Total Citations: {len(citations)}")
            print(f"Total Clusters: {len(clusters)}")
            
            # Check canonical data
            clusters_with_canonical = 0
            for cluster in clusters:
                if cluster.get('canonical_name'):
                    clusters_with_canonical += 1
                    if clusters_with_canonical <= 5:  # Show first 5
                        print(f"\n✅ Cluster has canonical data:")
                        print(f"   Name: {cluster.get('canonical_name')}")
                        print(f"   Date: {cluster.get('canonical_date')}")
            
            print(f"\n📊 FINAL RESULT: {clusters_with_canonical}/{len(clusters)} clusters have canonical data")
            
            if clusters_with_canonical > 3:
                print("🎉🎉🎉 FIX WORKED! More than 3 clusters have canonical data!")
            elif clusters_with_canonical == 3:
                print("⚠️  Still only 3 clusters - same as before fix")
            else:
                print("❌ Less than 3 clusters have canonical data")
            
            break
            
        elif status == 'failed':
            print(f"\n❌ Task failed: {result.get('error')}")
            break
    else:
        print(f"Error checking status: {response.status_code}")
        break
    
    time.sleep(2)
else:
    print("\n⏱️  Timeout waiting for task completion")
