"""
Investigate why incorrect citations are being clustered together
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

import json

print("=" * 80)
print("INVESTIGATING INCORRECT CLUSTERING")
print("=" * 80)

# Load the motion.pdf results if they exist
try:
    with open('D:/dev/casestrainer/output/motion_pdf_results.json', 'r') as f:
        results = json.load(f)
    
    print("\n1. Checking extracted citations...")
    
    # Find the problematic citations
    for citation in results.get('citations', []):
        if '855 F.2d 569' in citation.get('citation', '') or '2022 WL 15153410' in citation.get('citation', ''):
            print(f"\nCitation: {citation.get('citation')}")
            print(f"  Case Name: {citation.get('case_name')}")
            print(f"  Date: {citation.get('date')}")
            print(f"  Context: {citation.get('context', '')[:100]}...")
            
except FileNotFoundError:
    print(" motion.pdf results not found, checking recent processing...")

# Let's also check the clustering logic
print("\n\n2. Analyzing clustering criteria...")
print("-" * 60)

print("\nClustering typically groups citations by:")
print("  a) Similar case names (ignoring common words like 'v.')")
print("  b) Same court/jurisdiction")
print("  c) Close dates (within a few years)")
print("  d) Similar citation patterns")

print("\nFor the two citations:")
print("  1. 2022 WL 15153410 - Doe v. City of New York (2022)")
print("  2. 855 F.2d 569 - [Different case name] (1988)")

print("\n⚠️  These should NOT be clustered because:")
print("  - Different case names")
print("  - 34-year date difference")
print("  - Different citation formats (WL vs F.2d)")

# Check the clustering configuration
print("\n\n3. Checking clustering configuration...")
print("-" * 60)

try:
    from unified_clustering_master import UnifiedClusteringMaster
    
    clusterer = UnifiedClusteringMaster()
    
    # Check similarity threshold
    print(f"Name similarity threshold: {getattr(clusterer, 'name_similarity_threshold', 'Unknown')}")
    print(f"Date difference tolerance: {getattr(clusterer, 'date_tolerance_years', 'Unknown')}")
    print(f"Same court required: {getattr(clusterer, 'require_same_court', 'Unknown')}")
    
except Exception as e:
    print(f"Could not load clustering config: {e}")

print("\n\n4. Possible causes...")
print("-" * 60)
print("1. Case name extraction error - both extracted as 'Doe v. City of New York'")
print("2. Clustering threshold too low (too permissive)")
print("3. Date comparison disabled")
print("4. Court matching not working properly")

print("\n\n5. Let's check the actual case name for 855 F.2d 569...")
print("-" * 60)

# Verify what 855 F.2d 569 actually is
import asyncio
from unified_verification_master import UnifiedVerificationMaster

async def check_citation():
    master = UnifiedVerificationMaster()
    
    # Check 855 F.2d 569
    result = await master.verify_citation("855 F.2d 569")
    
    print(f"\n855 F.2d 569 verification:")
    print(f"  Verified: {result.verified}")
    print(f"  Canonical Name: {result.canonical_name}")
    print(f"  Canonical Date: {result.canonical_date}")
    print(f"  Source: {result.source}")

try:
    asyncio.run(check_citation())
except Exception as e:
    print(f"Could not verify citation: {e}")

print("\n" + "=" * 80)
print("RECOMMENDATION:")
print("-" * 40)
print("The clustering algorithm needs to be stricter about:")
print("1. Case name matching (exact match required for common names like 'Doe')")
print("2. Date differences (should not cluster citations >5 years apart)")
print("3. Citation format differences (WL vs reporter citations)")
print("=" * 80)
