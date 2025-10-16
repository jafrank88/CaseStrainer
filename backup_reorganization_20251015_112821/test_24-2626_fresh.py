"""Re-test 24-2626 with fresh backend after deploying fixes"""
import requests
import json

pdf_path = "D:/dev/casestrainer/24-2626.pdf"
url = "http://localhost:5000/casestrainer/api/analyze"

print("=" * 80)
print("RE-TESTING 24-2626.pdf WITH FRESH BACKEND")
print("=" * 80)
print()

# Upload the PDF
with open(pdf_path, 'rb') as f:
    files = {'file': ('24-2626.pdf', f, 'application/pdf')}
    
    print("[UPLOAD] Uploading 24-2626.pdf to fresh backend...")
    response = requests.post(url, files=files, timeout=300)

print(f"[STATUS] Response: {response.status_code}")

if response.status_code == 200:
    result = response.json()
    
    # Check if async
    processing_mode = result.get('metadata', {}).get('processing_mode', 'immediate')
    if processing_mode == 'queued':
        print("[INFO] Document queued for async processing")
        print("[INFO] Results will appear in the frontend when complete")
        print()
        print("Please check the frontend in ~30-60 seconds")
    else:
        citations = result.get('citations', [])
        clusters = result.get('clusters', [])
        
        print(f"\n[RESULTS]")
        print(f"  Total Citations: {len(citations)}")
        print(f"  Total Clusters: {len(clusters)}")
        print()
        
        # Check for the false clustering issue
        print("[CHECKING FALSE CLUSTERING ISSUE]")
        print("-" * 80)
        
        # Find clusters with multiple F.3d citations
        for cluster in clusters:
            cluster_citations = cluster.get('citations', [])
            f3d_cites = [c for c in cluster_citations if 'F.3d' in c.get('text', '')]
            
            if len(f3d_cites) > 1:
                case_name = cluster.get('case_name', 'N/A')
                print(f"\n⚠️  CLUSTER with multiple F.3d:")
                print(f"  Case Name: {case_name}")
                print(f"  Citations: {[c.get('text') for c in f3d_cites]}")
                
                # Check if they're different volumes
                volumes = set()
                for cite in f3d_cites:
                    text = cite.get('text', '')
                    if ' F.3d ' in text:
                        vol = text.split(' F.3d ')[0].strip()
                        volumes.add(vol)
                
                if len(volumes) > 1:
                    print(f"  ❌ FALSE CLUSTERING! Different volumes: {volumes}")
                else:
                    print(f"  ✅ OK - Same volume (likely parallel)")
        
        # Check for contaminated case names
        print("\n[CHECKING CASE NAME CONTAMINATION]")
        print("-" * 80)
        
        contaminated = []
        for cite in citations[:20]:
            case_name = cite.get('extracted_case_name', '')
            if 'GOPHER MEDIA' in case_name or 'MELONE' in case_name:
                contaminated.append({
                    'citation': cite.get('citation', ''),
                    'name': case_name
                })
        
        if contaminated:
            print(f"\n⚠️  Found {len(contaminated)} citations with contaminated names:")
            for item in contaminated[:5]:
                print(f"  {item['citation']:25} -> {item['name'][:60]}")
        else:
            print("✅ No contamination detected in first 20 citations")
        
        # Check for truncation
        print("\n[CHECKING TRUNCATION]")
        print("-" * 80)
        
        truncated = []
        for cite in citations:
            case_name = cite.get('extracted_case_name', '')
            # Check for common truncation patterns
            if (len(case_name) < 10 and case_name not in ['N/A', '']) or \
               case_name.endswith(' v.') or \
               case_name.startswith('v. ') or \
               case_name.count('.') > 5:
                truncated.append({
                    'citation': cite.get('citation', ''),
                    'name': case_name
                })
        
        if truncated:
            print(f"\n⚠️  Found {len(truncated)} potentially truncated names:")
            for item in truncated[:5]:
                print(f"  {item['citation']:25} -> '{item['name']}'")
        else:
            print("✅ No obvious truncation detected")

else:
    print(f"[ERROR] {response.status_code}")
    print(response.text[:500])

print("\n" + "=" * 80)
print("TEST COMPLETE - Check frontend for full results")
print("=" * 80)
