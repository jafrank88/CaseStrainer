#!/usr/bin/env python3
"""
Update all uses of old citation extraction methods to use the new unified processor.

This script will:
1. Replace extract_citations_from_text from citation_utils with the new unified processor
2. Replace extract_all_citations from citation_utils with the new unified processor
3. Update imports and function calls accordingly
"""
import os
import re
import sys
from pathlib import Path

def update_file(file_path, old_import, new_import, old_function, new_function):
    """Update a single file to use the new citation extraction method."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Update imports
        if old_import in content:
            content = content.replace(old_import, new_import)
            print(f"  Updated import in {file_path}")
        
        # Update function calls
        if old_function in content:
            # Replace function calls with the new unified processor
            if old_function == "extract_citations_from_text":
                # Replace the old function call with new unified processor
                content = re.sub(
                    r'extract_citations_from_text\s*\(\s*([^)]+)\s*\)',
                    r'get_unified_citations(\1)',
                    content
                )
                # Add the helper function at the top of the file
                helper_function = '''
def get_unified_citations(text, logger=None):
    """Get citations using the new unified processor with eyecite."""
    from unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig
    
    config = ProcessingConfig(
        use_eyecite=True,
        use_regex=True,
        extract_case_names=True,
        extract_dates=True,
        enable_clustering=True,
        enable_deduplication=True,
        debug_mode=False
    )
    
    processor = UnifiedCitationProcessorV2(config)
    results = processor.process_text(text)
    
    # Return just the citation strings for compatibility
    return [result.citation for result in results]

'''
                # Add helper function after imports
                import_pattern = r'^((?:import|from).*?)(?=\n(?!import|from))'
                match = re.search(import_pattern, content, re.MULTILINE | re.DOTALL)
                if match:
                    content = content.replace(match.group(1), match.group(1) + helper_function)
                else:
                    # If no imports found, add at the beginning
                    content = helper_function + content
                
                print(f"  Updated function calls in {file_path}")
            
            elif old_function == "extract_all_citations":
                # Replace with the new unified processor
                content = re.sub(
                    r'extract_all_citations\s*\(\s*([^)]+)\s*\)',
                    r'get_unified_citations(\1)',
                    content
                )
                # Add the helper function at the top of the file
                helper_function = '''
def get_unified_citations(text, logger=None):
    """Get citations using the new unified processor with eyecite."""
    from unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig
    
    config = ProcessingConfig(
        use_eyecite=True,
        use_regex=True,
        extract_case_names=True,
        extract_dates=True,
        enable_clustering=True,
        enable_deduplication=True,
        debug_mode=False
    )
    
    processor = UnifiedCitationProcessorV2(config)
    results = processor.process_text(text)
    
    # Return just the citation strings for compatibility
    return [result.citation for result in results]

'''
                # Add helper function after imports
                import_pattern = r'^((?:import|from).*?)(?=\n(?!import|from))'
                match = re.search(import_pattern, content, re.MULTILINE | re.DOTALL)
                if match:
                    content = content.replace(match.group(1), match.group(1) + helper_function)
                else:
                    # If no imports found, add at the beginning
                    content = helper_function + content
                
                print(f"  Updated function calls in {file_path}")
        
        # Only write if content changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        return False
        
    except Exception as e:
        print(f"  Error updating {file_path}: {e}")
        return False

def main():
    """Main function to update all citation extraction methods."""
    
    # Files that need updating
    files_to_update = [
        # Test files
        "test_brief_with_toa.py",
        "compare_body_vs_toa.py", 
        "debug_citation_extraction.py",
        "test_extraction_methods.py",
        
        # Script files
        "scripts/test_year_extraction.py",
        "scripts/sample_citation_extractor.py",
        "scripts/process_downloaded_wa_briefs.py",
        "scripts/process_c_drive_wa_briefs.py",
        
        # Source files that might need updating
        "src/citation_utils.py",  # Update the deprecated functions
    ]
    
    # Import patterns to replace
    old_imports = [
        "from citation_utils import extract_citations_from_text",
        "from citation_utils import extract_all_citations",
        "from .citation_utils import extract_citations_from_text",
        "from .citation_utils import extract_all_citations",
    ]
    
    new_imports = [
        "# Updated to use unified processor",
        "# Updated to use unified processor", 
        "# Updated to use unified processor",
        "# Updated to use unified processor",
    ]
    
    # Function names to replace
    old_functions = [
        "extract_citations_from_text",
        "extract_all_citations"
    ]
    
    new_functions = [
        "get_unified_citations",
        "get_unified_citations"
    ]
    
    print("Updating citation extraction methods...")
    
    updated_count = 0
    
    for file_path in files_to_update:
        if os.path.exists(file_path):
            print(f"\nProcessing {file_path}...")
            
            # Update imports
            for old_import, new_import in zip(old_imports, new_imports):
                if update_file(file_path, old_import, new_import, "", ""):
                    updated_count += 1
            
            # Update function calls
            for old_function, new_function in zip(old_functions, new_functions):
                if update_file(file_path, "", "", old_function, new_function):
                    updated_count += 1
        else:
            print(f"  File not found: {file_path}")
    
    print(f"\nUpdate complete! Updated {updated_count} files.")
    print("\nNote: The old functions in citation_utils.py are now deprecated.")
    print("All new code should use the unified processor with eyecite for better results.")

if __name__ == "__main__":
    main() 