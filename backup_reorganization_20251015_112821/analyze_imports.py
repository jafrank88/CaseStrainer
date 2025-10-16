"""
Analyze imports to identify files that need updating for production cleanup
"""
import os
import re
from collections import defaultdict

# Patterns to search for
OLD_IMPORTS = [
    # Old extraction imports
    r'from\s+src\.unified_case_name_extractor\s+import',
    r'from\s+src\.unified_extraction_architecture\s+import\s+extract_case_name',
    r'from\s+src\.unified_extraction_service\s+import',
    
    # Old verification imports
    r'verify_citations_with_courtlistener_batch',
    
    # Old clustering imports  
    r'from\s+src\.unified_citation_clustering\s+import\s+cluster_citations_unified',
    
    # Deprecated modules
    r'from\s+src\.unified_sync_processor\s+import',
    r'from\s+src\.websearch\.citation_normalizer\s+import',
]

def analyze_file(filepath):
    """Analyze a single file for old imports."""
    issues = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        for pattern in OLD_IMPORTS:
            matches = re.findall(pattern, content)
            if matches:
                issues.append({
                    'pattern': pattern,
                    'count': len(matches)
                })
    except Exception as e:
        pass
    
    return issues

def scan_directory(directory):
    """Scan directory for Python files with old imports."""
    results = defaultdict(list)
    
    for root, dirs, files in os.walk(directory):
        # Skip certain directories
        if any(skip in root for skip in ['__pycache__', '.git', 'node_modules', 'venv', '.ruff_cache']):
            continue
            
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                issues = analyze_file(filepath)
                if issues:
                    results[filepath] = issues
    
    return results

if __name__ == '__main__':
    print("=" * 80)
    print("IMPORT ANALYSIS FOR PRODUCTION CLEANUP")
    print("=" * 80)
    
    # Scan src directory
    src_results = scan_directory('src')
    
    if not src_results:
        print("\n✅ No old imports found in src/ directory!")
    else:
        print(f"\n⚠️  Found {len(src_results)} files with old imports:\n")
        
        for filepath, issues in sorted(src_results.items()):
            rel_path = os.path.relpath(filepath)
            print(f"\n📄 {rel_path}")
            for issue in issues:
                print(f"   - {issue['pattern'][:60]}... ({issue['count']} occurrences)")
    
    # Check for backup files
    print("\n" + "=" * 80)
    print("BACKUP FILES TO DELETE")
    print("=" * 80)
    
    backup_patterns = [
        '*_before_*',
        '*_original_*',
        '*_restore_*',
        '*_regressed_*',
        '*_pre_*',
        '*.backup',
        '*_optimized.py',
        '*_refactored.py'
    ]
    
    backup_files = []
    for root, dirs, files in os.walk('src'):
        if '__pycache__' in root or '.git' in root:
            continue
        for file in files:
            if any(pattern.replace('*', '') in file for pattern in backup_patterns):
                filepath = os.path.join(root, file)
                size = os.path.getsize(filepath) / 1024  # KB
                backup_files.append((filepath, size))
    
    if backup_files:
        total_size = sum(size for _, size in backup_files)
        print(f"\n⚠️  Found {len(backup_files)} backup files ({total_size:.1f} KB total):\n")
        for filepath, size in sorted(backup_files, key=lambda x: x[1], reverse=True):
            rel_path = os.path.relpath(filepath)
            print(f"   ❌ {rel_path} ({size:.1f} KB)")
        
        print(f"\n💾 Total space to reclaim: {total_size:.1f} KB")
    else:
        print("\n✅ No backup files found!")
    
    # Check for deprecated functions
    print("\n" + "=" * 80)
    print("DEPRECATED FUNCTIONS STILL IN USE")
    print("=" * 80)
    
    deprecated_funcs = [
        'extract_case_name_and_date_unified',  # Old version
        'extract_case_name_only_unified',      # Old version
        'extract_citations_unified',           # Multiple versions
        'cluster_citations_unified',           # Old version
    ]
    
    func_usage = defaultdict(list)
    for root, dirs, files in os.walk('src'):
        if '__pycache__' in root or '.git' in root:
            continue
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    for func in deprecated_funcs:
                        if func in content and 'def ' + func not in content:
                            # It's being used, not defined
                            func_usage[func].append(os.path.relpath(filepath))
                except:
                    pass
    
    if func_usage:
        print("\n⚠️  Deprecated functions still in use:\n")
        for func, files in sorted(func_usage.items()):
            print(f"\n📌 {func} ({len(files)} files):")
            for f in files[:5]:  # Show first 5
                print(f"   - {f}")
            if len(files) > 5:
                print(f"   ... and {len(files) - 5} more")
    else:
        print("\n✅ No deprecated functions found in use!")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\n📊 Files with old imports: {len(src_results)}")
    print(f"📊 Backup files to delete: {len(backup_files)}")
    print(f"📊 Deprecated functions in use: {len(func_usage)}")
    
    if src_results or backup_files or func_usage:
        print("\n⚠️  Action required: See PRODUCTION_READINESS_ANALYSIS.md for cleanup plan")
    else:
        print("\n✅ Codebase is clean and ready for production!")
