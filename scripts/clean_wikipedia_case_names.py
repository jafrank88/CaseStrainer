#!/usr/bin/env python3
"""
Script to clean and filter the Wikipedia case names CSV to extract only actual case names.
"""

import csv
import re
import os
from datetime import datetime
from typing import List, Dict

def is_actual_case_name(case_name: str) -> bool:
    """Check if a case name is actually a legal case name."""
    if not case_name or len(case_name) < 5:
        return False
    
    # Remove common non-case name patterns
    non_case_patterns = [
        r'^United States Reports$',
        r'^U\.S\. Reports$',
        r'^Lawyers\' Edition$',
        r'^About Wikipedia$',
        r'^Get shortened URL$',
        r'^Download QR code$',
        r'^Download as PDF$',
        r'^United States Supreme Court$',
        r'^Reporters of Decisions',
        r'^Chief Justice$',
        r'^Supreme Court Building$',
        r'^Code of Conduct',
        r'^Terms of Use$',
        r'^Privacy Policy$',
        r'^Contact Wikipedia$',
        r'^Creative Commons',
        r'^Wikimedia Foundation',
        r'^Same Cause$',
        r'^Dallas Reports$',
        r'^Reports of cases',
        r'^The Ship Resolution$',
        r'^The Brig ',
        r'^The Sloop ',
        r'^Number of U\.S\.',
        r'^Information About',
        r'^Opinions of the Court',
        r'^Justices who served',
        r'^Judiciary Act of',
        r'^Seventh Circuit Act',
        r'^Eighth and Ninth Circuits',
        r'^Tenth Circuit Act',
        r'^Judicial Circuits Act',
        r'^Supreme Court Police',
        r'^Reporter of Decisions',
        r'^Royal Exchange',
        r'^Old City Hall',
        r'^Old Supreme Court Chamber',
        r'^Old Senate Chamber',
        r'^Article III',
        r'^Judicial Procedures Reform',
        r'^Impeachment of',
        r'^Impeachment trial of',
        r'^Presidential Commission',
        r'^Supreme Court in fiction',
        r'^Supreme Court leaks',
        r'^United States Solicitor General',
        r'^United States portal',
        r'^Lists of United States',
        r'^Short description',
        r'^Creative Commons',
        r'^Terms of Use',
        r'^Privacy Policy',
        r'^Wikimedia Foundation',
        r'^Contact Wikipedia',
        r'^Code of Conduct',
        r'^Dallas Reports$',
        r'^Reports of cases ruled',
    ]
    
    for pattern in non_case_patterns:
        if re.match(pattern, case_name, re.IGNORECASE):
            return False
    
    # Must contain case name indicators
    case_indicators = [
        r'\bv\.\s+',  # v. pattern
        r'\bvs\.\s+',  # vs. pattern
        r'\bversus\s+',  # versus pattern
        r'\bIn\s+re\s+',  # In re pattern
        r'\bEx\s+parte\s+',  # Ex parte pattern
        r'\bEstate\s+of\s+',  # Estate pattern
        r'\bState\s+v\.\s+',  # State v. pattern
        r'\bPeople\s+v\.\s+',  # People v. pattern
        r'\bUnited\s+States\s+v\.\s+',  # United States v. pattern
        r'\bRespublica\s+v\.\s+',  # Respublica v. pattern
        r'\bCommonwealth\s+v\.\s+',  # Commonwealth v. pattern
    ]
    
    has_case_indicator = any(re.search(pattern, case_name, re.IGNORECASE) for pattern in case_indicators)
    
    # Must have proper capitalization (at least two capitalized words)
    words = case_name.split()
    if len(words) < 2:
        return False
    
    capitalized_words = sum(1 for word in words if word and word[0].isupper())
    
    # Must be reasonable length
    if len(case_name) < 8 or len(case_name) > 200:
        return False
    
    return has_case_indicator and capitalized_words >= 2

def clean_case_name(case_name: str) -> str:
    """Clean and normalize a case name."""
    if not case_name:
        return ""
    
    # Remove extra whitespace
    case_name = re.sub(r'\s+', ' ', case_name).strip()
    
    # Remove trailing punctuation
    case_name = re.sub(r'[,\s]+$', '', case_name)
    case_name = case_name.rstrip('.,;:')
    
    # Normalize spacing around "v."
    case_name = re.sub(r'\s+v\.\s+', ' v. ', case_name)
    case_name = re.sub(r'\s+vs\.\s+', ' v. ', case_name)
    case_name = re.sub(r'\s+versus\s+', ' v. ', case_name)
    
    # Normalize spacing around "In re"
    case_name = re.sub(r'\s+In\s+re\s+', ' In re ', case_name)
    
    # Normalize spacing around "Ex parte"
    case_name = re.sub(r'\s+Ex\s+parte\s+', ' Ex parte ', case_name)
    
    return case_name

def process_csv(input_file: str, output_file: str = None) -> str:
    """Process the Wikipedia case names CSV and create a cleaned version."""
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"data/cleaned_wikipedia_case_names_{timestamp}.csv"
    
    # Ensure the data directory exists
    os.makedirs('data', exist_ok=True)
    
    cleaned_cases = []
    total_cases = 0
    
    print(f"Processing {input_file}...")
    
    with open(input_file, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row in reader:
            total_cases += 1
            case_name = row['case_name'].strip()
            
            # Clean the case name
            cleaned_name = clean_case_name(case_name)
            
            # Check if it's an actual case name
            if is_actual_case_name(cleaned_name):
                cleaned_row = {
                    'case_name': cleaned_name,
                    'source_url': row['source_url'],
                    'extraction_method': row['extraction_method'],
                    'confidence': row['confidence'],
                    'extracted_date': row['extracted_date'],
                    'cleaned_date': datetime.now().isoformat()
                }
                cleaned_cases.append(cleaned_row)
    
    # Save cleaned cases to CSV
    fieldnames = ['case_name', 'source_url', 'extraction_method', 'confidence', 'extracted_date', 'cleaned_date']
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for case in cleaned_cases:
            writer.writerow(case)
    
    print(f"Processed {total_cases} total cases")
    print(f"Found {len(cleaned_cases)} actual case names")
    print(f"Saved cleaned cases to: {output_file}")
    
    return output_file

def main():
    """Main function to clean the Wikipedia case names."""
    # Find the most recent Wikipedia case names CSV
    data_dir = 'data'
    if not os.path.exists(data_dir):
        print("No data directory found. Please run the Wikipedia extraction script first.")
        return
    
    csv_files = [f for f in os.listdir(data_dir) if f.startswith('wikipedia_case_names_') and f.endswith('.csv')]
    
    if not csv_files:
        print("No Wikipedia case names CSV files found. Please run the extraction script first.")
        return
    
    # Use the most recent file
    latest_file = max(csv_files, key=lambda x: os.path.getctime(os.path.join(data_dir, x)))
    input_file = os.path.join(data_dir, latest_file)
    
    print(f"Using input file: {input_file}")
    
    # Process the CSV
    output_file = process_csv(input_file)
    
    # Show some examples of cleaned case names
    print("\nExamples of cleaned case names:")
    with open(output_file, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for i, row in enumerate(reader):
            if i < 10:  # Show first 10 examples
                print(f"  {row['case_name']}")
            else:
                break
    
    print(f"\nCleaning complete! Results saved to: {output_file}")

if __name__ == "__main__":
    main() 