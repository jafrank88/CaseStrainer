import json

# Load the PDF results
with open('D:/dev/casestrainer/pdf_final_output.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Find interesting Supreme Court citations
target_citations = ["497 U.S. 1", "554 U.S. 269", "481 U.S. 465", "496 U.S. 310"]

print("Supreme Court Citation Date Analysis:")
print("=" * 80)

for citation in data.get('citations', []):
    cit_text = citation.get('citation', '')

    if any(target in cit_text for target in target_citations) or ' U.S. ' in cit_text:
        canonical_date = citation.get('canonical_date', 'N/A')
        cluster_year = citation.get('cluster_year', 'N/A')
        extracted_date = citation.get('extracted_date', 'N/A')
        date_mismatch = citation.get('date_mismatch', False)
        canonical_name = citation.get('canonical_name', 'N/A')

        # Extract year from canonical_date if it's a full date
        if canonical_date and canonical_date != 'N/A' and '-' in str(canonical_date):
            canonical_year = canonical_date.split('-')[0]
        else:
            canonical_year = canonical_date

        print(f"\n{cit_text}")
        print(f"  Name: {canonical_name[:60]}")
        print(f"  Canonical Date: {canonical_date}")
        print(f"  Cluster Year: {cluster_year}")
        print(f"  Extracted Date: {extracted_date}")
        print(f"  Date Mismatch: {date_mismatch}")

        # Check if dates match
        if cluster_year and cluster_year != 'N/A' and canonical_year:
            if str(cluster_year) != str(canonical_year):
                print(f"  ⚠️  WARNING: cluster_year ({cluster_year}) != canonical_year ({canonical_year})")

print("\n" + "=" * 80)
print(f"Total citations found: {len(data.get('citations', []))}")
