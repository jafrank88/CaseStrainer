"""
Verify that the main pipeline does not call deprecated functions.
Checks main entry points and processing paths.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

def check_file_for_deprecated(filepath: Path) -> List[Dict]:
    """Check a file for deprecated function calls or imports."""
    issues = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Patterns to check for deprecated items
        deprecated_patterns = {
            'EnhancedSyncProcessor import': r'from.*enhanced_sync_processor import|import.*enhanced_sync_processor',
            'EnhancedSyncProcessor usage': r'EnhancedSyncProcessor\(',
            'ProcessingOptions usage': r'ProcessingOptions\(',
            'deprecated decorator': r'@deprecated',
            'warnings.warn deprecated': r'warnings\.warn.*deprecated',
            'UnifiedSyncProcessor import': r'from.*unified_sync_processor import|import.*unified_sync_processor',
            'UnifiedSyncProcessor usage': r'UnifiedSyncProcessor\(',
        }
        
        for line_num, line in enumerate(lines, 1):
            for pattern_name, pattern in deprecated_patterns.items():
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append({
                        'file': str(filepath),
                        'line': line_num,
                        'type': pattern_name,
                        'content': line.strip()
                    })
        
    except Exception as e:
        print(f"Error checking {filepath}: {e}")
    
    return issues

def check_main_pipeline_files():
    """Check the main pipeline files for deprecated calls."""
    
    print("=" * 80)
    print("CHECKING MAIN PIPELINE FOR DEPRECATED FUNCTION CALLS")
    print("=" * 80)
    
    # Main pipeline files to check
    main_files = [
        # Entry points
        'src/app_final_vue.py',
        
        # Main API endpoints
        'src/vue_api_endpoints.py',
        
        # Main processing pipeline
        'src/unified_input_processor.py',
        'src/unified_citation_processor_v2.py',
        
        # Services
        'src/api/services/citation_service.py',
        
        # Workers
        'src/rq_worker.py',
        'src/async_verification_worker.py',
        
        # Progress tracking
        'src/progress_manager.py',
        'src/progress_tracker.py',
        
        # Verification
        'src/enhanced_fallback_verifier.py',
        'src/verification_manager.py',
        
        # Clustering
        'src/unified_citation_clustering.py',
        'src/unified_clustering_master.py',
    ]
    
    all_issues = []
    checked_files = []
    missing_files = []
    
    for filepath in main_files:
        path = Path(filepath)
        if path.exists():
            checked_files.append(str(path))
            issues = check_file_for_deprecated(path)
            if issues:
                all_issues.extend(issues)
        else:
            missing_files.append(filepath)
    
    # Print results
    print(f"\n{'='*80}")
    print("RESULTS")
    print('='*80)
    
    print(f"\nFiles checked: {len(checked_files)}")
    print(f"Files missing: {len(missing_files)}")
    print(f"Issues found: {len(all_issues)}")
    
    if missing_files:
        print(f"\n⚠️  Missing files (not checked):")
        for f in missing_files:
            print(f"  - {f}")
    
    if all_issues:
        print(f"\n❌ DEPRECATED CALLS FOUND:")
        
        # Group by file
        by_file = {}
        for issue in all_issues:
            filepath = issue['file']
            if filepath not in by_file:
                by_file[filepath] = []
            by_file[filepath].append(issue)
        
        for filepath, issues in by_file.items():
            print(f"\n  📄 {Path(filepath).name} ({len(issues)} issues)")
            for issue in issues[:5]:  # Show first 5
                print(f"    Line {issue['line']}: [{issue['type']}]")
                print(f"      {issue['content'][:80]}...")
            if len(issues) > 5:
                print(f"    ... and {len(issues) - 5} more issues")
    else:
        print(f"\n✅ NO DEPRECATED CALLS FOUND IN MAIN PIPELINE")
        print("   All main pipeline files are clean!")
    
    # Check for specific safe patterns
    print(f"\n{'='*80}")
    print("VERIFICATION: CORRECT PROCESSOR USAGE")
    print('='*80)
    
    unified_processor_files = []
    for filepath in checked_files:
        path = Path(filepath)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'UnifiedCitationProcessorV2' in content:
                    unified_processor_files.append(path.name)
        except:
            pass
    
    if unified_processor_files:
        print(f"\n✅ Files correctly using UnifiedCitationProcessorV2:")
        for f in unified_processor_files:
            print(f"  - {f}")
    
    return len(all_issues) == 0

def check_imports_in_main_app():
    """Check what the main app imports."""
    print(f"\n{'='*80}")
    print("MAIN APP IMPORTS ANALYSIS")
    print('='*80)
    
    app_file = Path('src/app_final_vue.py')
    if not app_file.exists():
        print("❌ Main app file not found")
        return
    
    with open(app_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    imports = []
    for line_num, line in enumerate(lines[:100], 1):  # Check first 100 lines
        if 'import' in line and not line.strip().startswith('#'):
            imports.append((line_num, line.strip()))
    
    print(f"\nFirst 20 imports in main app:")
    for line_num, imp in imports[:20]:
        status = "✅" if "deprecated" not in imp.lower() and "enhanced_sync" not in imp.lower() else "⚠️"
        print(f"  {status} Line {line_num:3d}: {imp[:70]}")
    
    if len(imports) > 20:
        print(f"  ... and {len(imports) - 20} more imports")

if __name__ == '__main__':
    success = check_main_pipeline_files()
    check_imports_in_main_app()
    
    print(f"\n{'='*80}")
    if success:
        print("✅ VERIFICATION PASSED: Main pipeline is clean")
        print("   No deprecated function calls detected")
    else:
        print("❌ VERIFICATION FAILED: Deprecated calls found")
        print("   Review issues above and update code")
    print('='*80)
