#!/usr/bin/env python3
"""
Analyze the sp-7788.pdf results to check if reporter-first verification is working
"""

import requests
import json

def analyze_sp7788_results():
    task_id = "773de729-1d50-45c8-b973-9f88922e4aad"
    
    try:
        response = requests.get(f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}")
        
        if response.status_code == 200:
            result = response.json()
            clusters = result.get('result', {}).get('clusters', [])
            
            print(f"Analyzing {len(clusters)} clusters from sp-7788.pdf...")
            print("=" * 80)
            
            # Find citations with missing/invalid case names
            problematic_citations = []
            total_citations = 0
            
            for cluster in clusters:
                citations = cluster.get('citations', [])
                total_citations += len(citations)
                
                for citation in citations:
                    extracted_name = citation.get('extracted_case_name', 'N/A')
                    if not extracted_name or extracted_name == "N/A" or len(extracted_name.strip()) < 3:
                        problematic_citations.append({
                            'citation': citation.get('citation', 'Unknown'),
                            'extracted_name': extracted_name,
                            'canonical_name': citation.get('canonical_name'),
                            'canonical_date': citation.get('canonical_date'),
                            'verified': citation.get('verified', False),
                            'source': citation.get('verification_source', ''),
                            'error': citation.get('error', '')
                        })
            
            print(f"Total citations: {total_citations}")
            print(f"Citations with missing/invalid case names: {len(problematic_citations)}")
            print()
            
            # Analyze the problematic citations
            verified_count = 0
            reporter_first_count = 0
            other_verified_count = 0
            
            print("Citations that should have triggered reporter-first verification:")
            print("-" * 80)
            
            for i, cit in enumerate(problematic_citations[:20]):  # Show first 20
                citation_text = cit['citation']
                extracted_name = cit['extracted_name']
                canonical_name = cit['canonical_name']
                canonical_date = cit['canonical_date']
                verified = cit['verified']
                source = cit['source']
                error = cit['error']
                
                print(f"{i+1:2d}. {citation_text}")
                print(f"    Extracted: '{extracted_name}'")
                print(f"    Canonical: {canonical_name}")
                print(f"    Date: {canonical_date}")
                print(f"    Verified: {verified}")
                print(f"    Source: {source}")
                if error:
                    print(f"    Error: {error}")
                
                if verified:
                    verified_count += 1
                    if source and "reporter-first" in source.lower():
                        reporter_first_count += 1
                        print("    ✅ SUCCESS: Reporter-first verification worked!")
                    else:
                        other_verified_count += 1
                        print("    ⚠️  Verified by another source")
                else:
                    print("    ❌ FAILED: No verification obtained")
                print()
            
            if len(problematic_citations) > 20:
                print(f"... and {len(problematic_citations) - 20} more citations")
                print()
            
            # Summary
            print("=" * 80)
            print("SUMMARY:")
            print(f"Total citations with missing case names: {len(problematic_citations)}")
            print(f"Successfully verified: {verified_count}")
            print(f"Verified via reporter-first: {reporter_first_count}")
            print(f"Verified via other sources: {other_verified_count}")
            print(f"Still unverified: {len(problematic_citations) - verified_count}")
            print()
            
            if reporter_first_count > 0:
                print("✅ Reporter-first verification is WORKING!")
                success_rate = (reporter_first_count / len(problematic_citations)) * 100
                print(f"   Success rate: {success_rate:.1f}% of citations with missing names")
            else:
                print("❌ Reporter-first verification is NOT working")
                if verified_count > 0:
                    print("   (Other verification sources are working, but not reporter-first)")
                else:
                    print("   (No verification at all for citations with missing names)")
            
            # Check some specific examples
            print()
            print("EXAMPLES TO INVESTIGATE:")
            print("-" * 40)
            examples = ["685 P.2d 715", "990 P.2d 1"]
            for cit_text in examples:
                for cit in problematic_citations:
                    if cit['citation'] == cit_text:
                        print(f"{cit_text}: canonical_name={cit['canonical_name']}, verified={cit['verified']}, source='{cit['source']}'")
                        break
            
        else:
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_sp7788_results()
