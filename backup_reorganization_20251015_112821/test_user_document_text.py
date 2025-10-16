"""Test with user's document by extracting text first"""
import requests
import PyPDF2
import json

pdf_path = "D:/dev/casestrainer/24-2626.pdf"
url = "http://localhost:5000/casestrainer/api/analyze"

print("=" * 80)
print("TESTING USER'S DOCUMENT: 24-2626.pdf (via text extraction)")
print("=" * 80)
print()

# Extract text from PDF
print("[EXTRACTING] Reading PDF...")
with open(pdf_path, 'rb') as f:
    reader = PyPDF2.PdfReader(f)
    text = '\n'.join([page.extract_text() for page in reader.pages])
    print(f"[EXTRACTED] {len(text)} characters from {len(reader.pages)} pages")
    print(f"[SAMPLE] First 200 chars: {text[:200]}")

# Send as text (should force sync processing for smaller chunks)
# Split into first 20KB to force sync
text_chunk = text[:20000]
print(f"\n[SENDING] First 20KB as text to force sync processing...")

response = requests.post(
    url,
    json={'text': text_chunk},
    timeout=180
)

print(f"[STATUS] Response: {response.status_code}")
print()

if response.status_code == 200:
    result = response.json()
    citations = result.get('citations', [])
    clusters = result.get('clusters', [])
    
    print(f"[RESULTS]")
    print(f"  Total Citations: {len(citations)}")
    print(f"  Total Clusters: {len(clusters)}")
    print()
    
    # Check for the specific issues user reported
    print("[CHECKING REPORTED ISSUES]")
    print("-" * 80)
    
    # Issue 1: False clustering of F.3d citations  
    print("\n1. False Clustering Check (783 F.3d, 936 F.3d, 910 F.3d, 897 F.3d):")
    f3d_citations = [c for c in citations if 'F.3d' in c.get('citation', '')]
    f3d_problematic = [c for c in f3d_citations if any(vol in c.get('citation', '') for vol in ['783', '936', '910', '897'])]
    
    if f3d_problematic:
        print(f"  Found {len(f3d_problematic)} F.3d citations:")
        cluster_map = {}
        for cite in f3d_problematic:
            citation_text = cite.get('citation', '')
            case_name = cite.get('extracted_case_name', 'N/A')
            cluster_id = cite.get('cluster_id', 'none')
            print(f"    • {citation_text}: '{case_name}' (cluster: {cluster_id})")
            
            if cluster_id != 'none':
                if cluster_id not in cluster_map:
                    cluster_map[cluster_id] = []
                cluster_map[cluster_id].append(citation_text)
        
        # Check if different volumes are in the same cluster
        print(f"\n  Cluster Analysis:")
        for cluster_id, cites in cluster_map.items():
            print(f"    Cluster {cluster_id}: {', '.join(cites)}")
            if len(cites) > 1:
                print(f"      ⚠️  Multiple F.3d citations in same cluster")
    else:
        print("  No F.3d citations found")
    
    # Issue 2: N/A extractions
    print("\n2. N/A Extraction Check:")
    na_citations = [c for c in citations if c.get('extracted_case_name') == 'N/A']
    truncated_citations = [c for c in citations if c.get('metadata', {}).get('name_may_be_truncated')]
    
    if na_citations:
        print(f"  Found {len(na_citations)} citations with N/A:")
        for cite in na_citations[:5]:
            print(f"    • {cite.get('citation', '')}: N/A")
    else:
        print("  ✅ NO N/A EXTRACTIONS")
    
    if truncated_citations:
        print(f"  Found {len(truncated_citations)} citations flagged as potentially truncated:")
        for cite in truncated_citations[:5]:
            print(f"    • {cite.get('citation', '')}: {cite.get('extracted_case_name', '')} ⚠️")
    
    # Show all citations
    print("\n3. All Citations Found:")
    print("-" * 80)
    for i, cite in enumerate(citations[:20], 1):
        citation_text = cite.get('citation', '')
        case_name = cite.get('extracted_case_name', 'N/A')
        verified = cite.get('verified', False)
        cluster_id = cite.get('cluster_id', 'none')
        flag = '⚠️' if cite.get('metadata', {}).get('name_may_be_truncated') else ''
        v_mark = '✅' if verified else '❌'
        print(f"  {i:2}. {citation_text:25} -> {case_name:40} {flag} {v_mark} (cluster: {cluster_id})")
    
    if len(citations) > 20:
        print(f"  ... and {len(citations) - 20} more")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    na_count = len(na_citations)
    truncated_count = len(truncated_citations)
    print(f"  Citations: {len(citations)}")
    print(f"  N/A: {na_count}")
    print(f"  Truncated (flagged): {truncated_count}")
    print(f"  Clusters: {len(clusters)}")

else:
    print(f"[ERROR] {response.status_code}")
    print(response.text[:500])
