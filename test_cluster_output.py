from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig
from src.citation_clustering import group_citations_into_clusters

test_text = (
    "A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)"
)

config = ProcessingConfig(
    debug_mode=True,
    extract_case_names=True,
    extract_dates=True,
    enable_verification=True
)
processor = UnifiedCitationProcessorV2(config)
results = processor.process_text(test_text)
clusters = group_citations_into_clusters(results, original_text=test_text)

print("\n--- EXTRACTED CITATIONS ---")
for c in results:
    print(f"Citation: {c.citation} | Extracted Name: {c.extracted_case_name} | Extracted Date: {c.extracted_date}")

print("\n--- RAW CLUSTERS ---")
for idx, cluster in enumerate(clusters):
    print(f"Cluster {idx}: cluster_id={cluster.get('cluster_id', 'N/A')}, canonical_name={cluster.get('canonical_name', 'N/A')}, extracted_case_name={cluster.get('extracted_case_name', 'N/A')}, citations={[c['citation'] for c in cluster['citations']]}")

print("\n--- CLUSTER RESULTS ({} clusters) ---".format(len(clusters)))
for cluster in clusters:
    canonical_name = cluster.get('canonical_name') or 'N/A'
    canonical_date = cluster.get('canonical_date') or 'N/A'
    extracted_name = cluster.get('extracted_case_name') or 'N/A'
    extracted_date = cluster.get('extracted_date') or 'N/A'
    print(f"Canonical Name and Year: {canonical_name}, {canonical_date}")
    print(f"Extracted Name and Year: {extracted_name}, {extracted_date}")
    print(f"Citation Cluster: {', '.join([c['citation'] for c in cluster['citations']])}\n") 