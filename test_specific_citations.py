#!/usr/bin/env python3
"""
Script to test specific Washington state citations
"""
import json
import time
from citation_verification import CitationVerifier

# List of specific Washington state citations to test
CITATIONS_TO_TEST = [
    "196 Wash. 2d 725",  # Associated Press v. Washington State Legislature
    "190 Wash. 2d 1",    # WPEA v. Washington State Center for Childhood Deafness & Hearing Loss
    "183 Wash. 2d 490",  # State v. Arlene's Flowers
    "178 Wash. 2d 561",  # State v. Saintcalle
    "173 Wash. 2d 477",  # State v. Rice
    "165 Wash. 2d 761",  # Andress v. State
    "159 Wash. 2d 778",  # State v. O'Neill
    "149 Wash. 2d 621",  # State v. Smith
    "139 Wash. 2d 581",  # State v. Gore
    "128 Wash. 2d 254",  # State v. Russell
    
    # Court of Appeals citations
    "196 Wash. App. 138", # State v. Ramirez
    "185 Wash. App. 679", # State v. Johnson
    "175 Wash. App. 119", # State v. Williams
    "165 Wash. App. 732", # State v. Jones
    "155 Wash. App. 83",  # State v. Brown
    
    # First series citations
    "198 Wash. 383",     # State v. Clark
    "185 Wash. 612",     # State v. Davis
    "175 Wash. 547",     # State v. Wilson
    "165 Wash. 326",     # State v. Miller
    "155 Wash. 296"      # State v. Thompson
]

def test_specific_citations():
    """Test the citation verification system on specific Washington state citations."""
    print(f"Testing {len(CITATIONS_TO_TEST)} specific Washington state citations")
    
    # Load API keys from config.json
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            courtlistener_api_key = config.get('courtlistener_api_key')
            langsearch_api_key = config.get('langsearch_api_key')
    except Exception as e:
        print(f"Error loading config.json: {e}")
        courtlistener_api_key = None
        langsearch_api_key = None
    
    # Create the citation verifier
    verifier = CitationVerifier(
        api_key=courtlistener_api_key,
        langsearch_api_key=langsearch_api_key
    )
    
    # Test each citation
    results = []
    for i, citation in enumerate(CITATIONS_TO_TEST):
        print(f"\nTesting citation {i+1}/{len(CITATIONS_TO_TEST)}: {citation}")
        
        # Verify the citation
        result = verifier.verify_citation(citation)
        
        # Print the results
        print(f"Found: {result.get('found')}")
        print(f"Source: {result.get('source')}")
        print(f"Case Name: {result.get('case_name')}")
        
        # Add to results
        results.append({
            'citation': citation,
            'found': result.get('found'),
            'source': result.get('source'),
            'case_name': result.get('case_name'),
            'details': result.get('details', {})
        })
        
        # Sleep to avoid rate limiting
        time.sleep(1)
    
    # Save the verification results
    with open('specific_citation_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print("\nVerification results saved to specific_citation_results.json")
    
    # Count successes and failures
    successes = sum(1 for r in results if r.get('found'))
    failures = sum(1 for r in results if not r.get('found'))
    
    print(f"\nSummary:")
    print(f"  Total citations tested: {len(results)}")
    print(f"  Successfully verified: {successes} ({successes/len(results)*100:.1f}%)")
    print(f"  Failed to verify: {failures} ({failures/len(results)*100:.1f}%)")
    
    # List citations that couldn't be verified
    if failures > 0:
        print("\nCitations that couldn't be verified:")
        for r in results:
            if not r.get('found'):
                print(f"  - {r.get('citation')}")
    
    # List verification methods used
    sources = {}
    for r in results:
        if r.get('found'):
            source = r.get('source')
            sources[source] = sources.get(source, 0) + 1
    
    print("\nVerification methods used:")
    for source, count in sources.items():
        print(f"  - {source}: {count} ({count/successes*100:.1f}%)")
    
    return results

if __name__ == "__main__":
    test_specific_citations()
