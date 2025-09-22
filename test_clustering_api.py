#!/usr/bin/env python3

import requests
import json

def test_clustering_api():
    """Test API with multiple different cases to trigger clustering."""
    
    # Text with multiple different cases that should form clusters
    text = """
    The Supreme Court held in Spokeo, Inc. v. Robins, 136 S. Ct. 1540, 194 L. Ed. 2d 635 (2016) that standing requirements cannot be erased.
    
    In Raines v. Byrd, 521 U.S. 811, 117 S. Ct. 2312, 138 L. Ed. 2d 849 (1997), the Court addressed legislative standing.
    
    The decision in Brown v. Board of Education, 347 U.S. 483, 74 S. Ct. 686, 98 L. Ed. 873 (1954) was landmark.
    """
    
    print("CLUSTERING API TEST")
    print("=" * 50)
    print(f"Text: {text[:100]}...")
    print()
    
    # Make API request
    url = "http://localhost:5000/casestrainer/api/analyze"
    data = {"text": text, "type": "text"}
    
    try:
        response = requests.post(url, data=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('citations', [])
            clusters = result.get('clusters', [])
            
            print(f"Found {len(citations)} citations:")
            print(f"Found {len(clusters)} clusters:")
            print()
            
            # Group citations by case name to see clustering
            case_groups = {}
            for i, citation in enumerate(citations, 1):
                citation_text = citation.get('citation', 'N/A')
                case_name = citation.get('case_name', 'N/A')
                extracted_case_name = citation.get('extracted_case_name', 'N/A')
                cluster_case_name = citation.get('cluster_case_name', 'N/A')
                canonical_name = citation.get('canonical_name', 'N/A')
                verified = citation.get('verified', False)
                true_by_parallel = citation.get('true_by_parallel', False)
                
                if case_name not in case_groups:
                    case_groups[case_name] = []
                case_groups[case_name].append({
                    'citation': citation_text,
                    'cluster_case_name': cluster_case_name,
                    'extracted_case_name': extracted_case_name,
                    'canonical_name': canonical_name,
                    'verified': verified,
                    'true_by_parallel': true_by_parallel
                })
            
            # Display results grouped by case name
            for case_name, group_citations in case_groups.items():
                print(f"CASE: {case_name}")
                print(f"  Citations in this group: {len(group_citations)}")
                for cit in group_citations:
                    print(f"    - {cit['citation']}")
                    print(f"      cluster_case_name: '{cit['cluster_case_name']}'")
                    print(f"      extracted_case_name: '{cit['extracted_case_name']}'")
                    print(f"      canonical_name: '{cit['canonical_name']}'")
                    print(f"      verified: {cit['verified']}, true_by_parallel: {cit['true_by_parallel']}")
                print()
            
            # Check for clustering issues
            spokeo_citations = [c for c in citations if 'Spokeo' in c.get('case_name', '')]
            raines_citations = [c for c in citations if 'Raines' in c.get('case_name', '')]
            brown_citations = [c for c in citations if 'Brown' in c.get('case_name', '')]
            
            print("CLUSTERING ANALYSIS:")
            print(f"Spokeo citations: {len(spokeo_citations)}")
            print(f"Raines citations: {len(raines_citations)}")
            print(f"Brown citations: {len(brown_citations)}")
            
            # Check if parallel citations are properly marked
            for case_name, group_citations in case_groups.items():
                if len(group_citations) > 1:
                    parallel_count = sum(1 for c in group_citations if c['true_by_parallel'])
                    print(f"{case_name}: {len(group_citations)} citations, {parallel_count} marked as true_by_parallel")
                    
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_clustering_api()
