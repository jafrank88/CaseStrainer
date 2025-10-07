"""
Direct backend test - bypasses external URL issues
"""
import requests
import json
import time

class DirectBackendTest:
    def __init__(self):
        self.api_url = "http://localhost:5000/casestrainer/api/analyze"
        self.pdf_url = "https://www.courts.wa.gov/opinions/pdf/1033940.pdf"
        self.issues = []
        
    def test_backend(self):
        print("=" * 80)
        print("TESTING BACKEND DIRECTLY (LOCALHOST)")
        print("=" * 80)
        
        # Test with text first (should work)
        print("\n1. Testing with text (should work)...")
        text_payload = {
            "type": "text",
            "text": "See Lopez Demetrio, 183 Wash.2d 649, 355 P.3d 258 (2015). See also Broughton Lumber Co. v. BNSF Ry. Co., 174 Wash.2d 619, 278 P.3d 173 (2012)."
        }
        
        try:
            response = requests.post(self.api_url, json=text_payload, timeout=30)
            data = response.json()
            
            print(f"   Status: {response.status_code}")
            print(f"   Success: {data.get('success')}")
            print(f"   Citations: {len(data.get('citations', []))}")
            print(f"   Clusters: {len(data.get('clusters', []))}")
            
            # Check clustering
            citations = data.get('citations', [])
            with_cluster_id = [c for c in citations if c.get('cluster_id')]
            print(f"   Citations with cluster_id: {len(with_cluster_id)}")
            
            if len(data.get('clusters', [])) > 0:
                print("   ✅ TEXT PROCESSING + CLUSTERING WORKING!")
            else:
                print("   ❌ Clustering not working")
                self.issues.append("Text clustering not working")
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            self.issues.append(f"Text processing failed: {e}")
        
        # Test with PDF URL (may have issues)
        print("\n2. Testing with PDF URL...")
        pdf_payload = {
            "type": "url",
            "url": self.pdf_url
        }
        
        try:
            response = requests.post(self.api_url, json=pdf_payload, timeout=120)
            data = response.json()
            
            print(f"   Status: {response.status_code}")
            print(f"   Success: {data.get('success')}")
            
            # Check if async or sync
            task_id = data.get('task_id')
            if task_id:
                print(f"   Processing: ASYNC (task_id: {task_id})")
                # Wait for completion
                status_url = f"http://localhost:5000/casestrainer/api/task_status/{task_id}"
                for i in range(60):
                    time.sleep(2)
                    status_response = requests.get(status_url, timeout=5)
                    status_data = status_response.json()
                    
                    if status_data.get('status') in ['completed', 'failed']:
                        data = status_data
                        break
                    elif i % 5 == 0:
                        progress = status_data.get('progress_data', {}).get('overall_progress', 0)
                        print(f"   Progress: {progress}%")
            else:
                print(f"   Processing: SYNC")
            
            print(f"   Citations: {len(data.get('citations', []))}")
            print(f"   Clusters: {len(data.get('clusters', []))}")
            
            if len(data.get('citations', [])) == 0:
                print("   ⚠️  PDF extraction returning 0 citations (separate issue)")
                self.issues.append("PDF extraction not working")
            else:
                citations = data.get('citations', [])
                with_cluster_id = [c for c in citations if c.get('cluster_id')]
                print(f"   Citations with cluster_id: {len(with_cluster_id)}")
                
                if len(data.get('clusters', [])) > 0:
                    print("   ✅ PDF PROCESSING + CLUSTERING WORKING!")
                else:
                    print("   ⚠️  PDF processed but no clusters")
                    
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            self.issues.append(f"PDF processing failed: {e}")
        
        # Summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        if not self.issues:
            print("\n🎉 ALL TESTS PASSED!")
            print("   - Text processing: ✅")
            print("   - Clustering: ✅")
            print("   - PDF processing: ✅")
        else:
            print(f"\n⚠️  FOUND {len(self.issues)} ISSUE(S):")
            for i, issue in enumerate(self.issues, 1):
                print(f"   {i}. {issue}")
        
        print("\n" + "=" * 80)

if __name__ == "__main__":
    tester = DirectBackendTest()
    tester.test_backend()
