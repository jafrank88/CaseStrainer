import json

def analyze_paragraph_results():
    try:
        with open('paragraph_analysis_response.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        result = data['result']
        citations = result['citations']
        clusters = result['clusters']
        metadata = result['metadata']
        
        print("=" * 80)
        print("CITATION PARAGRAPH ANALYSIS RESULTS")
        print("=" * 80)
        
        print(f"Total citations found: {len(citations)}")
        print(f"Clusters created: {len(clusters)}")
        print(f"Processing strategy: {metadata.get('processing_strategy', 'N/A')}")
        print(f"Processing mode: {metadata.get('processing_mode', 'N/A')}")
        print(f"Text length: {metadata.get('text_length', 'N/A')} characters")
        
        print("\nCITATIONS FOUND:")
        print("-" * 40)
        
        for i, citation in enumerate(citations, 1):
            print(f"{i}. {citation['citation']}")
            print(f"   Case: {citation['extracted_case_name']}")
            print(f"   Year: {citation['extracted_date']}")
            print(f"   Verified: {citation['verified']}")
            print(f"   Method: {citation['method']}")
            print(f"   Confidence: {citation['confidence']}")
            print()
        
        print("ANALYSIS:")
        print("-" * 40)
        
        # Why no clusters?
        if len(citations) > 1 and len(clusters) == 0:
            print("WHY NO CLUSTERS WERE CREATED:")
            
            # Check for same case citations
            case_groups = {}
            for citation in citations:
                case_name = citation['extracted_case_name']
                if case_name not in case_groups:
                    case_groups[case_name] = []
                case_groups[case_name].append(citation)
            
            print(f"- Found {len(case_groups)} unique cases")
            for case_name, case_citations in case_groups.items():
                if len(case_citations) > 1:
                    print(f"  * {case_name}: {len(case_citations)} citations (should cluster)")
                    for c in case_citations:
                        print(f"    - {c['citation']}")
                else:
                    print(f"  * {case_name}: 1 citation (no clustering needed)")
            
            print("\nPossible reasons for no clustering:")
            print("1. Clustering algorithm may require exact case name matches")
            print("2. Citations from same case may not meet similarity threshold")
            print("3. Processing strategy may have clustering disabled")
            print("4. Clustering may only work with larger datasets")
        
        # Why no verification?
        verified_count = sum(1 for c in citations if c['verified'])
        if verified_count == 0:
            print(f"\nWHY NO CITATIONS WERE VERIFIED:")
            print("- All 4 citations show 'verified: false'")
            print("- canonical_url is null for all citations")
            print("- canonical_name is null for all citations")
            print("\nPossible reasons:")
            print("1. CourtListener API key may be missing or invalid")
            print("2. Citations may not exist in CourtListener database")
            print("3. Citation format may not match database entries")
            print("4. Verification service may be temporarily unavailable")
            print("5. Network connectivity issues to CourtListener API")
            
            print(f"\nCitations that should be verifiable:")
            for citation in citations:
                print(f"- {citation['citation']} ({citation['extracted_case_name']}, {citation['extracted_date']})")
        
        print("=" * 80)
        
    except FileNotFoundError:
        print("Error: paragraph_analysis_response.json not found")
    except Exception as e:
        print(f"Error analyzing results: {e}")

if __name__ == "__main__":
    analyze_paragraph_results()
