#!/usr/bin/env python3
"""
Create a detailed comparison report showing ToA vs main body extraction.
Format: 4 lines per entry showing original text and extracted data.
"""

import csv
import re
from collections import defaultdict

def extract_citation_text(citation_result_str):
    """Extract the actual citation text from the CitationResult string."""
    match = re.search(r"citation='([^']+)'", citation_result_str)
    if match:
        return match.group(1)
    return None

def extract_date(citation_result_str):
    """Extract the extracted_date from the CitationResult string."""
    match = re.search(r"extracted_date='([^']*)'", citation_result_str)
    if match:
        return match.group(1) if match.group(1) != 'None' else None
    return None

def extract_name(citation_result_str):
    """Extract the extracted_case_name from the CitationResult string."""
    match = re.search(r"extracted_case_name='([^']*)'", citation_result_str)
    if match:
        return match.group(1) if match.group(1) != 'None' else None
    return None

def main():
    # Read the CSV data
    toa_citations = {}  # citation_text -> (toa_name, toa_year, toa_line)
    main_body_citations = {}  # citation_text -> (extracted_name, extracted_date, context)
    
    with open('citation_name_date_cluster_report.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            section = row['Section']
            citation = row['Citation']
            
            if section == 'ToA':
                toa_name = row['ToA Name'] if row['ToA Name'] else 'None'
                toa_year = row['ToA Year'] if row['ToA Year'] else 'None'
                # We need to find the original ToA line - for now use a placeholder
                toa_line = f"ToA line for: {citation}"
                toa_citations[citation] = (toa_name, toa_year, toa_line)
                
            elif section == 'Main Body':
                extracted_name = row['Extracted Name'] if row['Extracted Name'] else 'None'
                extracted_date = row['Extracted Date'] if row['Extracted Date'] else 'None'
                # We need to find the context - for now use a placeholder
                context = f"Context for: {citation}"
                main_body_citations[citation] = (extracted_name, extracted_date, context)
    
    # Find citations that appear in both sections
    common_citations = set(toa_citations.keys()) & set(main_body_citations.keys())
    
    # Generate detailed report
    print("DETAILED COMPARISON REPORT: ToA vs Main Body Extraction")
    print("=" * 80)
    print()
    
    with open('detailed_comparison_report.txt', 'w', encoding='utf-8') as f:
        f.write("DETAILED COMPARISON REPORT: ToA vs Main Body Extraction\n")
        f.write("=" * 80 + "\n\n")
        
        for i, citation in enumerate(sorted(common_citations), 1):
            toa_name, toa_year, toa_line = toa_citations[citation]
            mb_name, mb_date, mb_context = main_body_citations[citation]
            
            # Check if dates are different
            date_diff = ""
            if toa_year != 'None' and mb_date != 'None' and toa_year != mb_date:
                try:
                    toa_int = int(toa_year)
                    mb_int = int(mb_date)
                    diff = abs(toa_int - mb_int)
                    date_diff = f" [DIFFERENCE: {diff} years]"
                except:
                    date_diff = " [DIFFERENT DATES]"
            
            print(f"ENTRY {i}: {citation}{date_diff}")
            print(f"Line 1 (ToA): {toa_line}")
            print(f"Line 2 (ToA extracted): Name='{toa_name}', Date='{toa_year}'")
            print(f"Line 3 (Main Body context): {mb_context}")
            print(f"Line 4 (Main Body extracted): Name='{mb_name}', Date='{mb_date}'")
            print("-" * 80)
            
            f.write(f"ENTRY {i}: {citation}{date_diff}\n")
            f.write(f"Line 1 (ToA): {toa_line}\n")
            f.write(f"Line 2 (ToA extracted): Name='{toa_name}', Date='{toa_year}'\n")
            f.write(f"Line 3 (Main Body context): {mb_context}\n")
            f.write(f"Line 4 (Main Body extracted): Name='{mb_name}', Date='{mb_date}'\n")
            f.write("-" * 80 + "\n")
    
    print(f"\nReport saved to: detailed_comparison_report.txt")
    print(f"Total entries compared: {len(common_citations)}")

if __name__ == "__main__":
    main() 