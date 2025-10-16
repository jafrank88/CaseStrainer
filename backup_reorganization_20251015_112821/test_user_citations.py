import PyPDF2
import requests

pdf = open('24-2626.pdf', 'rb')
reader = PyPDF2.PdfReader(pdf)
text = ''.join([p.extract_text() for p in reader.pages])

# Extract the section with the problematic citations (around position 63000-84000)
# This section contains: 783 F.3d, 936 F.3d, 910 F.3d, 897 F.3d, La Liberte
test_section = text[63000:84000]

print("=" * 80)
print("TESTING SECTION WITH USER'S REPORTED CITATIONS")
print("=" * 80)
print(f"Text length: {len(test_section)} chars")
print()

# Split into chunks under 4KB to force sync processing
chunks = []
chunk_size = 3500
for i in range(0, len(test_section), chunk_size):
    chunks.append(test_section[i:i+chunk_size])

print(f"Split into {len(chunks)} chunks for processing")
print()

all_citations = []
all_clusters = []

for i, chunk in enumerate(chunks, 1):
    print(f"[Chunk {i}/{len(chunks)}] Processing {len(chunk)} chars...")
    
    response = requests.post(
        'http://localhost:5000/casestrainer/api/analyze',
        json={'text': chunk},
        timeout=120
    )
    
    if response.status_code == 200:
        result = response.json()
        citations = result.get('citations', [])
        clusters = result.get('clusters', [])
        
        print(f"  Found: {len(citations)} citations, {len(clusters)} clusters")
        all_citations.extend(citations)
        all_clusters.extend(clusters)

print()
print("=" * 80)
print("COMBINED RESULTS")
print("=" * 80)
print(f"Total Citations: {len(all_citations)}")
print(f"Total Clusters: {len(all_clusters)}")
print()

# Check for the specific F.3d citations
print("[CHECKING SPECIFIC CITATIONS]")
print("-" * 80)

target_vols = ['783', '936', '910', '897']
target_cites = []

for cite in all_citations:
    cite_text = cite.get('citation', '')
    if 'F.3d' in cite_text and any(vol in cite_text for vol in target_vols):
        target_cites.append(cite)
        
if target_cites:
    print(f"\nFound {len(target_cites)} target F.3d citations:")
    cluster_map = {}
    
    for cite in target_cites:
        cite_text = cite.get('citation', '')
        case_name = cite.get('extracted_case_name', 'N/A')
        cluster_id = cite.get('cluster_id', 'none')
        truncated = ' ⚠️' if cite.get('metadata', {}).get('name_may_be_truncated') else ''
        
        print(f"  • {cite_text:20} -> {case_name:45} {truncated}(cluster: {cluster_id})")
        
        if cluster_id and cluster_id != 'none':
            if cluster_id not in cluster_map:
                cluster_map[cluster_id] = []
            cluster_map[cluster_id].append(cite_text)
    
    # Check for false clustering
    print(f"\n[CLUSTERING ANALYSIS]")
    print("-" * 80)
    
    if cluster_map:
        for cluster_id, cites in cluster_map.items():
            print(f"\nCluster {cluster_id}:")
            print(f"  Citations: {', '.join(cites)}")
            
            # Check if multiple different F.3d volumes are in same cluster
            f3d_cites = [c for c in cites if 'F.3d' in c]
            if len(f3d_cites) > 1:
                print(f"  ❌ FALSE CLUSTERING! Multiple F.3d citations in same cluster")
                print(f"     These should be separate (different volumes = different cases)")
            else:
                print(f"  ✅ OK - Single citation or valid parallel citations")
    else:
        print("✅ NO CLUSTERING - Each citation is separate")

# Show all extracted case names to check for extraction issues
print(f"\n[ALL CITATIONS EXTRACTED]")
print("-" * 80)
for i, cite in enumerate(all_citations[:30], 1):
    cite_text = cite.get('citation', '')
    case_name = cite.get('extracted_case_name', 'N/A')
    truncated = ' ⚠️' if cite.get('metadata', {}).get('name_may_be_truncated') else ''
    na_flag = ' [N/A]' if case_name == 'N/A' else ''
    print(f"{i:2}. {cite_text:25} -> {case_name:50} {truncated}{na_flag}")

if len(all_citations) > 30:
    print(f"... and {len(all_citations) - 30} more")
