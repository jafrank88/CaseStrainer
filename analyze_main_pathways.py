#!/usr/bin/env python3
"""
Analyze main sync and async pathways for stubs, disabled features, or deprecated functions
"""

import sys
from pathlib import Path
import re

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

def analyze_sync_pathway():
    """Analyze the main sync processing pathway."""
    print("🔍 ANALYZING SYNC PATHWAY")
    print("=" * 60)
    print("Current sync path: UnifiedInputProcessor → UnifiedCitationProcessorV2")
    print("=" * 60)
    
    # Files in the sync pathway
    sync_files = [
        "vue_api_endpoints.py",
        "unified_input_processor.py", 
        "unified_citation_processor_v2.py",
        "unified_citation_clustering.py"
    ]
    
    issues_found = []
    
    for filename in sync_files:
        print(f"\n📋 Analyzing {filename}")
        print("-" * 40)
        
        try:
            file_path = Path(__file__).parent / 'src' / filename
            if not file_path.exists():
                print(f"❌ File not found: {filename}")
                continue
                
            content = file_path.read_text(encoding='utf-8')
            
            # Look for stubs and disabled features
            stub_patterns = [
                (r'def.*:\s*pass\s*$', "Stub function (pass only)"),
                (r'def.*:\s*return\s*None\s*$', "Stub function (return None)"),
                (r'def.*:\s*raise\s+NotImplementedError', "Not implemented function"),
                (r'#\s*TODO', "TODO comments"),
                (r'#\s*FIXME', "FIXME comments"),
                (r'#\s*STUB', "Stub comments"),
                (r'#\s*DISABLED', "Disabled features"),
                (r'if\s+False:', "Disabled code blocks"),
                (r'enable_.*=\s*False', "Disabled features"),
                (r'DEPRECATED', "Deprecated functions"),
                (r'warnings\.warn', "Deprecation warnings")
            ]
            
            file_issues = []
            for pattern, description in stub_patterns:
                matches = re.findall(pattern, content, re.MULTILINE | re.IGNORECASE)
                if matches:
                    file_issues.append(f"{description}: {len(matches)} found")
            
            if file_issues:
                print("⚠️ Issues found:")
                for issue in file_issues:
                    print(f"   • {issue}")
                issues_found.extend([(filename, issue) for issue in file_issues])
            else:
                print("✅ No obvious stubs or disabled features found")
                
        except Exception as e:
            print(f"❌ Error analyzing {filename}: {e}")
    
    return issues_found

def analyze_async_pathway():
    """Analyze the main async processing pathway."""
    print(f"\n🔍 ANALYZING ASYNC PATHWAY")
    print("=" * 60)
    print("Current async path: UnifiedInputProcessor → process_citation_task_direct → UnifiedCitationProcessorV2")
    print("=" * 60)
    
    # Files in the async pathway
    async_files = [
        "vue_api_endpoints.py",
        "unified_input_processor.py",
        "progress_manager.py",
        "unified_citation_processor_v2.py",
        "unified_citation_clustering.py"
    ]
    
    issues_found = []
    
    for filename in async_files:
        print(f"\n📋 Analyzing {filename}")
        print("-" * 40)
        
        try:
            file_path = Path(__file__).parent / 'src' / filename
            if not file_path.exists():
                print(f"❌ File not found: {filename}")
                continue
                
            content = file_path.read_text(encoding='utf-8')
            
            # Look for async-specific issues
            async_patterns = [
                (r'def.*:\s*pass\s*$', "Stub function (pass only)"),
                (r'def.*:\s*return\s*None\s*$', "Stub function (return None)"),
                (r'def.*:\s*raise\s+NotImplementedError', "Not implemented function"),
                (r'#\s*TODO.*async', "Async TODO comments"),
                (r'#\s*FIXME.*async', "Async FIXME comments"),
                (r'#\s*BROKEN.*async', "Broken async features"),
                (r'async\s+def.*:\s*pass', "Async stub functions"),
                (r'await.*#.*disabled', "Disabled async calls"),
                (r'redis.*#.*disabled', "Disabled Redis features"),
                (r'queue.*#.*disabled', "Disabled queue features")
            ]
            
            file_issues = []
            for pattern, description in async_patterns:
                matches = re.findall(pattern, content, re.MULTILINE | re.IGNORECASE)
                if matches:
                    file_issues.append(f"{description}: {len(matches)} found")
            
            if file_issues:
                print("⚠️ Issues found:")
                for issue in file_issues:
                    print(f"   • {issue}")
                issues_found.extend([(filename, issue) for issue in file_issues])
            else:
                print("✅ No obvious async stubs or disabled features found")
                
        except Exception as e:
            print(f"❌ Error analyzing {filename}: {e}")
    
    return issues_found

