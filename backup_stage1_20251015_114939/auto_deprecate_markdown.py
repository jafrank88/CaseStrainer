#!/usr/bin/env python3
"""
Automated Deprecation of Outdated Markdown Files
"""

import os
import shutil
import datetime
from pathlib import Path

def create_deprecation_notice(original_content, reason="Outdated documentation"):
    """Create a deprecation notice for markdown files."""
    
    deprecation_header = f"""# ⚠️ DEPRECATED - {os.path.basename(__file__)}

> **This file has been deprecated and moved to the archived documentation.**

## Deprecation Information
- **Date Deprecated**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Reason**: {reason}
- **Replacement**: See `CONSOLIDATED_DOCUMENTATION.md` for current documentation

## Original Content
The original content has been preserved below for reference:

---

"""
    
    return deprecation_header + original_content

def should_deprecate_file(filename, file_size, last_modified):
    """Determine if a file should be deprecated based on various criteria."""
    
    # Files that are definitely outdated
    definitely_outdated = [
        "DEPRECATED.md",
        "DEPRECATION_NOTICE.md", 
        "DEPRECATION_COMPLETE.md",
        "DEPRECATED_MODULES.md",
        "FINAL_CLEANUP_SUMMARY.md",
        "CLEANUP_SUMMARY.md",
        "VERIFICATION_FIX_SUMMARY.md",
        "ENHANCEMENTS_SUMMARY.md",
        "ENHANCED_CASE_EXTRACTION_SUMMARY.md",
        "ENHANCED_INTEGRATION_SUMMARY.md",
        "VERIFIER_CONSOLIDATION_SUMMARY.md",
        "INTEGRATION_SUMMARY.md",
        "CITATION_MERGE_PLAN.md",
        "CITATION_VERIFICATION_OPTIMIZATION_PROPOSAL.md",
        "CASE_NAME_IMPROVEMENTS.md",
        "COMPLEX_CITATION_IMPROVEMENTS.md",
        "PARSER_CONSOLIDATION_SUMMARY.md",
        "OPTION_6_DIAGNOSTICS_FIXES.md",
        "WIKIPEDIA_CASE_NAMES_SUMMARY.md",
        "ENHANCED_PERFORMANCE_OPTIMIZATIONS.md",
        "FINAL_ENHANCEMENT_SUMMARY.md",
        "COMPREHENSIVE_ENGINE_COMPARISON.md",
        "SECURITY_FIXES_SUMMARY.md",
        "SECURITY_STATUS_SUMMARY.md",
        "PRODUCTION_TEST_SUITE_RECOMMENDATIONS.md",
        "pylance_fixes_summary.md"
    ]
    
    # Files that are temporary or test results
    temporary_files = [
        "results.md",
        "extracted_text.md",
        "test_results.md",
        "citation_debug_summary.md",
        "production_files_analysis.md",
        "step4_update_checklist.md"
    ]
    
    # Files that are superseded by consolidated documentation
    superseded_files = [
        "DEPLOYMENT.md",
        "DEPLOYMENT_GUIDE.md",
        "PERFORMANCE_OPTIMIZATIONS.md",
        "AUTO-RESTART-README.md",
        "AUTO_RESTART_GUIDE.md",
        "MONITORING_README.md",
        "DEVELOPER_GUIDE.md",
        "PRODUCTION_CHECKLIST.md",
        "PRODUCTION_READINESS_CHECKLIST.md",
        "MIGRATION_GUIDE.md",
        "MIGRATION_PLAN.md",
        "CHANGELOG.md",
        "DOCKER_PRODUCTION_FIXES.md",
        "DOCKER_DISABLED.md",
        "NGINX_SSL_SETUP.md",
        "BATCH_FILES.md",
        "backend_flowchart.md"
    ]
    
    # Check if file is in any of the deprecation lists
    if filename in definitely_outdated:
        return True, "Definitely outdated - superseded by newer implementations"
    elif filename in temporary_files:
        return True, "Temporary file - test results or debug output"
    elif filename in superseded_files:
        return True, "Superseded by CONSOLIDATED_DOCUMENTATION.md"
    
    # Check file size (very large files might be test results)
    if file_size > 50000:  # 50KB
        return True, "Large file - likely test results or debug output"
    
    # Check if file is very old (more than 30 days)
    days_old = (datetime.datetime.now() - last_modified).days
    if days_old > 30:
        return True, f"Old file ({days_old} days) - likely outdated"
    
    return False, "Keep file"

