"""
Comprehensive codebase review for refactoring and deprecation opportunities.
"""

import os
import re
from pathlib import Path
from collections import defaultdict
import ast

def find_python_files(directory, exclude_dirs=None):
    """Find all Python files in directory."""
    if exclude_dirs is None:
        exclude_dirs = {'__pycache__', '.git', 'node_modules', 'venv', 'env'}
    
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Remove excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(Path(root) / file)
    
    return python_files

def analyze_imports(filepath):
    """Analyze imports in a Python file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
        
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        
        return imports
    except:
        return []

def find_deprecated_patterns(filepath):
    """Find deprecated patterns in code."""
    deprecated = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
    
    patterns = {
        'warnings.warn': r'warnings\.warn.*deprecated',
        'TODO/FIXME': r'#\s*(TODO|FIXME|XXX|HACK)',
        'old_processor': r'EnhancedSyncProcessor',
        'legacy_import': r'from.*legacy|import.*legacy',
        'archived': r'from.*archived|import.*archived',
    }
    
    for line_num, line in enumerate(lines, 1):
        for pattern_name, pattern in patterns.items():
            if re.search(pattern, line, re.IGNORECASE):
                deprecated.append({
                    'line': line_num,
                    'type': pattern_name,
                    'content': line.strip()
                })
    
    return deprecated

def analyze_function_complexity(filepath):
    """Analyze function complexity (line count, nesting)."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
        
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Count lines
                if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
                    lines = node.end_lineno - node.lineno
                    if lines > 100:  # Flag functions over 100 lines
                        functions.append({
                            'name': node.name,
                            'lines': lines,
                            'start': node.lineno
                        })
        
        return functions
    except:
        return []

def find_duplicate_code(files):
    """Find potential duplicate code patterns."""
    # Look for similar function names across files
    function_names = defaultdict(list)
    
    for filepath in files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    function_names[node.name].append(str(filepath))
        except:
            continue
    
    # Find functions with same name in multiple files
    duplicates = {name: files for name, files in function_names.items() if len(files) > 1}
    
    return duplicates