def check_specific_known_issues():
    """Check for specific known issues from memories."""
    print(f"\n🔍 CHECKING KNOWN ISSUES FROM MEMORIES")
    print("=" * 60)
    
    known_issues = []
    
    # Check async result retrieval issue
    print("📋 Checking async result retrieval issue...")
    try:
        file_path = Path(__file__).parent / 'src' / 'progress_manager.py'
        content = file_path.read_text(encoding='utf-8')
        
        # Look for result storage/retrieval patterns
        if 'task_id' in content and 'result' in content:
            print("✅ Async task result handling found")
            
            # Check for potential issues
            if 'redis' in content.lower():
                print("✅ Redis integration present")
            else:
                print("⚠️ Redis integration may be missing")
                known_issues.append("Redis integration check needed")
                
        else:
            print("⚠️ Async result handling may be incomplete")
            known_issues.append("Async result handling incomplete")
            
    except Exception as e:
        print(f"❌ Error checking async results: {e}")
    
    # Check deduplication implementation
    print("\n📋 Checking deduplication implementation...")
    try:
        file_path = Path(__file__).parent / 'src' / 'unified_citation_processor_v2.py'
        content = file_path.read_text(encoding='utf-8')
        
        if 'deduplication' in content.lower() or 'deduplicate' in content.lower():
            print("✅ Deduplication logic found")
        else:
            print("⚠️ Deduplication may not be implemented")
            known_issues.append("Deduplication implementation missing")
            
    except Exception as e:
        print(f"❌ Error checking deduplication: {e}")
    
    # Check verification integration
    print("\n📋 Checking verification integration...")
    try:
        file_path = Path(__file__).parent / 'src' / 'unified_citation_clustering.py'
        content = file_path.read_text(encoding='utf-8')
        
        if 'enable_verification' in content and 'verify' in content:
            print("✅ Verification integration found")
        else:
            print("⚠️ Verification integration may be incomplete")
            known_issues.append("Verification integration check needed")
            
    except Exception as e:
        print(f"❌ Error checking verification: {e}")
    
    return known_issues

def check_disabled_features():
    """Check for specifically disabled features in configuration."""
    print(f"\n🔍 CHECKING DISABLED FEATURES IN CONFIGURATION")
    print("=" * 60)
    
    config_files = [
        "models.py",
        "config.py",
        "unified_citation_processor_v2.py"
    ]
    
    disabled_features = []
    
    for filename in config_files:
        print(f"\n📋 Checking {filename} for disabled features...")
        
        try:
            file_path = Path(__file__).parent / 'src' / filename
            if not file_path.exists():
                continue
                
            content = file_path.read_text(encoding='utf-8')
            
            # Look for disabled features
            disabled_patterns = [
                (r'enable_.*=\s*False', "Disabled feature flags"),
                (r'.*_enabled\s*=\s*False', "Disabled components"),
                (r'debug_mode\s*=\s*False', "Debug mode disabled"),
                (r'verification.*=\s*False', "Verification disabled"),
                (r'clustering.*=\s*False', "Clustering disabled"),
                (r'deduplication.*=\s*False', "Deduplication disabled")
            ]
            
            for pattern, description in disabled_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    print(f"   ⚠️ {description}: {matches}")
                    disabled_features.extend(matches)
                    
        except Exception as e:
            print(f"❌ Error checking {filename}: {e}")
    
    if not disabled_features:
        print("✅ No explicitly disabled features found in configuration")
    
    return disabled_features

