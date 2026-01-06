import requests
import json
from datetime import datetime

# Process the motion.pdf file directly
print("=" * 80)
print("CASESTRAINER DOCUMENT ANALYSIS REPORT")
print("=" * 80)
print(f"Document: motion.pdf")
print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Make the API request
with open('D:/dev/casestrainer/motion.pdf', 'rb') as f:
    files = {'file': ('motion.pdf', f, 'application/pdf')}
    response = requests.post('http://localhost:5000/casestrainer/api/analyze', files=files)
    
    if response.status_code == 200:
        data = response.json()
        
        # Summary statistics
        citations = data['citations']
        clusters = data.get('clusters', [])
        
        print("SUMMARY STATISTICS:")
        print("-" * 40)
        print(f"Text Length: {data['metadata']['text_length']:,} characters")
        print(f"Processing Mode: {data['metadata']['processing_mode']}")
        print(f"Extraction Method: {data['metadata']['extraction_method']}")
        print(f"Total Citations Found: {len(citations)}")
        print(f"Total Clusters Formed: {len(clusters)}")
        print(f"Verified Citations: {sum(1 for c in citations if c.get('verified', False))}")
        print(f"Citations with Case Names: {sum(1 for c in citations if c.get('extracted_case_name') and c.get('extracted_case_name') != 'N/A')}")
        print(f"Citations with Dates: {sum(1 for c in citations if c.get('extracted_date') and c.get('extracted_date') != 'N/A')}")
        print()

        # Issues found
        print("ISSUES IDENTIFIED:")
        print("-" * 40)
        
        issues = []
        
        # Check for N/A values
        na_case_names = [c for c in citations if c.get('extracted_case_name') == 'N/A']
        if na_case_names:
            issues.append(f"❌ {len(na_case_names)} citations with 'N/A' case names")
        
        # Check for missing dates
        missing_dates = [c for c in citations if not c.get('extracted_date') or c.get('extracted_date') == 'N/A']
        if missing_dates:
            issues.append(f"⚠️  {len(missing_dates)} citations missing dates")
        
        # Check verification status
        unverified = [c for c in citations if not c.get('verified', False)]
        if len(unverified) == len(citations):
            issues.append(f"❌ ALL citations are unverified")
        
        # Check for canonical data
        missing_canonical = [c for c in citations if not c.get('canonical_name')]
        if len(missing_canonical) == len(citations):
            issues.append("❌ NO citations have canonical data (from verification sources)")
        
        if issues:
            for issue in issues:
                print(issue)
        else:
            print("✅ No major issues detected")
        print()

        # Citation details
        print("CITATION DETAILS (First 10):")
        print("-" * 40)
        
        for i, citation in enumerate(citations[:10], 1):
            print(f"\n{i}. {citation['citation']}")
            print(f"   Case Name: {citation.get('extracted_case_name', 'N/A')}")
            print(f"   Date: {citation.get('extracted_date', 'N/A')}")
            print(f"   Verified: {citation.get('verified', False)}")
            print(f"   Court: {citation.get('court', 'N/A')}")
            print(f"   Cluster: {citation.get('cluster_id', 'None')}")
        
        if len(citations) > 10:
            print(f"\n... and {len(citations) - 10} more citations")
        
        # Cluster analysis
        if clusters:
            print("\n\nCLUSTER ANALYSIS:")
            print("-" * 40)
            for i, cluster in enumerate(clusters[:5], 1):
                print(f"\nCluster {i}: {cluster.get('cluster_case_name', 'N/A')}")
                print(f"  Year: {cluster.get('cluster_year', 'N/A')}")
                print(f"  Size: {cluster.get('cluster_size', 0)} citations")
                print(f"  Members: {', '.join(cluster.get('cluster_members', [])[:3])}")
        
        # What's not working
        print("\n\nWHAT DID NOT WORK:")
        print("-" * 40)
        print("1. Verification System: All citations are marked as 'not_verified'")
        print("   - This could be due to verification being disabled or sources unavailable")
        print()
        print("2. Canonical Data Missing: No citations have canonical_name or canonical_date")
        print("   - Verification sources (CourtListener, CaseMine, etc.) not returning data")
        print()
        if na_case_names:
            print("3. Some Case Names Missing or N/A:")
            for c in na_case_names[:3]:
                print(f"   - {c['citation']}: Case name could not be extracted")
            print()
        print("4. Limited Clustering: Most citations are not being grouped into parallel clusters")
        print("   - Most citations have cluster_id as null or are in clusters of size 1")
        print()
        print("5. Court Information Missing: Most citations lack court identification")
        print("   - This affects the ability to distinguish between similar citations")
        
        print("\n\nRECOMMENDATIONS:")
        print("-" * 40)
        print("1. Check if verification is enabled in the configuration")
        print("2. Verify API keys for CourtListener and other sources are valid")
        print("3. Review case name extraction patterns for citations showing 'N/A'")
        print("4. Investigate why parallel citation detection is not working effectively")
        print("5. Check if court identification patterns need updating")
        
        # Show specific examples of problematic citations
        print("\n\nPROBLEMATIC CITATIONS:")
        print("-" * 40)
        problem_citations = []
        for c in citations:
            if c.get('extracted_case_name') == 'N/A' or not c.get('extracted_date'):
                problem_citations.append(c)
        
        for i, c in enumerate(problem_citations[:5], 1):
            print(f"{i}. {c['citation']}")
            print(f"   Case Name: {c.get('extracted_case_name', 'Missing')}")
            print(f"   Date: {c.get('extracted_date', 'Missing')}")
            print(f"   Index: {c.get('start_index')} - {c.get('end_index')}")
        
    else:
        print(f"Error: API returned status code {response.status_code}")
        print(response.text)

print("\n" + "=" * 80)
