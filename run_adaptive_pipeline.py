#!/usr/bin/env python3
"""
Run the complete adaptive pipeline for case name/year extraction improvement.
"""

import os
import glob
from pathlib import Path
from src.improved_year_extraction_comparison import process_batch, log_mismatches_to_jsonl
from review_mismatches_report import load_mismatches, write_csv, write_html

def find_brief_files(directory="wa_briefs_text"):
    """Find all .txt files in the briefs directory."""
    pattern = os.path.join(directory, "*.txt")
    files = glob.glob(pattern)
    print(f"Found {len(files)} brief files in {directory}")
    return files

def run_adaptive_pipeline():
    """Run the complete adaptive pipeline."""
    print("=== ADAPTIVE PIPELINE: CASE NAME/YEAR EXTRACTION IMPROVEMENT ===")
    
    # Step 1: Find all brief files
    print("\nStep 1: Finding brief files...")
    brief_files = find_brief_files()
    if not brief_files:
        print("No brief files found. Please check the wa_briefs_text directory.")
        return
    
    # Step 2: Process all briefs in batch
    print(f"\nStep 2: Processing {len(brief_files)} briefs...")
    batch_results = process_batch(brief_files)
    
    # Step 3: Log mismatches to JSONL
    print("\nStep 3: Logging mismatches...")
    mismatches_file = "extraction_mismatches.jsonl"
    log_mismatches_to_jsonl(batch_results, mismatches_file)
    
    # Step 4: Generate review reports
    print("\nStep 4: Generating review reports...")
    mismatches = list(load_mismatches(mismatches_file))
    write_csv(mismatches, "extraction_mismatches.csv")
    write_html(mismatches, "extraction_mismatches.html")
    
    # Step 5: Print summary statistics
    print("\nStep 5: Summary Statistics")
    print("=" * 50)
    
    total_docs = len(batch_results)
    total_mismatches = len(mismatches)
    
    # Count by error type
    year_mismatches = len([m for m in mismatches if m['error_type'] == 'year_mismatch'])
    case_name_mismatches = len([m for m in mismatches if m['error_type'] == 'case_name_mismatch'])
    
    print(f"Total documents processed: {total_docs}")
    print(f"Total mismatches found: {total_mismatches}")
    print(f"  - Year mismatches: {year_mismatches}")
    print(f"  - Case name mismatches: {case_name_mismatches}")
    
    # Show documents with most mismatches
    doc_mismatch_counts = {}
    for mismatch in mismatches:
        doc = mismatch['document']
        doc_mismatch_counts[doc] = doc_mismatch_counts.get(doc, 0) + 1
    
    if doc_mismatch_counts:
        print(f"\nDocuments with most mismatches:")
        sorted_docs = sorted(doc_mismatch_counts.items(), key=lambda x: x[1], reverse=True)
        for doc, count in sorted_docs[:5]:
            doc_name = os.path.basename(doc)
            print(f"  - {doc_name}: {count} mismatches")
    
    # Show sample mismatches
    if mismatches:
        print(f"\nSample mismatches (first 3):")
        for i, mismatch in enumerate(mismatches[:3]):
            print(f"  {i+1}. {mismatch['citation']} - {mismatch['error_type']}")
            print(f"     ToA: {mismatch['toa_case_name']} ({mismatch['toa_year']})")
            print(f"     Body: {mismatch['body_case_name']} ({mismatch['body_year']})")
    
    print(f"\nFiles generated:")
    print(f"  - {mismatches_file} (JSONL format for ML)")
    print(f"  - extraction_mismatches.csv (CSV for review)")
    print(f"  - extraction_mismatches.html (Interactive HTML report)")
    
    print(f"\nNext steps:")
    print(f"  1. Open extraction_mismatches.html in your browser to review mismatches")
    print(f"  2. Optionally label corrections in the CSV file")
    print(f"  3. Use ml_adaptive_pipeline.py to train/improve models")
    
    print("\n=== PIPELINE COMPLETE ===")

if __name__ == "__main__":
    run_adaptive_pipeline() 