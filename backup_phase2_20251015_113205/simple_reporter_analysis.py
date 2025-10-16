#!/usr/bin/env python3
"""
Simple reporter analysis to avoid PowerShell truncation issues.
"""

import csv
from collections import Counter
import re

def extract_reporter(citation):
    """Extract reporter from citation."""
    match = re.search(r'\d+\s+([A-Za-z\.]+(?:\s+[A-Za-z\.]*)*)\s+\d+', citation)
    return match.group(1).strip() if match else 'Unknown'

def main():
    # Read files
    try:
        with open('non_courtlistener_citations_20250728_215223.csv', 'r', encoding='utf-8') as f:
            original = list(csv.DictReader(f))
        
        with open('non_courtlistener_citations_20250729_174752.csv', 'r', encoding='utf-8') as f:
            new_unverified = list(csv.DictReader(f))
    except Exception as e:
        print(f"Error reading files: {e}")
        return

    # Calculate differences
    new_citations = {row['citation_text'] for row in new_unverified}
    fallback_verified = [row for row in original if row['citation_text'] not in new_citations]

    print("COMPLETE REPORTER ANALYSIS")
    print("=" * 70)
    print(f"Original unverified citations: {len(original):,}")
    print(f"Still unverified citations:    {len(new_unverified):,}")
    print(f"Verified by fallback sources:  {len(fallback_verified):,}")
    print()

    # Analyze fallback verified reporters
    fallback_reporters = Counter()
    for row in fallback_verified:
        reporter = extract_reporter(row['citation_text'])
        fallback_reporters[reporter] += 1

    print("REPORTERS NOT FOUND IN COURTLISTENER (verified by fallback):")
    print("-" * 70)
    total_fallback = len(fallback_verified)
    for reporter, count in fallback_reporters.most_common():
        percentage = (count / total_fallback) * 100
        print(f"{reporter:25} {count:4d} citations ({percentage:5.1f}%)")

    print()
    print("STILL UNVERIFIED REPORTERS:")
    print("-" * 70)
    still_unverified_reporters = Counter()
    for row in new_unverified:
        reporter = extract_reporter(row['citation_text'])
        still_unverified_reporters[reporter] += 1

    total_unverified = len(new_unverified)
    for reporter, count in still_unverified_reporters.most_common():
        percentage = (count / total_unverified) * 100
        print(f"{reporter:25} {count:4d} citations ({percentage:5.1f}%)")

    print()
    print("KEY INSIGHTS:")
    print("=" * 70)
    
    # Top gaps in CourtListener
    top_gaps = fallback_reporters.most_common(5)
    print("Biggest CourtListener coverage gaps:")
    for reporter, count in top_gaps:
        print(f"  • {reporter}: {count:,} citations missing from CourtListener")
    
    # Washington state analysis
    wa_reporters = ['Wn.', 'Wn. App.', 'Wn.App.', 'Wash.App.', 'Wash.']
    wa_total = sum(fallback_reporters.get(r, 0) for r in wa_reporters)
    print(f"\nWashington State total: {wa_total:,} citations ({wa_total/total_fallback*100:.1f}% of fallback)")
    
    # Supreme Court analysis  
    sc_reporters = ['U.S.', 'S. Ct.', 'L. Ed.', 'L.ed.', 's.ct.']
    sc_total = sum(fallback_reporters.get(r, 0) for r in sc_reporters)
    print(f"Supreme Court total: {sc_total:,} citations ({sc_total/total_fallback*100:.1f}% of fallback)")

if __name__ == "__main__":
    main()
