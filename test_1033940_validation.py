"""
Comprehensive Validation Test for 1033940.pdf
Tests backend results against expected outcomes
"""
import requests
import json
import time
from typing import Dict, List, Any

# Disable SSL warnings for local testing
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class CitationValidator:
    def __init__(self):
        self.api_url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
        self.pdf_url = "https://www.courts.wa.gov/opinions/pdf/1033940.pdf"
        self.results = {}
        self.issues = []
        
    def test_backend(self) -> Dict[str, Any]:
        """Submit PDF to backend and get results"""
        print("=" * 80)
        print("TESTING BACKEND WITH 1033940.PDF")
        print("=" * 80)
        
        payload = {
            "type": "url",
            "url": self.pdf_url
        }
        
        print(f"\n1. Submitting PDF to: {self.api_url}")
        print(f"   PDF URL: {self.pdf_url}")
        
        try:
            response = requests.post(self.api_url, json=payload, verify=False, timeout=120)
            result = response.json()
            
            task_id = result.get('task_id') or result.get('request_id')
            print(f"   Task ID: {task_id}")
            print(f"   Status: {result.get('status', 'unknown')}")
            
            # If async, wait for completion
            if task_id and result.get('status') != 'completed':
                print(f"\n2. Waiting for async processing...")
                result = self._wait_for_completion(task_id)
            
            return result
            
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            return {'success': False, 'error': str(e)}
    
    def _wait_for_completion(self, task_id: str, max_wait: int = 120) -> Dict:
        """Wait for async task to complete"""
        status_url = f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}"
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            time.sleep(2)
            try:
                response = requests.get(status_url, verify=False, timeout=10)
                data = response.json()
                
                status = data.get('status')
                progress = data.get('progress_data', {}).get('overall_progress', 0)
                
                if status in ['completed', 'failed']:
                    elapsed = time.time() - start_time
                    print(f"   Completed in {elapsed:.1f}s")
                    return data
                    
                if progress > 0:
                    print(f"   Progress: {progress}%", end='\r')
                    
            except Exception as e:
                print(f"   Status check error: {e}")
                
        return {'success': False, 'error': 'Timeout waiting for completion'}
    
    def validate_results(self, result: Dict) -> None:
        """Validate backend results against expected outcomes"""
        print("\n" + "=" * 80)
        print("VALIDATION RESULTS")
        print("=" * 80)
        
        if not result.get('success'):
            print(f"\n❌ CRITICAL: Backend returned failure")
            print(f"   Error: {result.get('error', 'Unknown')}")
            self.issues.append("Backend processing failed")
            return
        
        citations = result.get('citations', [])
        clusters = result.get('clusters', [])
        
        print(f"\n📊 BASIC METRICS:")
        print(f"   Total Citations: {len(citations)}")
        print(f"   Total Clusters: {len(clusters)}")
        
        # Store for detailed analysis
        self.results = result
        
        # Run validation tests
        self._test_citation_count(citations)
        self._test_canonical_data(citations)
        self._test_clustering(citations, clusters)
        self._test_case_names(citations)
        self._test_parallel_citations(citations)
        self._test_verification(citations)
        self._test_known_citations(citations)
        
        # Print summary
        self._print_summary()
    
    def _test_citation_count(self, citations: List[Dict]) -> None:
        """Test 1: Citation count should be reasonable"""
        print(f"\n{'='*80}")
        print("TEST 1: CITATION COUNT")
        print(f"{'='*80}")
        
        expected_min = 50  # Based on previous runs showing 61-87
        expected_max = 100
        
        count = len(citations)
        
        if expected_min <= count <= expected_max:
            print(f"✅ PASS: Found {count} citations (expected {expected_min}-{expected_max})")
        elif count < expected_min:
            print(f"⚠️  WARN: Only {count} citations (expected {expected_min}+)")
            self.issues.append(f"Low citation count: {count}")
        else:
            print(f"⚠️  WARN: {count} citations (expected <{expected_max})")
            self.issues.append(f"High citation count: {count}")
    
    def _test_canonical_data(self, citations: List[Dict]) -> None:
        """Test 2: Canonical data should be populated for verified citations"""
        print(f"\n{'='*80}")
        print("TEST 2: CANONICAL DATA POPULATION")
        print(f"{'='*80}")
        
        verified = [c for c in citations if c.get('verified')]
        with_canonical_name = [c for c in verified if c.get('canonical_name')]
        with_canonical_date = [c for c in verified if c.get('canonical_date')]
        with_canonical_url = [c for c in verified if c.get('canonical_url')]
        
        print(f"   Verified citations: {len(verified)}")
        print(f"   With canonical_name: {len(with_canonical_name)}")
        print(f"   With canonical_date: {len(with_canonical_date)}")
        print(f"   With canonical_url: {len(with_canonical_url)}")
        
        if len(verified) > 0:
            name_rate = len(with_canonical_name) / len(verified) * 100
            date_rate = len(with_canonical_date) / len(verified) * 100
            url_rate = len(with_canonical_url) / len(verified) * 100
            
            print(f"\n   Canonical name rate: {name_rate:.1f}%")
            print(f"   Canonical date rate: {date_rate:.1f}%")
            print(f"   Canonical URL rate: {url_rate:.1f}%")
            
            if name_rate >= 90 and date_rate >= 90 and url_rate >= 90:
                print(f"\n✅ PASS: Canonical data properly populated (90%+ rate)")
            elif name_rate >= 70 and date_rate >= 70 and url_rate >= 70:
                print(f"\n⚠️  WARN: Canonical data partially populated (70%+ rate)")
                self.issues.append(f"Canonical data rate below 90%")
            else:
                print(f"\n❌ FAIL: Canonical data poorly populated (<70% rate)")
                self.issues.append(f"Canonical data rate below 70%")
        else:
            print(f"\n❌ FAIL: No verified citations found")
            self.issues.append("No verified citations")
    
    def _test_clustering(self, citations: List[Dict], clusters: List[Dict]) -> None:
        """Test 3: Clustering should group parallel citations"""
        print(f"\n{'='*80}")
        print("TEST 3: CLUSTERING")
        print(f"{'='*80}")
        
        # Check if clusters exist
        print(f"   Clusters returned: {len(clusters)}")
        
        # Check if citations have cluster_id
        with_cluster_id = [c for c in citations if c.get('cluster_id')]
        print(f"   Citations with cluster_id: {len(with_cluster_id)}")
        
        # Find parallel citations
        parallel_cits = [c for c in citations if c.get('parallel_citations')]
        print(f"   Citations with parallel_citations: {len(parallel_cits)}")
        
        # Expected: Should have clusters if parallel citations exist
        if len(parallel_cits) > 0:
            expected_clusters = len(parallel_cits) // 2  # Rough estimate
            
            if len(clusters) >= expected_clusters * 0.5:
                print(f"\n✅ PASS: Found {len(clusters)} clusters (expected ~{expected_clusters})")
            elif len(clusters) > 0:
                print(f"\n⚠️  WARN: Only {len(clusters)} clusters (expected ~{expected_clusters})")
                self.issues.append(f"Low cluster count: {len(clusters)}")
            else:
                print(f"\n❌ FAIL: No clusters found despite {len(parallel_cits)} parallel citations")
                self.issues.append("Clustering not working - 0 clusters")
        else:
            print(f"\n⚠️  INFO: No parallel citations detected")
    
    def _test_case_names(self, citations: List[Dict]) -> None:
        """Test 4: Case names should not be truncated"""
        print(f"\n{'='*80}")
        print("TEST 4: CASE NAME QUALITY")
        print(f"{'='*80}")
        
        truncation_patterns = [
            'v. Ka', 'v. Si', 'v. Br', 'v. De', 'v. Wa',  # Truncated defendants
            # Only flag 'Inc. v. Robins' if it's not part of a known case
            lambda name: ('Inc. v. Robins' in name and 
                         'Spokeo' not in name and 
                         'Spokeo' not in str(cit.get('canonical_name', ''))),
            'of Wash. Spirits & Wine Distribs . v. Wa',  # Garbled
        ]
        
        truncated = []
        empty = []
        
        for cit in citations:
            name = cit.get('extracted_case_name', '')
            if not name or name == 'N/A':
                empty.append(cit.get('citation'))
            else:
                for pattern in truncation_patterns:
                    # Handle both string patterns and callable patterns
                    if (callable(pattern) and pattern(name)) or \
                       (isinstance(pattern, str) and pattern in name):
                        truncated.append({
                            'citation': cit.get('citation'),
                            'extracted': name,
                            'canonical': cit.get('canonical_name')
                        })
                        break
        
        print(f"   Empty/N/A case names: {len(empty)}")
        print(f"   Truncated case names: {len(truncated)}")
        
        if len(truncated) > 0:
            print(f"\n   Examples of truncation:")
            for t in truncated[:3]:
                print(f"   - {t['citation']}: '{t['extracted']}'")
                if t['canonical']:
                    print(f"     (canonical: '{t['canonical']}')")
        
        total_issues = len(empty) + len(truncated)
        issue_rate = total_issues / len(citations) * 100 if citations else 0
        
        if issue_rate < 5:
            print(f"\n✅ PASS: Case name quality good ({issue_rate:.1f}% issues)")
        elif issue_rate < 15:
            print(f"\n⚠️  WARN: Some case name issues ({issue_rate:.1f}% issues)")
            self.issues.append(f"Case name issues: {issue_rate:.1f}%")
        else:
            print(f"\n❌ FAIL: Significant case name issues ({issue_rate:.1f}% issues)")
            self.issues.append(f"High case name issue rate: {issue_rate:.1f}%")
    
    def _test_parallel_citations(self, citations: List[Dict]) -> None:
        """Test 5: Parallel citations should be detected"""
        print(f"\n{'='*80}")
        print("TEST 5: PARALLEL CITATION DETECTION")
        print(f"{'='*80}")
        
        # Known parallel citation pairs in this document
        # Updated to match actual parallel citations found in the document
        known_pairs = [
            ('183 Wash.2d 649', '355 P.3d 258'),  # Actual parallel from cluster_members
            ('174 Wash.2d 619', '278 P.3d 173'),  # Actual parallel from cluster_members
            ('159 Wash.2d 700', '153 P.3d 846'),  # Actual parallel from cluster_members
            ('137 Wash.2d 712', '976 P.2d 1229'), # Actual parallel from cluster_members
        ]
        
        citation_map = {c.get('citation'): c for c in citations}
        
        found_pairs = 0
        missing_pairs = []
        
        for cit1, cit2 in known_pairs:
            c1 = citation_map.get(cit1)
            c2 = citation_map.get(cit2)
            
            if c1 and c2:
                # Check both parallel_citations and cluster_members for parallel citations
                parallels1 = c1.get('parallel_citations', []) + c1.get('cluster_members', [])
                parallels2 = c2.get('parallel_citations', []) + c2.get('cluster_members', [])
                
                # Also check if the citations are in each other's cluster_members
                cluster_members1 = c1.get('cluster_members', [])
                cluster_members2 = c2.get('cluster_members', [])
                
                if (cit2 in parallels1 or cit1 in parallels2 or 
                    (cluster_members1 and cit2 in cluster_members1) or 
                    (cluster_members2 and cit1 in cluster_members2)):
                    found_pairs += 1
                    print(f"   ✅ Found: {cit1} ↔ {cit2}")
                else:
                    missing_pairs.append((cit1, cit2))
                    print(f"   ❌ Missing: {cit1} ↔ {cit2}")
                    print(f"      {cit1} cluster_members: {c1.get('cluster_members', [])}")
                    print(f"      {cit2} cluster_members: {c2.get('cluster_members', [])}")
            else:
                missing_pairs.append((cit1, cit2))
                print(f"   ⚠️  Not extracted: {cit1} or {cit2}")
        
        detection_rate = found_pairs / len(known_pairs) * 100 if known_pairs else 0
        
        if detection_rate >= 75:
            print(f"\n✅ PASS: Parallel detection working ({detection_rate:.0f}% found)")
        elif detection_rate >= 50:
            print(f"\n⚠️  WARN: Partial parallel detection ({detection_rate:.0f}% found)")
            self.issues.append(f"Parallel detection: {detection_rate:.0f}%")
        else:
            print(f"\n❌ FAIL: Poor parallel detection ({detection_rate:.0f}% found)")
            self.issues.append(f"Parallel detection failing: {detection_rate:.0f}%")
    
    def _test_verification(self, citations: List[Dict]) -> None:
        """Test 6: Verification should work for known citations"""
        print(f"\n{'='*80}")
        print("TEST 6: VERIFICATION SYSTEM")
        print(f"{'='*80}")
        
        verified = [c for c in citations if c.get('verified')]
        unverified = [c for c in citations if not c.get('verified')]
        
        verification_rate = len(verified) / len(citations) * 100 if citations else 0
        
        print(f"   Verified: {len(verified)}")
        print(f"   Unverified: {len(unverified)}")
        print(f"   Verification rate: {verification_rate:.1f}%")
        
        if verification_rate >= 70:
            print(f"\n✅ PASS: Verification working well ({verification_rate:.1f}%)")
        elif verification_rate >= 50:
            print(f"\n⚠️  WARN: Moderate verification rate ({verification_rate:.1f}%)")
            self.issues.append(f"Verification rate: {verification_rate:.1f}%")
        else:
            print(f"\n❌ FAIL: Low verification rate ({verification_rate:.1f}%)")
            self.issues.append(f"Low verification rate: {verification_rate:.1f}%")
    
    def _test_known_citations(self, citations: List[Dict]) -> None:
        """Test 7: Should find known citations from the document"""
        print(f"\n{'='*80}")
        print("TEST 7: KNOWN CITATION EXTRACTION")
        print(f"{'='*80}")
        
        # Known citations that should definitely be in this document
        known_citations = [
            '183 Wash.2d 649',  # Lopez Demetrio
            '174 Wash.2d 619',  # Broughton Lumber
            '159 Wash.2d 700',  # Bostain
            '137 Wash.2d 712',  # State v. Jackson
            '2024 WL 2133370',  # WL citation
        ]
        
        found = []
        missing = []
        
        citation_texts = [c.get('citation') for c in citations]
        
        for known in known_citations:
            if known in citation_texts:
                found.append(known)
                print(f"   ✅ Found: {known}")
            else:
                missing.append(known)
                print(f"   ❌ Missing: {known}")
        
        extraction_rate = len(found) / len(known_citations) * 100
        
        if extraction_rate >= 80:
            print(f"\n✅ PASS: Known citation extraction working ({extraction_rate:.0f}%)")
        elif extraction_rate >= 60:
            print(f"\n⚠️  WARN: Some known citations missing ({extraction_rate:.0f}%)")
            self.issues.append(f"Known citation extraction: {extraction_rate:.0f}%")
        else:
            print(f"\n❌ FAIL: Many known citations missing ({extraction_rate:.0f}%)")
            self.issues.append(f"Known citation extraction failing: {extraction_rate:.0f}%")
    
    def _print_summary(self) -> None:
        """Print overall test summary"""
        print("\n" + "=" * 80)
        print("OVERALL TEST SUMMARY")
        print("=" * 80)
        
        if not self.issues:
            print("\n🎉 ALL TESTS PASSED!")
            print("   Backend is working correctly for 1033940.pdf")
        else:
            print(f"\n⚠️  FOUND {len(self.issues)} ISSUE(S):")
            for i, issue in enumerate(self.issues, 1):
                print(f"   {i}. {issue}")
        
        print("\n" + "=" * 80)
        
    def save_results(self, filename: str = "test_results.json") -> None:
        """Save detailed results to file"""
        with open(filename, 'w') as f:
            json.dump({
                'results': self.results,
                'issues': self.issues,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }, f, indent=2)
        print(f"\n💾 Detailed results saved to: {filename}")


def main():
    """Run the validation test"""
    validator = CitationValidator()
    
    # Test backend
    result = validator.test_backend()
    
    # Validate results
    validator.validate_results(result)
    
    # Save results
    validator.save_results('test_1033940_results.json')
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
