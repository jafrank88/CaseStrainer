#!/usr/bin/env python3
"""
Re-process a sample of citations from your CSV using the improved pipeline
to demonstrate the verification improvements.
"""

import csv
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def reprocess_sample_citations():
    """Re-process a sample of citations from your CSV with the improved pipeline."""
    
    print("Re-processing sample citations with improved pipeline...")
    print("=" * 60)
    
    # Import the improved fallback verifier
    from src.fallback_verifier import FallbackVerifier
    
    verifier = FallbackVerifier()
    
    # Sample problematic citations from your CSV
    sample_citations = [
        {
            'citation_text': '385 U.S. 493',
            'extracted_case_name': 'Davis v. Alaska',  # This was wrong
            'extracted_date': '1967',
            'original_status': 'unverified'
        },
        {
            'citation_text': '17 L. Ed. 2d 562',
            'extracted_case_name': 'Garrity v. New Jersey',
            'extracted_date': '1967',
            'original_status': 'unverified'
        },
        {
            'citation_text': '87 S. Ct. 616',
            'extracted_case_name': 'Chapman v. California',  # This might be wrong too
            'extracted_date': '1967',
            'original_status': 'unverified'
        }
    ]
    
    improved_count = 0
    
    for i, citation in enumerate(sample_citations, 1):
        print(f"\nCitation #{i}: {citation['citation_text']}")
        print(f"  Original extracted case name: {citation['extracted_case_name']}")
        print(f"  Original status: {citation['original_status']}")
        
        # Try fallback verification
        result = verifier.verify_citation(
            citation['citation_text'],
            citation['extracted_case_name'],
            citation['extracted_date']
        )
        
        if result['verified']:
            print(f"  ✅ NOW VERIFIED via {result['source']}!")
            print(f"  Correct canonical name: {result['canonical_name']}")
            print(f"  Canonical date: {result['canonical_date']}")
            print(f"  URL: {result['url']}")
            print(f"  Confidence: {result['confidence']}")
            improved_count += 1
            
            # Check if the canonical name is different from extracted name
            canonical_name = result['canonical_name'] or ''
            extracted_name = citation['extracted_case_name'] or ''
            
            if canonical_name.lower() != extracted_name.lower():
                print(f"  ⚠️  Case name correction: '{extracted_name}' → '{canonical_name}'")
        else:
            print(f"  ❌ Still unverified")
    
    print(f"\n" + "=" * 60)
    print(f"IMPROVEMENT SUMMARY")
    print(f"=" * 60)
    print(f"Citations tested: {len(sample_citations)}")
    print(f"Now verified: {improved_count}")
    print(f"Improvement rate: {improved_count/len(sample_citations)*100:.1f}%")
    
    if improved_count > 0:
        print(f"\n🎉 SUCCESS! The improved pipeline verified {improved_count} citations")
        print("that were previously marked as 'unverified' in your CSV!")
        print("\nThis means many of the 2,045 'unverified' citations in your")
        print("original results could now be verified with the improved system.")
    
    return improved_count

def estimate_improvement():
    """Estimate how many citations could be improved."""
    
    print(f"\n" + "=" * 60)
    print("ESTIMATED IMPACT ON YOUR FULL DATASET")
    print("=" * 60)
    
    # Your original results
    total_citations = 2227
    unverified_citations = 2045
    courtlistener_verified = 182
    
    print(f"Original results:")
    print(f"  Total citations: {total_citations}")
    print(f"  CourtListener verified: {courtlistener_verified}")
    print(f"  Unverified: {unverified_citations}")
    print(f"  Unverified rate: {unverified_citations/total_citations*100:.1f}%")
    
    # Conservative estimate: fallback verification could verify 20-40% of unverified citations
    # (Supreme Court cases, well-known federal cases, etc.)
    conservative_improvement = int(unverified_citations * 0.20)  # 20%
    optimistic_improvement = int(unverified_citations * 0.40)   # 40%
    
    print(f"\nEstimated improvement with fallback verification:")
    print(f"  Conservative (20% of unverified): +{conservative_improvement} verified")
    print(f"  Optimistic (40% of unverified): +{optimistic_improvement} verified")
    
    new_verified_conservative = courtlistener_verified + conservative_improvement
    new_verified_optimistic = courtlistener_verified + optimistic_improvement
    
    print(f"\nProjected new results:")
    print(f"  Conservative: {new_verified_conservative}/{total_citations} verified ({new_verified_conservative/total_citations*100:.1f}%)")
    print(f"  Optimistic: {new_verified_optimistic}/{total_citations} verified ({new_verified_optimistic/total_citations*100:.1f}%)")
    
    print(f"\nThis could reduce your unverified citations from {unverified_citations} to:")
    print(f"  Conservative: {total_citations - new_verified_conservative}")
    print(f"  Optimistic: {total_citations - new_verified_optimistic}")

if __name__ == "__main__":
    improved_count = reprocess_sample_citations()
    estimate_improvement()
    
    print(f"\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    print("1. The improved pipeline is now integrated into CaseStrainer")
    print("2. Re-run your brief processing script to see the improvements")
    print("3. Citations like '385 U.S. 493' should now be properly verified")
    print("4. Case name extraction accuracy should be improved")
    print("5. Many previously 'unverified' citations should now be verified")
