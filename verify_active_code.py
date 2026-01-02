#!/usr/bin/env python3
"""
Active Code Verification Tool
==============================

Run this script BEFORE modifying any extraction/clustering code
to verify which file is actually active.

Usage:
    python verify_active_code.py
"""

import os
import re
from pathlib import Path

def check_file_status(filepath: str) -> dict:
    """Analyze a file to determine if it's active or deprecated."""
    result = {
        'file': filepath,
        'exists': False,
        'deprecated': False,
        'is_active': False,
        'imported_by': [],
        'warnings': []
    }
    
    if not os.path.exists(filepath):
        return result
    
    result['exists'] = True
    
    # Check docstring for deprecation
    with open(filepath, 'r', encoding='utf-8') as f:
        first_100_lines = ''.join([f.readline() for _ in range(100)])
        
        deprecation_keywords = ['DEPRECATED', 'DO NOT MODIFY', 'superseded by', 'replaced by']
        for keyword in deprecation_keywords:
            if keyword in first_100_lines:
                result['deprecated'] = True
                result['warnings'].append(f"Found '{keyword}' in docstring")
                break
    
    # Check if file is imported by main processing files
    src_dir = Path(__file__).parent / 'src'
    main_files = [
        'rq_worker.py',
        'unified_processing_pipeline.py',
        'unified_citation_processor_v2.py',
        'unified_clustering_master.py',
        'unified_verification_master.py'
    ]
    
    filename = os.path.basename(filepath).replace('.py', '')
    
    for main_file in main_files:
        main_path = src_dir / main_file
        if main_path.exists():
            with open(main_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Check for direct imports
                if f'from src.{filename} import' in content or f'from .{filename} import' in content:
                    result['imported_by'].append(main_file)
    
    # Determine if active
    result['is_active'] = len(result['imported_by']) > 0 and not result['deprecated']
    
    return result

def main():
    print("=" * 80)
    print("CaseStrainer Active Code Verification Tool")
    print("=" * 80)
    print()
    
    # Files to check
    files_to_check = [
        'src/clean_extraction_pipeline.py',
        'src/unified_case_extraction_master.py',
        'src/unified_extraction_architecture.py',
        'src/unified_case_name_extractor_v2.py',
        'src/unified_clustering_master.py',
        'src/unified_citation_clustering.py',
    ]
    
    results = []
    for filepath in files_to_check:
        result = check_file_status(filepath)
        results.append(result)
    
    # Print results
    print("📊 EXTRACTION CODE STATUS:")
    print("-" * 80)
    extraction_files = [r for r in results if 'extraction' in r['file'] or 'clean_extraction' in r['file']]
    for result in extraction_files:
        filename = os.path.basename(result['file'])
        status = "✅ ACTIVE" if result['is_active'] else "❌ INACTIVE"
        if result['deprecated']:
            status = "⚠️  DEPRECATED"
        
        print(f"\n{status}: {filename}")
        if result['imported_by']:
            print(f"   Imported by: {', '.join(result['imported_by'])}")
        if result['warnings']:
            for warning in result['warnings']:
                print(f"   ⚠️  {warning}")
    
    print("\n" + "=" * 80)
    print("📊 CLUSTERING CODE STATUS:")
    print("-" * 80)
    clustering_files = [r for r in results if 'clustering' in r['file']]
    for result in clustering_files:
        filename = os.path.basename(result['file'])
        status = "✅ ACTIVE" if result['is_active'] else "❌ INACTIVE"
        if result['deprecated']:
            status = "⚠️  DEPRECATED"
        
        print(f"\n{status}: {filename}")
        if result['imported_by']:
            print(f"   Imported by: {', '.join(result['imported_by'])}")
        if result['warnings']:
            for warning in result['warnings']:
                print(f"   ⚠️  {warning}")
    
    print("\n" + "=" * 80)
    print("🎯 RECOMMENDATION:")
    print("=" * 80)
    
    active_extraction = [r for r in extraction_files if r['is_active']]
    active_clustering = [r for r in clustering_files if r['is_active']]
    
    if active_extraction:
        print(f"\n✅ FOR EXTRACTION CHANGES, MODIFY:")
        for result in active_extraction:
            print(f"   → {result['file']}")
    else:
        print("\n⚠️  WARNING: No active extraction file found!")
    
    if active_clustering:
        print(f"\n✅ FOR CLUSTERING CHANGES, MODIFY:")
        for result in active_clustering:
            print(f"   → {result['file']}")
    else:
        print("\n⚠️  WARNING: No active clustering file found!")
    
    print("\n" + "=" * 80)
    print("💡 TIPS:")
    print("=" * 80)
    print("""
1. Before modifying any file, run this script to verify it's active
2. If a file is deprecated, check its docstring for the replacement
3. After making changes, verify with:
   logger.error("[TEST] Your diagnostic message")
4. See ACTIVE_CODE_MAP.md for detailed architecture
""")
    print("=" * 80)

if __name__ == '__main__':
    main()