def main():
    print("=" * 80)
    print("COMPREHENSIVE CODEBASE REVIEW")
    print("=" * 80)
    
    src_dir = Path('src')
    if not src_dir.exists():
        print("Error: src/ directory not found")
        return
    
    python_files = find_python_files(src_dir)
    print(f"\nAnalyzing {len(python_files)} Python files...")
    
    # 1. ARCHIVED/DEPRECATED CODE
    print("\n" + "=" * 80)
    print("1. ARCHIVED & DEPRECATED CODE")
    print("=" * 80)
    
    archived_files = [f for f in python_files if 'archived' in str(f).lower()]
    print(f"\nFiles in archived directories: {len(archived_files)}")
    
    deprecated_usage = {}
    for filepath in python_files:
        if 'archived' not in str(filepath).lower():
            deprecated = find_deprecated_patterns(filepath)
            if deprecated:
                deprecated_usage[filepath] = deprecated
    
    if deprecated_usage:
        print(f"\nFiles with deprecated patterns: {len(deprecated_usage)}")
        for filepath, items in list(deprecated_usage.items())[:5]:
            try:
                rel_path = filepath.relative_to(Path.cwd())
            except ValueError:
                rel_path = filepath
            print(f"\n  {rel_path}:")
            for item in items[:3]:
                print(f"    Line {item['line']}: [{item['type']}] {item['content'][:60]}...")
    
    # 2. DUPLICATE FUNCTIONALITY
    print("\n" + "=" * 80)
    print("2. DUPLICATE FUNCTIONALITY")
    print("=" * 80)
    
    duplicates = find_duplicate_code(python_files)
    
    print(f"\nFunctions with same name in multiple files: {len(duplicates)}")
    
    # Focus on key duplicates
    key_duplicates = {
        name: files for name, files in duplicates.items() 
        if len(files) > 2 or any('processor' in name.lower() for f in files)
    }
    
    if key_duplicates:
        print("\nKey duplicate functions to review:")
        for name, files in list(key_duplicates.items())[:10]:
            print(f"\n  '{name}' found in {len(files)} files:")
            for f in files[:3]:
                try:
                    rel = Path(f).relative_to(Path.cwd())
                except ValueError:
                    rel = Path(f)
                print(f"    - {rel}")
    
    # 3. COMPLEX FUNCTIONS
    print("\n" + "=" * 80)
    print("3. LARGE/COMPLEX FUNCTIONS (>100 lines)")
    print("=" * 80)
    
    complex_functions = []
    for filepath in python_files:
        if 'archived' not in str(filepath).lower():
            functions = analyze_function_complexity(filepath)
            for func in functions:
                complex_functions.append((filepath, func))
    
    complex_functions.sort(key=lambda x: x[1]['lines'], reverse=True)
    
    print(f"\nFound {len(complex_functions)} large functions")
    if complex_functions:
        print("\nTop 10 largest functions:")
        for filepath, func in complex_functions[:10]:
            print(f"  {func['lines']:4d} lines: {func['name']:40s} in {filepath.name}")
    
    # 4. OLD PROCESSOR USAGE
    print("\n" + "=" * 80)
    print("4. OLD PROCESSOR USAGE")
    print("=" * 80)
    
    old_processors = [
        'EnhancedSyncProcessor',
        'UnifiedSyncProcessor',
        'enhanced_sync_processor',
        'unified_sync_processor_refactored',
    ]
    
    processor_usage = defaultdict(list)
    for filepath in python_files:
        if 'archived' not in str(filepath).lower():
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                for processor in old_processors:
                    if processor in content:
                        processor_usage[processor].append(filepath)
    
    if processor_usage:
        print("\nOld processor references found:")
        for processor, files in processor_usage.items():
            print(f"\n  {processor}: {len(files)} file(s)")
            for f in files[:3]:
                try:
                    rel = f.relative_to(Path.cwd())
                except ValueError:
                    rel = f
                print(f"    - {rel}")
    else:
        print("\n✓ No old processor references found")
    
    # 5. IMPORT ANALYSIS
    print("\n" + "=" * 80)
    print("5. IMPORT ANALYSIS")
    print("=" * 80)
    
    all_imports = defaultdict(int)
    for filepath in python_files:
        if 'archived' not in str(filepath).lower():
            imports = analyze_imports(filepath)
            for imp in imports:
                all_imports[imp] += 1
    
    # Find rarely used imports (potential unused)
    rare_imports = {imp: count for imp, count in all_imports.items() if count == 1}
    print(f"\nTotal unique imports: {len(all_imports)}")
    print(f"Imports used only once: {len(rare_imports)} (may be unused)")
    
    # 6. FILE SIZE ANALYSIS
    print("\n" + "=" * 80)
    print("6. FILE SIZE ANALYSIS")
    print("=" * 80)
    
    file_sizes = []
    for filepath in python_files:
        if 'archived' not in str(filepath).lower():
            size = filepath.stat().st_size
            lines = len(open(filepath, 'r', encoding='utf-8').readlines())
            file_sizes.append((filepath, size, lines))
    
    file_sizes.sort(key=lambda x: x[2], reverse=True)
    
    print("\nTop 10 largest files (by lines):")
    for filepath, size, lines in file_sizes[:10]:
        print(f"  {lines:5d} lines ({size//1024:4d} KB): {filepath.name}")
    
    # RECOMMENDATIONS
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    
    print("""
1. DEPRECATION CANDIDATES:
   - Archive directory contains {archived_count} files - consider permanent removal
   - Old processor references should be migrated to UnifiedCitationProcessorV2
   - Functions with deprecation warnings should be removed in next major version

2. REFACTORING PRIORITIES:
   - {complex_count} functions over 100 lines - consider breaking down
   - Duplicate function names suggest opportunity for consolidation
   - Large files (>1000 lines) could be split into modules

3. CODE CLEANUP:
   - {todo_count} TODO/FIXME comments need attention
   - {rare_import_count} rarely-used imports may be removable
   - Review {deprecated_files} files with deprecated patterns

4. ARCHITECTURAL IMPROVEMENTS:
   - Consolidate duplicate functionality
   - Standardize on UnifiedCitationProcessorV2 as single processor
   - Consider extracting common utilities into shared module
    """.format(
        archived_count=len(archived_files),
        complex_count=len(complex_functions),
        todo_count=sum(1 for f in deprecated_usage.values() for i in f if i['type'] == 'TODO/FIXME'),
        rare_import_count=len(rare_imports),
        deprecated_files=len(deprecated_usage)
    ))
    
    print("=" * 80)
    print("\nDetailed report saved to: CODEBASE_REVIEW_REPORT.md")
    
    # Generate detailed report
    with open('CODEBASE_REVIEW_REPORT.md', 'w', encoding='utf-8') as f:
        f.write("# Codebase Review Report\n\n")
        f.write(f"Generated: {Path.cwd()}\n\n")
        
        f.write("## Summary\n\n")
        f.write(f"- Total Python files analyzed: {len(python_files)}\n")
        f.write(f"- Archived files: {len(archived_files)}\n")
        f.write(f"- Files with deprecated patterns: {len(deprecated_usage)}\n")
        f.write(f"- Large functions (>100 lines): {len(complex_functions)}\n")
        f.write(f"- Duplicate function names: {len(duplicates)}\n\n")
        
        f.write("## Detailed Findings\n\n")
        
        f.write("### Large Functions\n\n")
        for filepath, func in complex_functions[:20]:
            f.write(f"- **{func['name']}** ({func['lines']} lines) in `{filepath.name}`\n")
        
        f.write("\n### Duplicate Functions\n\n")
        for name, files in list(key_duplicates.items())[:20]:
            f.write(f"- **{name}** in {len(files)} files\n")
        
        f.write("\n### Deprecated Patterns\n\n")
        for filepath, items in list(deprecated_usage.items())[:20]:
            try:
                rel = filepath.relative_to(Path.cwd())
            except ValueError:
                rel = filepath
            f.write(f"- `{rel}`: {len(items)} issues\n")

if __name__ == '__main__':
    main()
