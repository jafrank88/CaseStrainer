"""
Test CaseStrainer with real Washington briefs containing Tables of Authorities
"""
import requests
import json
import time
import os
from collections import Counter

API_URL = "https://wolf.law.uw.edu/casestrainer/api/analyze"
BRIEFS_DIR = "D:\\dev\\casestrainer\\wa_briefs"

# Test briefs that previously timed out (now with 600s timeout)
TEST_BRIEFS = [
    "002_Petition for Review.pdf",
    "003_COA  Appellant Brief.pdf",
    "019_Defendant Brief.pdf",
]

def test_brief(filename):
    """Test a single brief"""
    filepath = os.path.join(BRIEFS_DIR, filename)
    
    print(f"\n{'='*80}")
    print(f"📄 TESTING: {filename}")
    print('='*80)
    
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return None
    
    try:
        print(f"📂 Opening file: {filepath}")
        print(f"📏 File size: {os.path.getsize(filepath):,} bytes")
        
        with open(filepath, 'rb') as f:
            file_content = f.read()
            print(f"✅ File read successfully: {len(file_content):,} bytes")
            
        # Re-open for sending (avoid file handle closure issues)
        with open(filepath, 'rb') as f:
            files = {'file': (filename, f, 'application/pdf')}
            data = {'force_mode': 'sync'}
            
            print(f"📤 Sending to API: {API_URL}")
            print(f"   Filename: {filename}")
            start_time = time.time()
            
            response = requests.post(
                API_URL,
                files=files,
                data=data,
                verify=False,
                timeout=600  # 10 minute timeout for large briefs
            )
            print(f"📨 Response received: Status {response.status_code}")
            
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                stats = result.get('statistics', {})
                clusters = result.get('clusters', [])
                
                print(f"✅ SUCCESS ({elapsed:.1f}s)")
                print(f"\n📊 STATISTICS:")
                print(f"   Total Clusters: {stats.get('total_clusters', 0)}")
                print(f"   Total Citations: {stats.get('total_citations', 0)}")
                print(f"   Verified: {stats.get('verified_citations', 0)} ({stats.get('verified_citations', 0)*100//max(stats.get('total_citations', 1), 1)}%)")
                
                # Analyze quality
                header_contam = sum(1 for c in clusters if 'CLERK' in c.get('extracted_case_name', '').upper() or 'TABLE OF' in c.get('extracted_case_name', '').upper())
                na_extractions = sum(1 for c in clusters if c.get('extracted_case_name') == 'N/A')
                mixed_clusters = 0
                for cluster in clusters:
                    cits = cluster.get('citations', [])
                    names = set(c.get('extracted_case_name', 'N/A') for c in cits if c.get('extracted_case_name'))
                    if len(names) > 1:
                        mixed_clusters += 1
                
                print(f"\n🔍 QUALITY CHECKS:")
                print(f"   Header Contamination: {header_contam} clusters")
                print(f"   N/A Extractions: {na_extractions} ({na_extractions*100//max(len(clusters), 1)}%)")
                print(f"   Mixed Case Names: {mixed_clusters} clusters")
                
                # Show sample of extractions
                print(f"\n📋 SAMPLE EXTRACTIONS (First 5):")
                for i, cluster in enumerate(clusters[:5]):
                    extracted = cluster.get('extracted_case_name', 'N/A')
                    verified = cluster.get('canonical_name', 'None')
                    size = cluster.get('size', 0)
                    v_count = sum(1 for c in cluster.get('citations', []) if c.get('verified'))
                    print(f"   {i+1}. {extracted[:60]}... ({size} cits, {v_count} verified)")
                
                # Save results
                safe_filename = filename.replace(' ', '_').replace('.pdf', '')
                output_file = f"test_wa_briefs_{safe_filename}.json"
                with open(output_file, 'w', encoding='utf-8') as out:
                    json.dump(result, out, indent=2, ensure_ascii=False)
                print(f"\n📁 Full results: {output_file}")
                
                return {
                    'success': True,
                    'filename': filename,
                    'elapsed': elapsed,
                    'total_clusters': len(clusters),
                    'total_citations': stats.get('total_citations', 0),
                    'verified': stats.get('verified_citations', 0),
                    'header_contam': header_contam,
                    'na_extractions': na_extractions,
                    'mixed_clusters': mixed_clusters
                }
            else:
                print(f"❌ ERROR: HTTP {response.status_code}")
                print(response.text[:500])
                return {'success': False, 'filename': filename}
                
    except requests.exceptions.Timeout:
        print(f"❌ TIMEOUT after 5 minutes")
        return {'success': False, 'filename': filename, 'error': 'timeout'}
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'filename': filename, 'error': str(e)}

# Run tests
print("="*80)
print("🧪 TESTING CASESTRAINER WITH WA BRIEFS")
print("="*80)
print(f"Testing {len(TEST_BRIEFS)} representative briefs...")
print("These briefs contain Tables of Authorities for validation")

results = []
for brief in TEST_BRIEFS:
    result = test_brief(brief)
    if result:
        results.append(result)
    time.sleep(2)  # Brief pause between tests

# Summary
print("\n" + "="*80)
print("📊 OVERALL SUMMARY")
print("="*80)

successful = [r for r in results if r.get('success')]
failed = [r for r in results if not r.get('success')]

print(f"\n✅ Successful: {len(successful)}/{len(results)}")
print(f"❌ Failed: {len(failed)}/{len(results)}")

if successful:
    print(f"\n📈 AGGREGATE STATISTICS:")
    total_clusters = sum(r['total_clusters'] for r in successful)
    total_citations = sum(r['total_citations'] for r in successful)
    total_verified = sum(r['verified'] for r in successful)
    total_contam = sum(r['header_contam'] for r in successful)
    total_na = sum(r['na_extractions'] for r in successful)
    total_mixed = sum(r['mixed_clusters'] for r in successful)
    avg_time = sum(r['elapsed'] for r in successful) / len(successful)
    
    print(f"   Total Clusters: {total_clusters}")
    print(f"   Total Citations: {total_citations}")
    print(f"   Verified Rate: {total_verified}/{total_citations} ({total_verified*100//max(total_citations, 1)}%)")
    print(f"   Avg Processing Time: {avg_time:.1f}s")
    print(f"\n🔍 QUALITY METRICS:")
    print(f"   Header Contamination: {total_contam} clusters ({total_contam*100//max(total_clusters, 1)}%)")
    print(f"   N/A Extractions: {total_na} clusters ({total_na*100//max(total_clusters, 1)}%)")
    print(f"   Mixed Clusters: {total_mixed} clusters ({total_mixed*100//max(total_clusters, 1)}%)")

if failed:
    print(f"\n❌ FAILED BRIEFS:")
    for r in failed:
        print(f"   - {r['filename']}: {r.get('error', 'unknown error')}")

print("\n" + "="*80)
print("✅ Testing complete!")
print("="*80)

