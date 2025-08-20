#!/usr/bin/env python3
"""
Test script for CaseStrainer Production API
Tests file uploads, URL handling, and text analysis
"""

import requests
import json
import time
import os
from pathlib import Path

class CaseStrainerAPITester:
    """Test the CaseStrainer production API endpoints"""
    
    def __init__(self, base_url="https://wolf.law.uw.edu"):
        self.base_url = base_url
        self.api_base = f"{base_url}/casestrainer/api"
        self.session = requests.Session()
        
        # Configure session for production
        self.session.headers.update({
            'User-Agent': 'CaseStrainer-API-Tester/1.0',
            'Accept': 'application/json'
        })
        
        # Disable SSL verification for testing (only if needed)
        # self.session.verify = False
        
    def test_health_endpoint(self):
        """Test the health endpoint"""
        print("🔍 Testing health endpoint...")
        try:
            response = self.session.get(f"{self.api_base}/health")
            print(f"✅ Health check: {response.status_code}")
            if response.status_code == 200:
                print(f"   Response: {response.json()}")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False
    
    def test_text_analysis(self, text):
        """Test text analysis endpoint"""
        print(f"🔍 Testing text analysis...")
        try:
            data = {
                "type": "text",
                "text": text
            }
            
            response = self.session.post(
                f"{self.api_base}/analyze",
                json=data,
                timeout=30
            )
            
            print(f"✅ Text analysis: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"   Task ID: {result.get('task_id')}")
                print(f"   Status: {result.get('status')}")
                return result.get('task_id')
            else:
                print(f"   Error: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Text analysis failed: {e}")
            return None
    
    def test_file_upload(self, file_path):
        """Test file upload endpoint"""
        print(f"🔍 Testing file upload: {file_path}")
        
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return None
        
        try:
            with open(file_path, 'rb') as f:
                files = {
                    'file': (os.path.basename(file_path), f, 'application/octet-stream'),
                    'type': (None, 'file')
                }
                
                response = self.session.post(
                    f"{self.api_base}/analyze",
                    files=files,
                    timeout=60
                )
            
            print(f"✅ File upload: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"   Task ID: {result.get('task_id')}")
                print(f"   Status: {result.get('status')}")
                return result.get('task_id')
            else:
                print(f"   Error: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ File upload failed: {e}")
            return None
    
    def test_url_analysis(self, url):
        """Test URL analysis endpoint"""
        print(f"🔍 Testing URL analysis: {url}")
        try:
            data = {
                "type": "url",
                "url": url
            }
            
            response = self.session.post(
                f"{self.api_base}/analyze",
                json=data,
                timeout=30
            )
            
            print(f"✅ URL analysis: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"   Task ID: {result.get('task_id')}")
                print(f"   Status: {result.get('status')}")
                return result.get('task_id')
            else:
                print(f"   Error: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ URL analysis failed: {e}")
            return None
    
    def check_task_status(self, task_id):
        """Check the status of a task"""
        print(f"🔍 Checking task status: {task_id}")
        try:
            response = self.session.get(f"{self.api_base}/status/{task_id}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Task status: {result.get('status')}")
                print(f"   Progress: {result.get('progress', 'N/A')}")
                
                if result.get('status') == 'completed':
                    citations = result.get('citations', [])
                    clusters = result.get('clusters', [])
                    print(f"   Citations found: {len(citations)}")
                    print(f"   Clusters created: {len(clusters)}")
                    
                    # Show some citation details
                    for i, citation in enumerate(citations[:3]):
                        print(f"     Citation {i+1}: {citation.get('text', 'N/A')[:100]}...")
                
                return result
            else:
                print(f"❌ Status check failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Status check failed: {e}")
            return None
    
    def run_comprehensive_test(self):
        """Run a comprehensive test of all endpoints"""
        print("🚀 Starting comprehensive API test...")
        print("=" * 50)
        
        # Test 1: Health endpoint
        if not self.test_health_endpoint():
            print("❌ Health check failed - stopping tests")
            return
        
        print("\n" + "=" * 50)
        
        # Test 2: Text analysis
        test_text = """
        We review a trial court's parenting plan for abuse of discretion. 
        In re Marriage of Chandola, 180 Wn.2d 632, 642, 327 P.3d 644 (2014). 
        A court abuses its discretion if its decision is manifestly unreasonable 
        or based on untenable grounds or reasons.
        """
        
        task_id = self.test_text_analysis(test_text)
        if task_id:
            print(f"   Waiting for text analysis to complete...")
            time.sleep(5)  # Wait a bit for processing
            self.check_task_status(task_id)
        
        print("\n" + "=" * 50)
        
        # Test 3: File upload (if test file exists)
        test_files = [
            "test_upload.txt",
            "test_case_1.pdf",
            "test_case_2.pdf"
        ]
        
        for test_file in test_files:
            if os.path.exists(test_file):
                print(f"\nTesting file upload with: {test_file}")
                task_id = self.test_file_upload(test_file)
                if task_id:
                    print(f"   Waiting for file processing to complete...")
                    time.sleep(10)  # Wait longer for file processing
                    self.check_task_status(task_id)
                break
        
        print("\n" + "=" * 50)
        
        # Test 4: URL analysis
        test_urls = [
            "https://www.courts.wa.gov/opinions/index.cfm?fa=opinions.showOpinion&filename=180wn2d0632",
            "https://www.law.cornell.edu/supct/cases/name/us/"
        ]
        
        for test_url in test_urls:
            print(f"\nTesting URL analysis with: {test_url}")
            task_id = self.test_url_analysis(test_url)
            if task_id:
                print(f"   Waiting for URL processing to complete...")
                time.sleep(5)
                self.check_task_status(task_id)
            break
        
        print("\n" + "=" * 50)
        print("✅ Comprehensive test completed!")

def main():
    """Main test function"""
    print("CaseStrainer Production API Tester")
    print("=" * 40)
    
    # Create tester instance
    tester = CaseStrainerAPITester()
    
    # Run comprehensive test
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main()
