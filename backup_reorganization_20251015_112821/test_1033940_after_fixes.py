"""
Test 1033940.pdf after Fix #63-#67 to see improvements
"""
import requests
import json
import time
from collections import Counter

API_URL = "https://wolf.law.uw.edu/casestrainer/api/analyze"
PDF_FILE = "1033940.pdf"

print("="*80)
print(f"🔍 TESTING 1033940.pdf AFTER FIX #63-#67")
print("="*80)
print("Recent fixes:")
print("  #63: Syntax error fix (verification now running)")
print("  #64: Criminal case party validation")
print("  #65: Source tracking")
print("  #66: Timeout increase (10s → 20s)")
print("  #67: Header contamination filter")
print("")

try:
    with open(PDF_FILE, 'rb') as f:
        files = {'file': (PDF_FILE, f, 'application/pdf')}
        data = {'force_mode': 'sync'}
        
        print("📤 Sending request...")
        start_time = time.time()
        
        response = requests.post(
            API_URL,
            files=files,
            data=data,
            verify=False,
            timeout=300
        )
        
        elapsed = time.time() - start_time
        print(f"✅ Response in {elapsed:.1f}s")
        print(f"Status: {response.status_code}")
        print("")
        
        if response.status_code == 200:
            result = response.json()
            
            # Save results
            with open('test_1033940_after_fixes.json', 'w', encoding='utf-8') as out:
                json.dump(result, out, indent=2, ensure_ascii=False)
            
            stats = result.get('statistics', {})
            clusters = result.get('clusters', [])
            
            print("📊 OVERALL STATS:")
            print(f"   Total Clusters: {stats.get('total_clusters', 0)}")
            print(f"   Total Citations: {stats.get('total_citations', 0)}")
            print(f"   Verified: {stats.get('verified_citations', 0)} ({stats.get('verified_citations', 0)*100//max(stats.get('total_citations', 1), 1)}%)")
            print(f"   Processing Time: {elapsed:.1f}s")
            print("")
            
            # Analyze issues
            print("🔍 ISSUE ANALYSIS:")
            print("="*80)
            
            # Issue 1: Header contamination
            header_clusters = [c for c in clusters if 'CLERK' in c.get('extracted_case_name', '').upper()]
            print(f"1. Header Contamination: {len(header_clusters)} clusters")
            
            # Issue 2: N/A extractions
            na_clusters = [c for c in clusters if c.get('extracted_case_name') == 'N/A']
            print(f"2. N/A Extractions: {len(na_clusters)} clusters ({len(na_clusters)*100//max(len(clusters), 1)}%)")
            
            # Issue 3: Mixed case names in clusters
            mixed_clusters = []
            for cluster in clusters:
                cits = cluster.get('citations', [])
                extracted_names = set(c.get('extracted_case_name', 'N/A') for c in cits if c.get('extracted_case_name'))
                if len(extracted_names) > 1:
                    mixed_clusters.append(cluster)
            print(f"3. Mixed Case Names: {len(mixed_clusters)} clusters")
            
            # Issue 4: Year mismatches
            year_mismatch = 0
            for cluster in clusters:
                cits = cluster.get('citations', [])
                years = set(c.get('extracted_date', 'N/A') for c in cits if c.get('extracted_date'))
                if len(years) > 1 and 'N/A' not in years:
                    year_mismatch += 1
            print(f"4. Year Mismatches: {year_mismatch} clusters")
            
            # Issue 5: Wrong jurisdiction
            wrong_jurisdiction = []
            for cluster in clusters:
                cits = cluster.get('citations', [])
                for cit in cits:
                    canonical_url = cit.get('canonical_url', '')
                    if canonical_url and 'iowa' in canonical_url.lower():
                        wrong_jurisdiction.append(cluster)
                        break
            print(f"5. Wrong Jurisdiction: {len(wrong_jurisdiction)} clusters (Iowa cases)")
            
            print("")
            print("📋 FIRST 10 CLUSTERS:")
            print("="*80)
            
            for i, cluster in enumerate(clusters[:10]):
                print(f"\n--- Cluster {i+1}: {cluster.get('cluster_id')} ---")
                print(f"  Extracted: {cluster.get('extracted_case_name', 'N/A')}")
                print(f"  Canonical: {cluster.get('canonical_name', 'None')}")
                print(f"  Size: {cluster.get('size', 0)} citations")
                
                cits = cluster.get('citations', [])
                for j, cit in enumerate(cits[:3]):  # Show first 3
                    verified = "✅" if cit.get('verified') else "❌"
                    print(f"    {j+1}. {cit.get('text', cit.get('citation'))}: {verified}")
                    
                if len(cits) > 3:
                    print(f"    ... and {len(cits) - 3} more")
            
            print("\n" + "="*80)
            print("📄 Results saved to: test_1033940_after_fixes.json")
            
        else:
            print(f"❌ ERROR: {response.status_code}")
            print(response.text)
            
except FileNotFoundError:
    print(f"❌ ERROR: {PDF_FILE} not found!")
except requests.exceptions.Timeout:
    print("❌ ERROR: Timeout after 5 minutes")
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()




