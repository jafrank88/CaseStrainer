#!/usr/bin/env python3
"""
Script to update all test files to use UnifiedCitationProcessorV2 instead of the old processors.
"""

import os
import re
import glob

def update_file(filepath):
    """Update a single file to use the new V2 processor."""
    print(f"Updating {filepath}...")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
            with open(filepath, 'r', encoding='latin-1') as f:
                content = f.read()
        except Exception as e:
            print(f"  ✗ Error reading {filepath}: {e}")
            return False
    
    # Track if we made any changes
    original_content = content
    
    # Update imports from old unified processor
    content = re.sub(
        r'from src\.unified_citation_processor import UnifiedCitationProcessor',
        'from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2 as UnifiedCitationProcessor',
        content
    )
    
    # Update imports from old unified processor with additional imports
    content = re.sub(
        r'from src\.unified_citation_processor import UnifiedCitationProcessor, (.*)',
        r'from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2 as UnifiedCitationProcessor',
        content
    )
    
    # Update imports from old citation extractor
    content = re.sub(
        r'from src\.citation_extractor import CitationExtractor',
        '# DEPRECATED: # DEPRECATED: from src.citation_extractor import CitationExtractor',
        content
    )
    
    # Update imports from old enhanced citation extractor
    content = re.sub(
        r'from src\.enhanced_citation_extractor import EnhancedCitationExtractor',
        '# DEPRECATED: # DEPRECATED: from src.enhanced_citation_extractor import EnhancedCitationExtractor',
        content
    )
    
    # Update imports from old complex citation integration
    content = re.sub(
        r'from src\.complex_citation_integration import ComplexCitationIntegrator',
        '# DEPRECATED: # DEPRECATED: from src.complex_citation_integration import ComplexCitationIntegrator',
        content
    )
    
    # Update imports from old unified citation extractor
    content = re.sub(
        r'from src\.unified_citation_extractor import UnifiedCitationExtractor',
        '# DEPRECATED: # DEPRECATED: from src.unified_citation_extractor import UnifiedCitationExtractor',
        content
    )
    
    # Update imports from old brief citation analyzer
    content = re.sub(
        r'from src\.brief_citation_analyzer import BriefCitationAnalyzer',
        '# DEPRECATED: # DEPRECATED: from src.brief_citation_analyzer import BriefCitationAnalyzer',
        content
    )
    
    # Update direct imports from unified_citation_processor
    content = re.sub(
        r'from unified_citation_processor_v2 import UnifiedCitationProcessorV2 as UnifiedCitationProcessor',
        'from unified_citation_processor_v2 import UnifiedCitationProcessorV2 as UnifiedCitationProcessor',
        content
    )
    
    # Update CitationResult imports
    content = re.sub(
        r'from src\.unified_citation_processor import CitationResult',
        'from src.unified_citation_processor_v2 import CitationResult',
        content
    )
    
    # Update TextCleaner imports
    content = re.sub(
        r'from src\.unified_citation_processor import TextCleaner',
        '# DEPRECATED: TextCleaner functionality moved to UnifiedCitationProcessorV2',
        content
    )
    
    # Update get_canonical_case_name_with_date imports
    content = re.sub(
        r'from src\.unified_citation_processor import get_canonical_case_name_with_date',
        '# DEPRECATED: get_canonical_case_name_with_date functionality moved to UnifiedCitationProcessorV2',
        content
    )
    
    # Only write if content changed
    if content != original_content:
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✓ Updated {filepath}")
            return True
        except Exception as e:
            print(f"  ✗ Error writing {filepath}: {e}")
            return False
    else:
        print(f"  - No changes needed for {filepath}")
        return False

def main():
    """Update all test files."""
    print("Updating test files to use UnifiedCitationProcessorV2...")
    print("=" * 60)
    
    # Find all test files
    test_files = []
    test_files.extend(glob.glob("test_*.py"))
    test_files.extend(glob.glob("src/test_*.py"))
    test_files.extend(glob.glob("tests/test_*.py"))
    
    updated_count = 0
    total_count = len(test_files)
    
    for filepath in test_files:
        if os.path.isfile(filepath):
            if update_file(filepath):
                updated_count += 1
    
    print("=" * 60)
    print(f"Update complete! Updated {updated_count}/{total_count} files.")
    
    # Also update any scripts that might use the old processors
    print("\nChecking for other files that might need updates...")
    
    other_files = []
    other_files.extend(glob.glob("*.py"))
    other_files.extend(glob.glob("src/*.py"))
    
    for filepath in other_files:
        if filepath.startswith("test_"):
            continue  # Already processed
        if os.path.isfile(filepath):
            if update_file(filepath):
                updated_count += 1
    
    print(f"Total files updated: {updated_count}")

if __name__ == "__main__":
    main() 