def auto_deprecate_markdown_files():
    """Automatically deprecate outdated markdown files."""
    
    # Create archived directory if it doesn't exist
    archived_dir = Path("archived_documentation")
    archived_dir.mkdir(exist_ok=True)
    
    # Get all markdown files
    markdown_files = []
    for file_path in Path(".").glob("*.md"):
        if (file_path.name not in ["README.md", "CONSOLIDATED_DOCUMENTATION.md"] and
            "node_modules" not in str(file_path) and
            "venv" not in str(file_path)):
            
            stat = file_path.stat()
            markdown_files.append({
                'path': file_path,
                'name': file_path.name,
                'size': stat.st_size,
                'modified': datetime.datetime.fromtimestamp(stat.st_mtime)
            })
    
    print("🔍 ANALYZING MARKDOWN FILES FOR DEPRECATION")
    print("=" * 60)
    
    files_to_deprecate = []
    files_to_keep = []
    
    for file_info in markdown_files:
        should_deprecate, reason = should_deprecate_file(
            file_info['name'], 
            file_info['size'], 
            file_info['modified']
        )
        
        if should_deprecate:
            files_to_deprecate.append((file_info, reason))
        else:
            files_to_keep.append(file_info)
    
    print(f"\n📊 ANALYSIS RESULTS:")
    print(f"   Total markdown files found: {len(markdown_files)}")
    print(f"   Files to deprecate: {len(files_to_deprecate)}")
    print(f"   Files to keep: {len(files_to_keep)}")
    
    if files_to_deprecate:
        print(f"\n🗑️  FILES TO DEPRECATE:")
        for file_info, reason in files_to_deprecate:
            print(f"   📄 {file_info['name']}")
            print(f"      Size: {file_info['size']:,} bytes")
            print(f"      Modified: {file_info['modified'].strftime('%Y-%m-%d')}")
            print(f"      Reason: {reason}")
            print()
    
    if files_to_keep:
        print(f"\n✅ FILES TO KEEP:")
        for file_info in files_to_keep:
            print(f"   📄 {file_info['name']}")
    
    # Proceed with deprecation automatically
    if files_to_deprecate:
        print(f"\n🔄 DEPRECATING {len(files_to_deprecate)} FILES...")
        
        successful_deprecations = 0
        failed_deprecations = 0
        
        for file_info, reason in files_to_deprecate:
            original_path = file_info['path']
            archived_path = archived_dir / f"DEPRECATED_{file_info['name']}"
            
            try:
                # Read original content
                with open(original_path, 'r', encoding='utf-8') as f:
                    original_content = f.read()
                
                # Create deprecation notice
                deprecation_content = create_deprecation_notice(original_content, reason)
                
                # Write deprecation notice to original location
                with open(original_path, 'w', encoding='utf-8') as f:
                    f.write(deprecation_content)
                
                # Move original file to archived directory
                shutil.move(str(original_path), str(archived_path))
                
                print(f"   ✅ Deprecated: {file_info['name']}")
                successful_deprecations += 1
                
            except Exception as e:
                print(f"   ❌ Error deprecating {file_info['name']}: {e}")
                failed_deprecations += 1
        
        print(f"\n✅ DEPRECATION COMPLETE!")
        print(f"   Successfully deprecated: {successful_deprecations}")
        print(f"   Failed deprecations: {failed_deprecations}")
        print(f"   Archived files: {successful_deprecations}")
        print(f"   Original locations updated with deprecation notices")
        
        return successful_deprecations, failed_deprecations
    else:
        print("\n✅ No files need deprecation!")
        return 0, 0

if __name__ == "__main__":
    auto_deprecate_markdown_files() 