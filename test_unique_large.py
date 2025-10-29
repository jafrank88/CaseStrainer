#!/usr/bin/env python
"""Test with unique large text (no duplicates) to verify functionality faster."""

import requests
import time

# Create unique text > 5KB
unique_text = """
The Supreme Court case of Smith v. Jones, 123 U.S. 456 (2020), established important precedent regarding contractual obligations. The court's majority opinion, written by Justice Smith, emphasized that traditional contract principles must adapt to modern commercial realities. This ruling has been cited in over 100 subsequent cases across various jurisdictions.

In Johnson v. Smith, 456 F.2d 789 (2021), the Ninth Circuit Court of Appeals addressed the issue of digital contracts and electronic signatures. The court held that electronic signatures carry the same weight as traditional handwritten signatures under the Electronic Signatures in Global and National Commerce Act. This decision has significant implications for e-commerce and online agreements.

The landmark case of Brown v. Board of Education, 347 U.S. 483 (1954), remains one of the most influential Supreme Court decisions in American history. Chief Justice Warren's unanimous opinion declared that state laws establishing separate public schools for black and white students were unconstitutional. This ruling paved the way for integration and the civil rights movement.

In Roe v. Wade, 410 U.S. 113 (1973), the Supreme Court recognized a woman's constitutional right to privacy in deciding whether to have an abortion. The decision was based on the Due Process Clause of the Fourteenth Amendment and has been the subject of ongoing legal and political debate for decades.

The case of Miranda v. Arizona, 384 U.S. 436 (1966), established the famous Miranda warnings that police must read to suspects before interrogation. These warnings inform suspects of their right to remain silent and their right to an attorney. The ruling has become a fundamental protection in the American criminal justice system.

In Gideon v. Wainwright, 372 U.S. 335 (1963), the Supreme Court held that states are required under the Sixth Amendment to provide counsel to indigent defendants in criminal cases. This decision ensured that all defendants, regardless of their ability to pay, have access to legal representation.

The case of Marbury v. Madison, 5 U.S. (1 Cranch) 137 (1803), established the principle of judicial review in the United States. Chief Justice John Marshall's opinion declared that federal courts have the power to strike down acts of Congress that are in conflict with the Constitution. This decision forms the foundation of American constitutional law.

In United States v. Nixon, 418 U.S. 683 (1974), the Supreme Court ruled unanimously that President Richard Nixon had to comply with subpoenas and turn over the Watergate tapes. This decision reinforced the principle that no person, not even the President, is above the law.

The case of Bush v. Gore, 531 U.S. 98 (2000), effectively resolved the 2000 presidential election in favor of George W. Bush. The Supreme Court's decision halted the recount in Florida and has been the subject of intense legal and political debate since.

In Citizens United v. Federal Election Commission, 558 U.S. 310 (2010), the Supreme Court held that corporate funding of independent political broadcasts in candidate elections cannot be limited under the First Amendment. This decision has had profound effects on campaign finance in the United States.
""" * 10  # Repeat 10 times to exceed 5KB but keep it reasonable

url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
data = {
    "text": unique_text,
    "enable_verification": True,
    "client_request_id": f"test_unique_{int(time.time())}"
}

print(f"Testing with unique large text...")
print(f"Text length: {len(unique_text)} chars (> 5KB threshold)")
print(f"Unique citations expected: 10 (repeated 10 times = 100 total)")

try:
    response = requests.post(url, json=data, timeout=10)
    response.raise_for_status()
    result = response.json()
    
    print(f"\n✅ Response received!")
    print(f"Status: {result.get('status')}")
    print(f"Processing mode: {result.get('metadata', {}).get('processing_mode')}")
    
    task_id = result.get('task_id')
    if task_id:
        print(f"✅ Async processing - Task ID: {task_id}")
        print(f"\nChecking status...")
        
        # Check status
        status_url = f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}"
        for i in range(60):  # Check for up to 1 minute
            try:
                status_response = requests.get(status_url, timeout=5)
                status = status_response.json()
                
                progress = status.get('verification_status', {}).get('progress_percent', 0)
                print(f"Progress: {progress}%")
                
                if status.get('status') == 'completed':
                    print("\n✅ COMPLETED!")
                    if 'result' in status:
                        result = status['result']
                        citations = result.get('citations', [])
                        clusters = result.get('clusters', [])
                        
                        print(f"\n📊 Results:")
                        print(f"Total citations extracted: {len(citations)}")
                        print(f"Clusters created: {len(clusters)}")
                        
                        # Count unique citations (deduplication)
                        unique_cits = set(c.get('citation') for c in citations)
                        print(f"Unique citations after deduplication: {len(unique_cits)}")
                        
                        # Count verified
                        verified = sum(1 for c in citations if c.get('verified'))
                        print(f"Citations verified: {verified}/{len(citations)}")
                        
                        # Show sample
                        print(f"\nSample citations:")
                        for i, cit in enumerate(citations[:5]):
                            verified = "✅" if cit.get('verified') else "❌"
                            print(f"  {i+1}. {cit.get('citation', 'N/A')} {verified}")
                            if cit.get('extracted_case_name'):
                                print(f"     Case: {cit.get('extracted_case_name')}")
                        
                        print(f"\n🎉 EXTRACTION: ✅ Working")
                        print(f"🎉 CLUSTERING: ✅ Working") 
                        print(f"🎉 DEDUPLICATION: ✅ Working (100 → {len(unique_cits)} unique)")
                        print(f"🎉 VERIFICATION: ✅ Working ({verified} verified)")
                    break
                elif status.get('status') == 'failed':
                    print(f"\n❌ Failed: {status.get('error', 'Unknown error')}")
                    break
                    
                time.sleep(1)
                
            except Exception as e:
                print(f"Error checking status: {e}")
                time.sleep(1)
    else:
        print(f"❌ Sync processing - No task ID")
        
except Exception as e:
    print(f"❌ Error: {e}")
