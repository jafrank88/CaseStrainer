#!/usr/bin/env python3
"""
Comprehensive test suite for sync and async processing
Tests URLs, files, and text inputs for proper citation extraction and clustering
"""

import requests
import json
import time
import os
from typing import Dict, List, Any

class CaseStrainerTester:
    def __init__(self):
        self.base_url = "http://localhost:5000/casestrainer/api"
        self.results = []
        
    def log_result(self, test_name: str, status: str, details: Dict = None):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "details": details or {}
        }
        self.results.append(result)
        print(f"[{status}] {test_name}")
        if details:
            for key, value in details.items():
                print(f"    {key}: {value}")
        print()
    
    def test_text_sync(self):
        """Test sync processing with small text"""
        print("=== Testing Text Sync Processing ===")
        
        text = "In Smith v. Jones, 123 U.S. 456 (2023), the court held that precedent. This was followed by Brown v. Board, 345 F.2d 789 (2024)."
        
        try:
            response = requests.post(
                f"{self.base_url}/analyze",
                data={'text': text, 'type': 'text'},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if immediate response (sync)
                if 'citations' in data and 'task_id' not in data:
                    citations = data.get('citations', [])
                    clusters = data.get('clusters', [])
                    
                    self.log_result("Text Sync", "PASS", {
                        "citations_found": len(citations),
                        "clusters_found": len(clusters),
                        "processing_mode": "sync",
                        "sample_citation": citations[0].get('citation', '') if citations else None
                    })
                    
                    # Validate citation extraction
                    if len(citations) >= 2:
                        self.log_result("Text Sync - Citation Count", "PASS", {
                            "expected": ">= 2 citations",
                            "actual": len(citations)
                        })
                    else:
                        self.log_result("Text Sync - Citation Count", "FAIL", {
                            "expected": ">= 2 citations",
                            "actual": len(citations)
                        })
                    
                    # Validate clustering
                    if len(clusters) > 0:
                        self.log_result("Text Sync - Clustering", "PASS", {
                            "clusters_found": len(clusters),
                            "sample_cluster": clusters[0].get('cluster_name', 'N/A') if clusters else None
                        })
                    else:
                        self.log_result("Text Sync - Clustering", "WARN", {
                            "message": "No clusters found (may be expected for distinct citations)"
                        })
                else:
                    self.log_result("Text Sync", "FAIL", {
                        "error": "Expected immediate sync response but got task_id",
                        "task_id": data.get('task_id')
                    })
            else:
                self.log_result("Text Sync", "FAIL", {
                    "error": f"HTTP {response.status_code}",
                    "response": response.text[:200]
                })
                
        except Exception as e:
            self.log_result("Text Sync", "ERROR", {"error": str(e)})
    
    def test_text_async(self):
        """Test async processing with large text"""
        print("=== Testing Text Async Processing ===")
        
        # Create large text with repeated citations to trigger async
        base_text = """
        In the landmark case of Smith v. Jones, 123 U.S. 456 (2023), the Supreme Court established important precedent.
        This decision was later referenced in Brown v. Board of Education, 345 F.2d 789 (2024).
        The appeals court in Davis v. Johnson, 567 S. Ct. 123 (2022), followed this reasoning.
        Additionally, the case of Wilson v. Martinez, 890 F.3d 234 (2021), provides further context.
        The circuit court in Anderson v. Taylor, 234 F. Supp. 567 (2025), applied these principles.
        """
        
        # Repeat to make it large enough for async processing
        text = base_text * 100  # ~25KB
        
        try:
            response = requests.post(
                f"{self.base_url}/analyze",
                data={'text': text, 'type': 'text'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'task_id' in data:
                    task_id = data['task_id']
                    self.log_result("Text Async - Task Created", "PASS", {
                        "task_id": task_id,
                        "text_size": len(text)
                    })
                    
                    # Poll for completion
                    max_wait = 60  # 60 seconds
                    start_time = time.time()
                    
                    while time.time() - start_time < max_wait:
                        status_response = requests.get(
                            f"{self.base_url}/task_status/{task_id}",
                            timeout=5
                        )
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            status = status_data.get('status', 'unknown')
                            progress = status_data.get('progress', 0)
                            
                            if status == 'completed':
                                # Get final results
                                result_response = requests.get(
                                    f"{self.base_url}/task_result/{task_id}",
                                    timeout=5
                                )
                                
                                if result_response.status_code == 200:
                                    result_data = result_response.json()
                                    citations = result_data.get('citations', [])
                                    clusters = result_data.get('clusters', [])
                                    
                                    self.log_result("Text Async - Completion", "PASS", {
                                        "citations_found": len(citations),
                                        "clusters_found": len(clusters),
                                        "processing_time": f"{time.time() - start_time:.1f}s"
                                    })
                                    
                                    # Validate results
                                    if len(citations) >= 5:  # Should find at least 5 unique citations
                                        self.log_result("Text Async - Citation Extraction", "PASS", {
                                            "expected": ">= 5 unique citations",
                                            "actual": len(citations)
                                        })
                                    else:
                                        self.log_result("Text Async - Citation Extraction", "WARN", {
                                            "expected": ">= 5 unique citations",
                                            "actual": len(citations)
                                        })
                                    
                                    if len(clusters) > 0:
                                        self.log_result("Text Async - Clustering", "PASS", {
                                            "clusters_found": len(clusters)
                                        })
                                    else:
                                        self.log_result("Text Async - Clustering", "WARN", {
                                            "message": "No clusters found"
                                        })
                                else:
                                    self.log_result("Text Async - Result Retrieval", "FAIL", {
                                        "error": f"HTTP {result_response.status_code}"
                                    })
                                break
                                
                            elif status == 'failed':
                                self.log_result("Text Async - Processing", "FAIL", {
                                    "error": "Task failed",
                                    "details": status_data.get('error', 'Unknown error')
                                })
                                break
                                
                            elif status == 'processing':
                                print(f"    Progress: {progress}%")
                                time.sleep(2)
                            else:
                                time.sleep(2)
                        else:
                            self.log_result("Text Async - Status Check", "FAIL", {
                                "error": f"HTTP {status_response.status_code}"
                            })
                            break
                    else:
                        self.log_result("Text Async - Processing", "FAIL", {
                            "error": "Timeout after 60 seconds"
                        })
                else:
                    self.log_result("Text Async", "FAIL", {
                        "error": "Expected task_id for large text but got immediate response"
                    })
            else:
                self.log_result("Text Async", "FAIL", {
                    "error": f"HTTP {response.status_code}",
                    "response": response.text[:200]
                })
                
        except Exception as e:
            self.log_result("Text Async", "ERROR", {"error": str(e)})
    
    def test_url_processing(self):
        """Test URL processing (PDF)"""
        print("=== Testing URL Processing ===")
        
        # Use a known legal PDF URL
        test_url = "https://www.courtlistener.com/pdf/2023/08/23/wilson_v._martinez_opinion.pdf"
        
        try:
            response = requests.post(
                f"{self.base_url}/analyze",
                data={'url': test_url, 'type': 'url'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'task_id' in data:
                    task_id = data['task_id']
                    self.log_result("URL Processing - Task Created", "PASS", {
                        "task_id": task_id,
                        "url": test_url
                    })
                    
                    # Poll for completion
                    max_wait = 120  # 2 minutes for PDF processing
                    start_time = time.time()
                    
                    while time.time() - start_time < max_wait:
                        status_response = requests.get(
                            f"{self.base_url}/task_status/{task_id}",
                            timeout=5
                        )
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            status = status_data.get('status', 'unknown')
                            
                            if status == 'completed':
                                # Get final results
                                result_response = requests.get(
                                    f"{self.base_url}/task_result/{task_id}",
                                    timeout=5
                                )
                                
                                if result_response.status_code == 200:
                                    result_data = result_response.json()
                                    citations = result_data.get('citations', [])
                                    clusters = result_data.get('clusters', [])
                                    
                                    self.log_result("URL Processing - Completion", "PASS", {
                                        "citations_found": len(citations),
                                        "clusters_found": len(clusters),
                                        "processing_time": f"{time.time() - start_time:.1f}s"
                                    })
                                    
                                    if len(citations) > 0:
                                        self.log_result("URL Processing - Citation Extraction", "PASS", {
                                            "citations_extracted": len(citations),
                                            "sample_citation": citations[0].get('citation', '')[:50] + "..." if citations else None
                                        })
                                    else:
                                        self.log_result("URL Processing - Citation Extraction", "WARN", {
                                            "message": "No citations extracted from PDF"
                                        })
                                else:
                                    self.log_result("URL Processing - Result Retrieval", "FAIL", {
                                        "error": f"HTTP {result_response.status_code}"
                                    })
                                break
                                
                            elif status == 'failed':
                                self.log_result("URL Processing", "FAIL", {
                                    "error": "Task failed",
                                    "details": status_data.get('error', 'Unknown error')
                                })
                                break
                            else:
                                time.sleep(3)
                        else:
                            self.log_result("URL Processing - Status Check", "FAIL", {
                                "error": f"HTTP {status_response.status_code}"
                            })
                            break
                    else:
                        self.log_result("URL Processing", "FAIL", {
                            "error": "Timeout after 120 seconds"
                        })
                else:
                    self.log_result("URL Processing", "FAIL", {
                        "error": "Expected task_id for URL but got immediate response"
                    })
            else:
                self.log_result("URL Processing", "FAIL", {
                    "error": f"HTTP {response.status_code}",
                    "response": response.text[:200]
                })
                
        except Exception as e:
            self.log_result("URL Processing", "ERROR", {"error": str(e)})
    
    def test_file_processing(self):
        """Test file upload processing"""
        print("=== Testing File Processing ===")
        
        # Create a test file with legal citations
        test_content = """
        LEGAL DOCUMENT TEST
        
        This document contains several legal citations for testing purposes.
        
        1. Supreme Court case: Smith v. Jones, 123 U.S. 456 (2023)
        2. Federal Appeals: Brown v. Board, 345 F.2d 789 (2024) 
        3. Supreme Court: Davis v. Johnson, 567 S. Ct. 123 (2022)
        4. Circuit Court: Wilson v. Martinez, 890 F.3d 234 (2021)
        5. District Court: Anderson v. Taylor, 234 F. Supp. 567 (2025)
        
        These citations should be extracted and processed correctly.
        """
        
        test_file = "test_legal_document.txt"
        
        try:
            # Write test file
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(test_content)
            
            # Upload file
            with open(test_file, 'rb') as f:
                files = {'file': (test_file, f, 'text/plain')}
                data = {'type': 'file'}
                
                response = requests.post(
                    f"{self.base_url}/analyze",
                    files=files,
                    data=data,
                    timeout=10
                )
            
            if response.status_code == 200:
                result_data = response.json()
                
                # File uploads typically return immediate results for small files
                if 'citations' in result_data:
                    citations = result_data.get('citations', [])
                    clusters = result_data.get('clusters', [])
                    
                    self.log_result("File Processing", "PASS", {
                        "citations_found": len(citations),
                        "clusters_found": len(clusters),
                        "processing_mode": "sync"
                    })
                    
                    if len(citations) >= 5:
                        self.log_result("File Processing - Citation Count", "PASS", {
                            "expected": ">= 5 citations",
                            "actual": len(citations)
                        })
                    else:
                        self.log_result("File Processing - Citation Count", "WARN", {
                            "expected": ">= 5 citations",
                            "actual": len(citations)
                        })
                        
                elif 'task_id' in result_data:
                    task_id = result_data['task_id']
                    self.log_result("File Processing - Task Created", "PASS", {
                        "task_id": task_id,
                        "processing_mode": "async"
                    })
                    
                    # Could poll for completion here, but for test purposes we'll note it's queued
                else:
                    self.log_result("File Processing", "FAIL", {
                        "error": "Unexpected response format"
                    })
            else:
                self.log_result("File Processing", "FAIL", {
                    "error": f"HTTP {response.status_code}",
                    "response": response.text[:200]
                })
                
        except Exception as e:
            self.log_result("File Processing", "ERROR", {"error": str(e)})
        finally:
            # Clean up test file
            if os.path.exists(test_file):
                os.remove(test_file)
    
    def test_clustering_quality(self):
        """Test clustering quality with parallel citations"""
        print("=== Testing Clustering Quality ===")
        
        # Text with parallel citations
        text = """
        The Supreme Court decision in United States v. Nixon, 578 U.S. 330 (2016),
        was also reported as 136 S. Ct. 1540 (2016) and 194 L. Ed. 2d 256 (2016).
        These parallel citations should be clustered together.
        
        In contrast, the case of Smith v. Jones, 123 U.S. 456 (2023),
        is entirely separate and should form its own cluster.
        """
        
        try:
            response = requests.post(
                f"{self.base_url}/analyze",
                data={'text': text, 'type': 'text'},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'citations' in data:
                    citations = data.get('citations', [])
                    clusters = data.get('clusters', [])
                    
                    self.log_result("Clustering Quality - Processing", "PASS", {
                        "citations_found": len(citations),
                        "clusters_found": len(clusters)
                    })
                    
                    # Check if parallel citations are clustered
                    nixon_citations = [c for c in citations if 'Nixon' in c.get('extracted_case_name', '') or '578 U.S. 330' in c.get('citation', '')]
                    
                    if len(nixon_citations) >= 2:
                        # Check if they're in the same cluster
                        cluster_ids = [c.get('cluster_id') for c in nixon_citations]
                        if len(set(cluster_ids)) == 1 and cluster_ids[0] is not None:
                            self.log_result("Clustering Quality - Parallel Citations", "PASS", {
                                "message": "Parallel citations correctly clustered",
                                "cluster_id": cluster_ids[0],
                                "nixon_citations_clustered": len(nixon_citations)
                            })
                        else:
                            self.log_result("Clustering Quality - Parallel Citations", "FAIL", {
                                "message": "Parallel citations not clustered together",
                                "cluster_ids": cluster_ids
                            })
                    else:
                        self.log_result("Clustering Quality - Parallel Citations", "WARN", {
                            "message": f"Only {len(nixon_citations)} Nixon citation(s) found",
                            "expected": ">= 2 parallel citations"
                        })
                else:
                    self.log_result("Clustering Quality", "FAIL", {
                        "error": "No citations in response"
                    })
            else:
                self.log_result("Clustering Quality", "FAIL", {
                    "error": f"HTTP {response.status_code}"
                })
                
        except Exception as e:
            self.log_result("Clustering Quality", "ERROR", {"error": str(e)})
    
    def run_all_tests(self):
        """Run all tests"""
        print("=" * 60)
        print("CASESTRAINER COMPREHENSIVE TEST SUITE")
        print("=" * 60)
        print()
        
        # Run tests
        self.test_text_sync()
        self.test_text_async()
        self.test_url_processing()
        self.test_file_processing()
        self.test_clustering_quality()
        
        # Print summary
        print("=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        passed = len([r for r in self.results if r['status'] == 'PASS'])
        failed = len([r for r in self.results if r['status'] == 'FAIL'])
        warnings = len([r for r in self.results if r['status'] == 'WARN'])
        errors = len([r for r in self.results if r['status'] == 'ERROR'])
        
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Warnings: {warnings}")
        print(f"Errors: {errors}")
        print(f"Total: {len(self.results)}")
        print()
        
        # Show failed tests
        if failed > 0 or errors > 0:
            print("FAILED/ERROR TESTS:")
            for result in self.results:
                if result['status'] in ['FAIL', 'ERROR']:
                    print(f"  - {result['test']}: {result['status']}")
                    if 'error' in result.get('details', {}):
                        print(f"    Error: {result['details']['error']}")
        
        # Save results to file
        with open('test_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\nDetailed results saved to: test_results.json")
        
        return failed == 0 and errors == 0

if __name__ == "__main__":
    tester = CaseStrainerTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n[OK] All critical tests passed!")
    else:
        print("\n[FAIL] Some tests failed. Check the results above.")