def analyze_function_completeness():
    """Analyze if key functions are complete or just stubs."""
    print(f"\n🔍 ANALYZING FUNCTION COMPLETENESS")
    print("=" * 60)
    
    key_functions = [
        ("unified_citation_processor_v2.py", "process_text"),
        ("unified_citation_processor_v2.py", "_extract_citations_unified"),
        ("unified_citation_processor_v2.py", "_verify_citations_sync"),
        ("unified_citation_clustering.py", "cluster_citations_unified"),
        ("progress_manager.py", "process_citation_task_direct")
    ]
    
    incomplete_functions = []
    
    for filename, function_name in key_functions:
        print(f"\n📋 Checking {function_name} in {filename}...")
        
        try:
            file_path = Path(__file__).parent / 'src' / filename
            if not file_path.exists():
                print(f"❌ File not found: {filename}")
                continue
                
            content = file_path.read_text(encoding='utf-8')
            
            # Find the function
            function_pattern = rf'def\s+{function_name}\s*\([^)]*\):'
            match = re.search(function_pattern, content)
            
            if not match:
                print(f"❌ Function {function_name} not found")
                incomplete_functions.append(f"{filename}::{function_name} - Not found")
                continue
            
            # Get function body (rough approximation)
            start_pos = match.end()
            lines = content[start_pos:].split('\n')
            
            # Check if it's just a stub
            function_body = []
            indent_level = None
            
            for line in lines[:20]:  # Check first 20 lines
                if line.strip() == '':
                    continue
                    
                current_indent = len(line) - len(line.lstrip())
                
                if indent_level is None:
                    indent_level = current_indent
                elif current_indent <= indent_level and line.strip():
                    break  # End of function
                    
                function_body.append(line.strip())
            
            # Analyze function body
            body_text = ' '.join(function_body)
            
            if len(function_body) <= 2:
                print(f"⚠️ Very short function - may be stub")
                incomplete_functions.append(f"{filename}::{function_name} - Very short")
            elif 'pass' in body_text and len(function_body) <= 3:
                print(f"⚠️ Function contains only 'pass' - stub")
                incomplete_functions.append(f"{filename}::{function_name} - Stub (pass)")
            elif 'NotImplementedError' in body_text:
                print(f"⚠️ Function raises NotImplementedError - not implemented")
                incomplete_functions.append(f"{filename}::{function_name} - Not implemented")
            elif 'return None' in body_text and len(function_body) <= 3:
                print(f"⚠️ Function only returns None - may be stub")
                incomplete_functions.append(f"{filename}::{function_name} - Returns None only")
            else:
                print(f"✅ Function appears complete ({len(function_body)} lines)")
                
        except Exception as e:
            print(f"❌ Error analyzing {function_name}: {e}")
    
    return incomplete_functions

def main():
    print("🔍 Analyzing Main Sync and Async Pathways")
    print("=" * 70)
    print("Looking for stubs, disabled features, and deprecated functions")
    print("=" * 70)
    
    sync_issues = analyze_sync_pathway()
    async_issues = analyze_async_pathway()
    known_issues = check_specific_known_issues()
    disabled_features = check_disabled_features()
    incomplete_functions = analyze_function_completeness()
    
    print(f"\n" + "=" * 70)
    print("📋 COMPREHENSIVE ANALYSIS SUMMARY")
    print("=" * 70)
    
    print(f"\n🔄 SYNC PATHWAY ISSUES:")
    if sync_issues:
        for filename, issue in sync_issues:
            print(f"   • {filename}: {issue}")
    else:
        print("   ✅ No significant issues found in sync pathway")
    
    print(f"\n⚡ ASYNC PATHWAY ISSUES:")
    if async_issues:
        for filename, issue in async_issues:
            print(f"   • {filename}: {issue}")
    else:
        print("   ✅ No significant issues found in async pathway")
    
    print(f"\n🎯 KNOWN ISSUES FROM MEMORIES:")
    if known_issues:
        for issue in known_issues:
            print(f"   • {issue}")
    else:
        print("   ✅ No known issues detected")
    
    print(f"\n⚙️ DISABLED FEATURES:")
    if disabled_features:
        for feature in disabled_features:
            print(f"   • {feature}")
    else:
        print("   ✅ No explicitly disabled features found")
    
    print(f"\n🔧 INCOMPLETE FUNCTIONS:")
    if incomplete_functions:
        for func in incomplete_functions:
            print(f"   • {func}")
    else:
        print("   ✅ All key functions appear complete")
    
    total_issues = len(sync_issues) + len(async_issues) + len(known_issues) + len(disabled_features) + len(incomplete_functions)
    
    print(f"\n🎯 OVERALL ASSESSMENT:")
    if total_issues == 0:
        print("✅ Main pathways appear clean and functional")
    elif total_issues <= 3:
        print("⚠️ Minor issues found - should be addressed")
    else:
        print("🔴 Multiple issues found - needs attention")
    
    print(f"\n💡 RECOMMENDATIONS:")
    print("• Review any identified stubs or incomplete functions")
    print("• Check disabled features to see if they should be enabled")
    print("• Address known issues from previous analysis")
    print("• Test both sync and async pathways thoroughly")

if __name__ == "__main__":
    main()
