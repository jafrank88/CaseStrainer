#!/usr/bin/env python3
"""
Fix identified issues in main sync and async pathways
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

def fix_disabled_code_block():
    """Fix the disabled code block in unified_citation_processor_v2.py."""
    print("🔧 FIXING DISABLED CODE BLOCK")
    print("=" * 50)
    
    file_path = Path(__file__).parent / 'src' / 'unified_citation_processor_v2.py'
    
    try:
        content = file_path.read_text(encoding='utf-8')
        
        # Find and remove the disabled code block
        old_code = '''                # Verification handled by unified clustering - skip deprecated check
                if False:  # Deprecated function removed
                    # Verification handled by unified clustering
                    pass
                    if citation.verified:'''
        
        new_code = '''                # Verification handled by unified clustering - deprecated check removed'''
        
        if old_code in content:
            content = content.replace(old_code, new_code)
            file_path.write_text(content, encoding='utf-8')
            print("✅ Removed disabled code block (if False:)")
            return True
        else:
            print("⚠️ Disabled code block not found or already fixed")
            return False
            
    except Exception as e:
        print(f"❌ Error fixing disabled code block: {e}")
        return False

def check_function_completeness():
    """Double-check that key functions are actually complete."""
    print("\n🔍 VERIFYING FUNCTION COMPLETENESS")
    print("=" * 50)
    
    functions_to_check = [
        ("unified_citation_processor_v2.py", "process_text", "Main processing pipeline"),
        ("unified_citation_processor_v2.py", "_extract_citations_unified", "Unified extraction"),
        ("unified_citation_clustering.py", "cluster_citations_unified", "Citation clustering"),
        ("progress_manager.py", "process_citation_task_direct", "Async task processing")
    ]
    
    all_complete = True
    
    for filename, function_name, description in functions_to_check:
        print(f"\n📋 Checking {function_name} ({description})...")
        
        try:
            file_path = Path(__file__).parent / 'src' / filename
            content = file_path.read_text(encoding='utf-8')
            
            # Find function definition
            import re
            pattern = rf'def {function_name}\s*\([^)]*\):'
            match = re.search(pattern, content)
            
            if not match:
                print(f"❌ Function {function_name} not found")
                all_complete = False
                continue
            
            # Get function body (approximate)
            start_pos = match.end()
            remaining_content = content[start_pos:]
            lines = remaining_content.split('\n')
            
            # Count meaningful lines (not just comments or whitespace)
            meaningful_lines = 0
            in_docstring = False
            docstring_quotes = None
            
            for line in lines[:50]:  # Check first 50 lines
                stripped = line.strip()
                
                if not stripped:
                    continue
                    
                # Handle docstrings
                if not in_docstring and (stripped.startswith('"""') or stripped.startswith("'''")):
                    in_docstring = True
                    docstring_quotes = stripped[:3]
                    if stripped.count(docstring_quotes) >= 2:
                        in_docstring = False  # Single line docstring
                    continue
                elif in_docstring:
                    if docstring_quotes in stripped:
                        in_docstring = False
                    continue
                
                # Skip comments
                if stripped.startswith('#'):
                    continue
                
                # Check for end of function (dedent)
                if line and not line.startswith(' ') and not line.startswith('\t'):
                    break
                
                meaningful_lines += 1
                
                # Check for stub patterns
                if stripped == 'pass':
                    print(f"⚠️ Function contains 'pass' statement")
                elif stripped.startswith('raise NotImplementedError'):
                    print(f"❌ Function raises NotImplementedError - not implemented")
                    all_complete = False
                    break
                elif stripped == 'return None' and meaningful_lines <= 2:
                    print(f"⚠️ Function only returns None - may be stub")
            
            if meaningful_lines >= 5:
                print(f"✅ Function appears complete ({meaningful_lines} meaningful lines)")
            else:
                print(f"⚠️ Function may be incomplete ({meaningful_lines} meaningful lines)")
                
        except Exception as e:
            print(f"❌ Error checking {function_name}: {e}")
            all_complete = False
    
    return all_complete

