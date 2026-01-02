#!/usr/bin/env python3
"""
Check the actual citations from the completed task
"""

import requests
import json

def check_citations_detail():
    """Check detailed citation information"""
    
    task_id = "73d0ad65-8480-4a5a-910a-811cd27480eb"
    
    print(f"🔍 Checking detailed citations for: {task_id}")
    
    try:
        response = requests.get(f"http://localhost:5000/casestrainer/api/task_status/{task_id}")
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('citations', [])
            
            print(f"📋 Total citations: {len(citations)}")
            
            # Show first 10 citations in detail
            for i, citation in enumerate(citations[:10]):
                print(f"\n  Citation {i+1}:")
                print(f"    Citation: {citation.get('citation', 'N/A')}")
                print(f"    Verified: {citation.get('verified', 'N/A')}")
                print(f"    Case Name: {citation.get('case_name', 'N/A')}")
                print(f"    Extracted Case Name: {citation.get('extracted_case_name', 'N/A')}")
                print(f"    Canonical Name: {citation.get('canonical_name', 'N/A')}")
                print(f"    Canonical Date: {citation.get('canonical_date', 'N/A')}")
                print(f"    Canonical URL: {citation.get('canonical_url', 'N/A')}")
                print(f"    Court: {citation.get('court', 'N/A')}")
                print(f"    Method: {citation.get('method', 'N/A')}")
                print(f"    Confidence: {citation.get('confidence', 'N/A')}")
                
                # Check if this looks like a verifiable citation
                citation_text = citation.get('citation', '')
                if any(reporter in citation_text for reporter in ['U.S.', 'S. Ct.', 'L. Ed.', 'F.3d', 'F.2d', 'P.3d', 'P.2d', 'Wn.2d']):
                    print(f"    📯 This looks like a verifiable citation")
                else:
                    print(f"    ℹ️  This might not be a standard legal citation")
            
            # Check if any citations have verification data
            verified_count = sum(1 for c in citations if c.get('verified', False))
            canonical_count = sum(1 for c in citations if c.get('canonical_name'))
            
            print(f"\n📈 SUMMARY:")
            print(f"   Total citations: {len(citations)}")
            print(f"   Verified citations: {verified_count}")
            print(f"   Citations with canonical data: {canonical_count}")
            
            if verified_count == 0 and canonical_count == 0:
                print(f"\n🔍 ANALYSIS:")
                print(f"   None of the citations have verification data.")
                print(f"   This could mean:")
                print(f"   1. Verification is disabled in the pipeline")
                print(f"   2. These citations are not in the CourtListener database")
                print(f"   3. There's still an issue with the verification process")
                
                # Let's check a few citation formats
                print(f"\n📋 CITATION FORMATS:")
                for i, citation in enumerate(citations[:5]):
                    cit = citation.get('citation', '')
                    print(f"   {i+1}. '{cit}'")
                
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    check_citations_detail()
