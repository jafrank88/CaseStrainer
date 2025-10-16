#!/usr/bin/env python3
"""
Test Fix #68: PDF Line Break Handling
Test with 25-2808.pdf to see if case name truncation is fixed.
"""

import requests
import json
import urllib3
from pathlib import Path

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_25_2808():
    """Test 25-2808.pdf with Fix #68 applied"""
    
    pdf_path = Path(r"D:\dev\casestrainer\25-2808.pdf")
    
    print("="*80)
    print("TESTING FIX #68: PDF LINE BREAK HANDLING")
    print("="*80)
    print(f"\n[*] Document: {pdf_path.name}")
    print(f"    Size: {pdf_path.stat().st_size / 1024:.1f} KB")
    
    # Upload to API
    print("\n[*] Uploading to API...")
    url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    
    with open(pdf_path, 'rb') as f:
        files = {'file': (pdf_path.name, f, 'application/pdf')}
        data = {'force_mode': 'sync'}
        
        try:
            response = requests.post(
                url,
                files=files,
                data=data,
                verify=False,
                timeout=600
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Save full result
                with open("test_fix68_results.json", "w") as out:
                    json.dump(result, out, indent=2)
                print(f"[+] Saved results to test_fix68_results.json")
                
                # Analyze results
                total_citations = result.get('statistics', {}).get('total_citations', 0)
                verified_citations = result.get('statistics', {}).get('verified_citations', 0)
                total_clusters = result.get('statistics', {}).get('total_clusters', 0)
                verified_clusters = result.get('statistics', {}).get('verified_clusters', 0)
                
                print(f"\n" + "="*80)
                print("RESULTS")
                print("="*80)
                if total_citations > 0:
                    print(f"Citations: {total_citations} total, {verified_citations} verified ({verified_citations/total_citations*100:.1f}%)")
                else:
                    print(f"Citations: {total_citations} total, {verified_citations} verified (0.0%)")
                if total_clusters > 0:
                    print(f"Clusters: {total_clusters} total, {verified_clusters} verified ({verified_clusters/total_clusters*100:.1f}%)")
                else:
                    print(f"Clusters: {total_clusters} total, {verified_clusters} verified (0.0%)")
                
                # Check previously truncated case names
                print(f"\n" + "="*80)
                print("CHECKING PREVIOUSLY TRUNCATED CASE NAMES")
                print("="*80)
                
                problem_citations = {
                    "780 F. Supp. 3d 897": ("E. Palo Alto v. U.", "Cmty. Legal Servs. in E. Palo Alto v. U.S. Dep't"),
                    "446 F.3d 167": ("Tootle v. Se", "Tootle v. Sec'y of Navy"),
                    "56 F.3d 279": ("Kidwell v. Dep", "Kidwell v. Dep't of Army"),
                    "606 U.S. __": ("Noem v. Na", "Noem v. Nat'l TPS All."),
                    "145 S. Ct. 2635": ("Trump v. Am", "Trump v. Am. Fed'n of Gov't Emps."),
                }
                
                improvements = 0
                still_truncated = 0
                
                for citation_obj in result.get('citations', []):
                    citation_text = citation_obj.get('citation', '')
                    extracted_name = citation_obj.get('extracted_case_name', '')
                    
                    if citation_text in problem_citations:
                        old_name, expected_name = problem_citations[citation_text]
                        
                        # Check if it's improved
                        if len(extracted_name) > len(old_name):
                            print(f"\n[+] IMPROVED: {citation_text}")
                            print(f"   Before: '{old_name}'")
                            print(f"   After:  '{extracted_name}'")
                            if expected_name in extracted_name:
                                print(f"   Status: COMPLETE FIX!")
                                improvements += 1
                            else:
                                print(f"   Status: Partial improvement")
                                improvements += 1
                        elif extracted_name == old_name:
                            print(f"\n[-] STILL TRUNCATED: {citation_text}")
                            print(f"   Extracted: '{extracted_name}'")
                            print(f"   Expected:  '{expected_name}'")
                            still_truncated += 1
                        else:
                            print(f"\n[!] CHANGED: {citation_text}")
                            print(f"   Before: '{old_name}'")
                            print(f"   After:  '{extracted_name}'")
                
                print(f"\n" + "="*80)
                print("SUMMARY")
                print("="*80)
                print(f"Tested: {len(problem_citations)} previously truncated citations")
                print(f"Improved: {improvements}")
                print(f"Still truncated: {still_truncated}")
                print(f"Success rate: {improvements/len(problem_citations)*100:.1f}%")
                
                # Overall verification improvement
                print(f"\n" + "="*80)
                print("VERIFICATION IMPROVEMENT")
                print("="*80)
                print(f"Before Fix #68: 28% verification rate (12/43 citations)")
                if total_citations > 0:
                    print(f"After Fix #68:  {verified_citations/total_citations*100:.1f}% verification rate ({verified_citations}/{total_citations} citations)")
                    improvement = (verified_citations/total_citations*100) - 28
                    print(f"Improvement: {improvement:+.1f} percentage points")
                else:
                    print(f"After Fix #68:  0.0% verification rate (0/0 citations)")
                    print(f"Improvement: N/A")
                
            else:
                print(f"[-] API Error: {response.status_code}")
                print(f"   Response: {response.text[:500]}")
        
        except Exception as e:
            print(f"[-] Exception: {e}")

if __name__ == "__main__":
    test_25_2808()

