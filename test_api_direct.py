import requests
import json
import time

# Disable SSL warnings for localhost
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Test the API endpoint
url = "https://localhost/casestrainer/api/analyze"

with open("test_all_fixes_async.txt", "rb") as f:
    files = {"file": ("test_all_fixes_async.txt", f, "text/plain")}
    data = {
        "type": "file",
        "client_request_id": f"cascade-test-{int(time.time())}"
    }
    
    print("📤 Uploading to API...")
    response = requests.post(url, files=files, data=data, verify=False)
    
    print(f"\n✅ Response Status: {response.status_code}")
    
    result = response.json()
    print(f"\n📊 Response Keys: {result.keys()}")
    
    if "task_id" in result:
        task_id = result["task_id"]
        print(f"🆔 Task ID: {task_id}")
        
        # Poll for results
        status_url = f"https://localhost/casestrainer/api/task-status/{task_id}"
        
        for i in range(30):
            time.sleep(2)
            status_resp = requests.get(status_url, verify=False)
            status_data = status_resp.json()
            
            print(f"\n⏳ Poll {i+1}: Status = {status_data.get('status', 'unknown')}")
            
            if status_data.get("status") == "completed":
                print("\n✅ COMPLETED!")
                
                # Check clusters
                result = status_data.get("result", {})
                clusters = result.get("clusters", [])
                citations = result.get("citations", [])
                
                print(f"\n📚 Clusters: {len(clusters)}")
                print(f"📝 Citations: {len(citations)}")
                
                # Show cluster details
                for idx, cluster in enumerate(clusters, 1):
                    size = cluster.get("size", 0)
                    case_name = cluster.get("case_name", "Unknown")
                    members = cluster.get("cluster_members", [])
                    print(f"\nCluster {idx}: {case_name}")
                    print(f"  Size: {size}")
                    print(f"  Members: {members}")
                
                # Save full result
                with open("api_test_full_result.json", "w") as outf:
                    json.dump(status_data, outf, indent=2)
                print("\n💾 Full result saved to api_test_full_result.json")
                
                break
            elif status_data.get("status") == "failed":
                print(f"\n❌ FAILED: {status_data.get('error', 'Unknown error')}")
                break
    else:
        print(f"\n❌ No task_id in response!")
        print(json.dumps(result, indent=2))