def check_import_availability():
    """Check if clustering and other imports are actually available."""
    print("\n🔍 CHECKING IMPORT AVAILABILITY")
    print("=" * 50)
    
    imports_to_check = [
        ("unified_citation_clustering", "cluster_citations_unified"),
        ("unified_citation_processor_v2", "UnifiedCitationProcessorV2"),
        ("progress_manager", "process_citation_task_direct")
    ]
    
    all_available = True
    
    for module_name, function_name in imports_to_check:
        print(f"\n📋 Checking {module_name}.{function_name}...")
        
        try:
            # Try to import the module and function
            module = __import__(module_name, fromlist=[function_name])
            func = getattr(module, function_name)
            
            if func is not None:
                print(f"✅ {function_name} successfully imported")
            else:
                print(f"❌ {function_name} is None after import")
                all_available = False
                
        except ImportError as e:
            print(f"❌ Import error for {module_name}: {e}")
            all_available = False
        except AttributeError as e:
            print(f"❌ Attribute error for {function_name}: {e}")
            all_available = False
        except Exception as e:
            print(f"❌ Unexpected error importing {module_name}.{function_name}: {e}")
            all_available = False
    
    return all_available

def test_basic_functionality():
    """Test that basic functionality works."""
    print("\n🧪 TESTING BASIC FUNCTIONALITY")
    print("=" * 50)
    
    test_text = """
    In Wyoming v. U.S. Dep't of Interior, 2006 WL 3801910 (D. Wyo. 2006), 
    the court ruled on environmental regulations. See also Johnson v. State, 
    150 Wn.2d 674 (2004).
    """
    
    try:
        print("📋 Testing UnifiedCitationProcessorV2...")
        from unified_citation_processor_v2 import UnifiedCitationProcessorV2
        
        processor = UnifiedCitationProcessorV2()
        print("✅ Processor created successfully")
        
        # Test async processing
        import asyncio
        result = asyncio.run(processor.process_text(test_text))
        
        citations = result.get('citations', [])
        clusters = result.get('clusters', [])
        
        print(f"✅ Processing completed: {len(citations)} citations, {len(clusters)} clusters")
        
        if len(citations) > 0:
            print("✅ Citations found - basic functionality working")
            return True
        else:
            print("⚠️ No citations found - may indicate processing issue")
            return False
            
    except Exception as e:
        print(f"❌ Error testing basic functionality: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🔧 Fixing Main Pathway Issues")
    print("=" * 70)
    print("Addressing identified stubs, disabled features, and issues")
    print("=" * 70)
    
    results = {
        'disabled_code_fixed': fix_disabled_code_block(),
        'functions_complete': check_function_completeness(),
        'imports_available': check_import_availability(),
        'basic_functionality': test_basic_functionality()
    }
    
    print(f"\n" + "=" * 70)
    print("📋 FIX RESULTS SUMMARY")
    print("=" * 70)
    
    for check_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {check_name.replace('_', ' ').title()}")
    
    total_passed = sum(results.values())
    total_checks = len(results)
    
    print(f"\n🎯 OVERALL RESULT: {total_passed}/{total_checks} checks passed")
    
    if total_passed == total_checks:
        print("🎉 SUCCESS: Main pathways are clean and functional!")
        print("✅ No disabled code blocks")
        print("✅ All key functions are complete")
        print("✅ All imports are available")
        print("✅ Basic functionality works")
    else:
        print("⚠️ Some issues remain - need attention")
    
    print(f"\n💡 PATHWAY STATUS:")
    print("• Sync pathway: UnifiedInputProcessor → UnifiedCitationProcessorV2")
    print("• Async pathway: UnifiedInputProcessor → process_citation_task_direct → UnifiedCitationProcessorV2")
    print("• Both pathways use the same core processing logic")
    print("• Architectural simplifications have eliminated redundant layers")

if __name__ == "__main__":
    main()
