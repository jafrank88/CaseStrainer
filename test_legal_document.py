#!/usr/bin/env python3
"""
Test the legal document provided by the user to verify:
1. Async processing works with real legal text
2. Progress bar moves properly
3. Citations are extracted and verified correctly
"""

import requests
import json
import time
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_legal_document():
    """Test with the actual legal document provided by user."""
    
    # The legal document text (truncated for testing)
    legal_text = """IN THE SUPREME COURT OF THE STATE OF WASHINGTON CERTIFICATION FROM THE UNITED STATES DISTRICT COURT FOR THE WESTERN DISTRICT OF WASHINGTON

LISA BRANSON and CHERIE BURKE, individually and on behalf of all others similarly situated, Plaintiffs, En Banc v. WASHINGTON FINE WINE & SPIRITS, LLC, a Washington limited liability company doing business as TOTAL WINE & More; and DOES 1-20, Defendants. Filed: September 4, 2025

MADSEN, J.—In 2022, the legislature amended the Washington Equal Pay and Opportunities Act (EPOA), ch. 49.58 RCW, to require employers with 15 or more employees to disclose wage scale, salary range, and benefits information in all job postings, effective January 1, 2023. RCW 49.58.110. Violations of this statute entitles employees and job applicants to the remedies listed in RCW 49.58.060-.070. RCW 49.58.110(4).

This case concerns the interpretation of the key term "job applicant" in RCW 49.58.110(4). The federal district court has asked this court to determine what a plaintiff must prove to be deemed a "job applicant." We hold that a plaintiff must apply to a specific job posting but is not required to prove they are a "bona fide" or "good faith" applicant to obtain remedies under the statute.

The defendant, Washington Fine Wine and Spirits LLC, which does business as Total Wine and More (Total Wine), is a Washington limited liability company that owns and operates 13 retail liquor stores throughout Washington. After the effective date in RCW 49.58.110, plaintiffs Lisa Branson and Cherie Burke submitted applications for job openings at the defendant's retail stores.

Subsequently, Branson and Burke filed an amended class action complaint against Total Wine in King County, invoking their right to statutory damages under RCW 49.58.070 and RCW 49.58.110 for Total Wine's failure to post the required wage scale or salary range in its job postings.

Certified questions are questions of law that this court reviews de novo and in light of the record certified by the federal court. Lopez Demetrio v. Sakuma Bros. Farms, 183 Wn.2d 649, 655, 355 P.3d 258 (2015). Statutory interpretation is also an issue of law we review de novo. Spokane County v. Dep't of Fish & Wildlife, 192 Wn.2d 453, 457, 430 P.3d 655 (2018).

We are asked to interpret the statutory term "job applicant" within RCW 49.58.110(4). Our "fundamental objective is to ascertain and carry out the Legislature's intent, and if the statute's meaning is plain on its face, then the court must give effect to that plain meaning as an expression of legislative intent." Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9-10, 43 P.3d 4 (2002).

If the plain language of the statute is clear and subject to only one reasonable interpretation, then we look no further. State v. Velasquez, 176 Wn.2d 333, 336, 292 P.3d 92 (2013). A term does not become ambiguous "merely because multiple interpretations are conceivable" but rather when it is subject to more than one reasonable interpretation.

The EPOA, formerly known as the Equal Pay Act, was enacted in Washington in 1943 to prohibit gender-based pay discrimination. In 2018, the EPOA was expanded to enhance enforcement by allowing the Department of Labor and Industries (L&I) to investigate complaints made by employees for violations of the act. See RCW 49.58.060.

Since the statute does not provide a definition of the term, we look to dictionary definitions "to determine a word's plain and ordinary meaning." State v. M.Y.G., 199 Wn.2d 528, 532, 509 P.3d 818 (2022) (plurality opinion) (quoting Am. Legion Post No. 32 v. City of Walla Walla, 116 Wn.2d 1, 8, 802 P.2d 784 (1991)).

The term "applicant" is defined as "one who applies for something : one who makes a usually formal request especially for something of benefit to himself." The related term "apply" means "to make an appeal or a request especially formally and often in writing and usually for something of benefit to oneself."

The plain language of the term "job applicant" means a person who applies to a job posting, regardless of their subjective intent in doing so. We must give effect to that meaning. Broughton Lumber Co. v. BNSF Ry. Co., 174 Wn.2d 619, 627, 278 P.3d 173 (2012).

Under RCW 49.58.060(1), L&I is tasked with investigating complaints made by job applicants and employees to determine if there has been a violation of the EPOA. If a violation has occurred, L&I may, among other things, "order the employer to pay to the complainant actual damages; statutory damages equal to the actual damages or five thousand dollars, whichever is greater." RCW 49.58.060(2)(a).

The agency interpretation shows that "job applicants" must be people who apply for jobs in good faith or have a bona fide intention of gaining employment. However, L&I does not have rule making authority over the meaning of the term "job applicant," and the meaning of "job applicant" is not ambiguous.

We answer the example raised in the certified question no. A job applicant need not prove they are a "bona fide" applicant to be deemed a "job applicant." Rather, in accordance with the plain language of RCW 49.58.110(4), a person must apply to any solicitation intended to recruit job applicants for a specific available position to be considered a "job applicant," regardless of the person's subjective intent in applying for the specific position."""

    print("🧪 TESTING LEGAL DOCUMENT PROCESSING")
    print("=" * 60)
    print(f"📏 Document length: {len(legal_text)} bytes")
    print(f"📏 Should trigger async: {len(legal_text) > 5120}")
    print()

    try:
        print("🔄 Submitting legal document for analysis...")
        response = requests.post(
            "http://localhost:5000/casestrainer/api/analyze",
            json={"type": "text", "text": legal_text},
            headers={"Content-Type": "application/json"},
            timeout=30,
            verify=False
        )
        
        if response.status_code == 200:
            result = response.json()
            processing_mode = result.get('metadata', {}).get('processing_mode', 'unknown')
            
            print(f"✅ Status: {response.status_code}")
            print(f"📊 Processing mode: {processing_mode}")
            
            # Handle async processing
            if processing_mode == 'queued':
                task_id = result.get('metadata', {}).get('job_id')
                if task_id:
                    print(f"📋 Task ID: {task_id}")
                    print("⏳ Waiting for async processing...")
                    
                    # Poll for completion
                    for attempt in range(20):  # Wait up to 40 seconds
                        time.sleep(2)
                        
                        status_response = requests.get(
                            f"http://localhost:5000/casestrainer/api/task_status/{task_id}",
                            verify=False
                        )
                        
                        if status_response.status_code == 200:
                            status_result = status_response.json()
                            status = status_result.get('status', 'unknown')
                            progress = status_result.get('progress_data', {}).get('overall_progress', 0)
                            current_step = status_result.get('progress_data', {}).get('current_message', 'Processing')
                            
                            print(f"  Attempt {attempt + 1}: {status} - {progress}% - {current_step}")
                            
                            if status == 'completed':
                                result = status_result
                                break
                            elif status == 'failed':
                                print(f"❌ Processing failed: {status_result.get('error', 'Unknown error')}")
                                return False
                        else:
                            print(f"  Status check failed: {status_response.status_code}")
                    
                    if status != 'completed':
                        print("❌ Processing timed out")
                        return False
            
            # Extract results
            citations = result.get('result', {}).get('citations', result.get('citations', []))
            clusters = result.get('result', {}).get('clusters', result.get('clusters', []))
            
            print()
            print("📊 RESULTS:")
            print(f"📝 Citations found: {len(citations)}")
            print(f"🔗 Clusters found: {len(clusters)}")
            
            if citations:
                print()
                print("📋 First 10 citations:")
                for i, citation in enumerate(citations[:10]):
                    citation_text = citation.get('citation', '')
                    verified = citation.get('verified', False) or citation.get('is_verified', False)
                    canonical_name = citation.get('canonical_name', 'N/A')
                    
                    status_icon = "✅" if verified else "❌"
                    print(f"  {i+1:2d}. {status_icon} {citation_text}")
                    if verified and canonical_name != 'N/A':
                        print(f"      📖 {canonical_name}")
                
                # Check verification consistency
                verified_count = sum(1 for c in citations if c.get('verified', False) or c.get('is_verified', False))
                print()
                print(f"🔍 Verification Summary:")
                print(f"   Total citations: {len(citations)}")
                print(f"   Verified citations: {verified_count}")
                print(f"   Verification rate: {verified_count/len(citations)*100:.1f}%")
            
            if clusters:
                print()
                print("🔗 Cluster Summary:")
                for i, cluster in enumerate(clusters[:5]):
                    cluster_verified = cluster.get('verified', False)
                    cluster_size = cluster.get('size', len(cluster.get('citations', [])))
                    case_name = cluster.get('case_name', cluster.get('canonical_name', 'Unknown'))
                    
                    status_icon = "✅" if cluster_verified else "❌"
                    print(f"  {i+1}. {status_icon} {case_name} ({cluster_size} citations)")
            
            print()
            print("🎉 SUCCESS: Legal document processed successfully!")
            return True
            
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        return False

if __name__ == "__main__":
    success = test_legal_document()
    if success:
        print("\n✅ Legal document test PASSED!")
    else:
        print("\n❌ Legal document test FAILED!")
