#!/usr/bin/env python3
"""
Analyze date differences between ToA and main body citations.
Find citations that appear in both sections but have different dates.
"""

import csv
import re
from collections import defaultdict

def extract_citation_text(citation_result_str):
    """Extract the actual citation text from the CitationResult string."""
    # Look for citation='...' pattern
    match = re.search(r"citation='([^']+)'", citation_result_str)
    if match:
        return match.group(1)
    return None

def extract_date(citation_result_str):
    """Extract the extracted_date from the CitationResult string."""
    # Look for extracted_date='...' pattern
    match = re.search(r"extracted_date='([^']*)'", citation_result_str)
    if match:
        date = match.group(1)
        return date if date else None
    return None

def extract_case_name(citation_result_str):
    """Extract the extracted_case_name from the CitationResult string."""
    # Look for extracted_case_name='...' pattern
    match = re.search(r"extracted_case_name='([^']*)'", citation_result_str)
    if match:
        name = match.group(1)
        return name if name else None
    return None

def main():
    """Analyze date differences between ToA and main body citations."""
    
    # Read the CSV file
    citations_by_text = defaultdict(list)
    
    with open('citation_name_date_cluster_report.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            citation_text = extract_citation_text(row['Citation'])
            if citation_text:
                section = row['Section']
                extracted_date = extract_date(row['Citation'])
                extracted_name = extract_case_name(row['Citation'])
                
                citations_by_text[citation_text].append({
                    'section': section,
                    'date': extracted_date,
                    'name': extracted_name,
                    'full_row': row
                })
    
    # Find citations that appear in both sections
    print("=== CITATIONS IN BOTH TOA AND MAIN BODY ===\n")
    
    date_differences = []
    same_dates = []
    
    for citation_text, entries in citations_by_text.items():
        if len(entries) > 1:
            toa_entries = [e for e in entries if e['section'] == 'ToA']
            main_body_entries = [e for e in entries if e['section'] == 'Main Body']
            
            if toa_entries and main_body_entries:
                # Get unique dates from each section
                toa_dates = set(e['date'] for e in toa_entries if e['date'])
                main_body_dates = set(e['date'] for e in main_body_entries if e['date'])
                
                # Get unique names from each section
                toa_names = set(e['name'] for e in toa_entries if e['name'])
                main_body_names = set(e['name'] for e in main_body_entries if e['name'])
                
                print(f"Citation: {citation_text}")
                print(f"  ToA dates: {sorted(toa_dates) if toa_dates else ['None']}")
                print(f"  Main Body dates: {sorted(main_body_dates) if main_body_dates else ['None']}")
                print(f"  ToA names: {sorted(toa_names) if toa_names else ['None']}")
                print(f"  Main Body names: {sorted(main_body_names) if main_body_names else ['None']}")
                
                # Check for date differences
                if toa_dates and main_body_dates and toa_dates != main_body_dates:
                    date_differences.append({
                        'citation': citation_text,
                        'toa_dates': toa_dates,
                        'main_body_dates': main_body_dates,
                        'toa_names': toa_names,
                        'main_body_names': main_body_names
                    })
                    print(f"  *** DATE DIFFERENCE DETECTED ***")
                elif toa_dates and main_body_dates and toa_dates == main_body_dates:
                    same_dates.append({
                        'citation': citation_text,
                        'dates': toa_dates,
                        'toa_names': toa_names,
                        'main_body_names': main_body_names
                    })
                    print(f"  ✓ Dates match")
                else:
                    print(f"  - One or both sections missing dates")
                
                print()
    
    # Summary
    print(f"\n=== SUMMARY ===")
    print(f"Total citations in both sections: {len([c for c in citations_by_text.values() if len(c) > 1 and any(e['section'] == 'ToA' for e in c) and any(e['section'] == 'Main Body' for e in c)])}")
    print(f"Citations with matching dates: {len(same_dates)}")
    print(f"Citations with different dates: {len(date_differences)}")
    
    if date_differences:
        print(f"\n=== DETAILED DATE DIFFERENCES ===")
        for diff in date_differences:
            print(f"\nCitation: {diff['citation']}")
            print(f"  ToA dates: {sorted(diff['toa_dates'])}")
            print(f"  Main Body dates: {sorted(diff['main_body_dates'])}")
            print(f"  ToA names: {sorted(diff['toa_names']) if diff['toa_names'] else ['None']}")
            print(f"  Main Body names: {sorted(diff['main_body_names']) if diff['main_body_names'] else ['None']}")
    
    # Save detailed results to file
    with open('date_difference_analysis.txt', 'w', encoding='utf-8') as f:
        f.write("=== DATE DIFFERENCE ANALYSIS ===\n\n")
        f.write(f"Total citations in both sections: {len([c for c in citations_by_text.values() if len(c) > 1 and any(e['section'] == 'ToA' for e in c) and any(e['section'] == 'Main Body' for e in c)])}\n")
        f.write(f"Citations with matching dates: {len(same_dates)}\n")
        f.write(f"Citations with different dates: {len(date_differences)}\n\n")
        
        if date_differences:
            f.write("=== CITATIONS WITH DIFFERENT DATES ===\n\n")
            for diff in date_differences:
                f.write(f"Citation: {diff['citation']}\n")
                f.write(f"  ToA dates: {sorted(diff['toa_dates'])}\n")
                f.write(f"  Main Body dates: {sorted(diff['main_body_dates'])}\n")
                f.write(f"  ToA names: {sorted(diff['toa_names']) if diff['toa_names'] else ['None']}\n")
                f.write(f"  Main Body names: {sorted(diff['main_body_names']) if diff['main_body_names'] else ['None']}\n\n")
        
        if same_dates:
            f.write("=== CITATIONS WITH MATCHING DATES ===\n\n")
            for same in same_dates:
                f.write(f"Citation: {same['citation']}\n")
                f.write(f"  Dates: {sorted(same['dates'])}\n")
                f.write(f"  ToA names: {sorted(same['toa_names']) if same['toa_names'] else ['None']}\n")
                f.write(f"  Main Body names: {sorted(same['main_body_names']) if same['main_body_names'] else ['None']}\n\n")
    
    print(f"\nDetailed analysis saved to: date_difference_analysis.txt")

if __name__ == "__main__":
    main() 