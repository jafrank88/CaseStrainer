#!/usr/bin/env python3
"""
Test that deprecation warnings are properly issued for deprecated components
"""

import sys
from pathlib import Path
import warnings

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

def test_enhanced_sync_processor_deprecation():
    """Test that EnhancedSyncProcessor issues deprecation warning."""
    print("🧪 Testing EnhancedSyncProcessor Deprecation Warning")
    print("=" * 60)
    
    warnings_captured = []
    
    def warning_handler(message, category, filename, lineno, file=None, line=None):
        warnings_captured.append({
            'message': str(message),
            'category': category.__name__,
            'filename': filename,
            'lineno': lineno
        })
    
    # Capture warnings
    old_showwarning = warnings.showwarning
    warnings.showwarning = warning_handler
    
    try:
        # Import and instantiate EnhancedSyncProcessor
        from enhanced_sync_processor import EnhancedSyncProcessor
        
        # This should trigger a deprecation warning
        processor = EnhancedSyncProcessor()
        
        # Check if deprecation warning was issued
        deprecation_warnings = [w for w in warnings_captured if w['category'] == 'DeprecationWarning']
        
        print(f"✅ Warnings captured: {len(warnings_captured)}")
        print(f"✅ Deprecation warnings: {len(deprecation_warnings)}")
        
        if deprecation_warnings:
            for warning in deprecation_warnings:
                print(f"📋 Warning: {warning['message']}")
            print("🎉 SUCCESS: EnhancedSyncProcessor properly issues deprecation warning!")
            return True
        else:
            print("❌ FAILURE: No deprecation warning issued")
            return False
            
    except Exception as e:
        print(f"❌ Error testing EnhancedSyncProcessor: {e}")
        return False
    finally:
        warnings.showwarning = old_showwarning

def test_enhanced_sync_processor_refactored_deprecation():
    """Test that EnhancedSyncProcessorRefactored issues deprecation warning."""
    print("\n🧪 Testing EnhancedSyncProcessorRefactored Deprecation Warning")
    print("=" * 60)
    
    warnings_captured = []
    
    def warning_handler(message, category, filename, lineno, file=None, line=None):
        warnings_captured.append({
            'message': str(message),
            'category': category.__name__,
            'filename': filename,
            'lineno': lineno
        })
    
    # Capture warnings
    old_showwarning = warnings.showwarning
    warnings.showwarning = warning_handler
    
    try:
        # Import and instantiate EnhancedSyncProcessorRefactored
        from enhanced_sync_processor_refactored import EnhancedSyncProcessor as RefactoredProcessor
        
        # This should trigger a deprecation warning
        processor = RefactoredProcessor()
        
        # Check if deprecation warning was issued
        deprecation_warnings = [w for w in warnings_captured if w['category'] == 'DeprecationWarning']
        
        print(f"✅ Warnings captured: {len(warnings_captured)}")
        print(f"✅ Deprecation warnings: {len(deprecation_warnings)}")
        
        if deprecation_warnings:
            for warning in deprecation_warnings:
                print(f"📋 Warning: {warning['message']}")
            print("🎉 SUCCESS: EnhancedSyncProcessorRefactored properly issues deprecation warning!")
            return True
        else:
            print("❌ FAILURE: No deprecation warning issued")
            return False
            
    except Exception as e:
        print(f"❌ Error testing EnhancedSyncProcessorRefactored: {e}")
        return False
    finally:
        warnings.showwarning = old_showwarning

def test_unified_processor_no_warnings():
    """Test that UnifiedCitationProcessorV2 does not issue deprecation warnings."""
    print("\n🧪 Testing UnifiedCitationProcessorV2 (No Warnings Expected)")
    print("=" * 60)
    
    warnings_captured = []
    
    def warning_handler(message, category, filename, lineno, file=None, line=None):
        warnings_captured.append({
            'message': str(message),
            'category': category.__name__,
            'filename': filename,
            'lineno': lineno
        })
    
    # Capture warnings
    old_showwarning = warnings.showwarning
    warnings.showwarning = warning_handler
    
    try:
        # Import and instantiate UnifiedCitationProcessorV2
        from unified_citation_processor_v2 import UnifiedCitationProcessorV2
        
        # This should NOT trigger any deprecation warnings
        processor = UnifiedCitationProcessorV2()
        
        # Check if any warnings were issued
        deprecation_warnings = [w for w in warnings_captured if w['category'] == 'DeprecationWarning']
        
        print(f"✅ Warnings captured: {len(warnings_captured)}")
        print(f"✅ Deprecation warnings: {len(deprecation_warnings)}")
        
        if len(deprecation_warnings) == 0:
            print("🎉 SUCCESS: UnifiedCitationProcessorV2 does not issue deprecation warnings!")
            return True
        else:
            print("❌ UNEXPECTED: UnifiedCitationProcessorV2 issued deprecation warnings")
            for warning in deprecation_warnings:
                print(f"📋 Unexpected warning: {warning['message']}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing UnifiedCitationProcessorV2: {e}")
        return False
    finally:
        warnings.showwarning = old_showwarning

def test_migration_guidance():
    """Test that deprecation warnings provide clear migration guidance."""
    print("\n🧪 Testing Migration Guidance in Warnings")
    print("=" * 60)
    
    expected_guidance = [
        "UnifiedCitationProcessorV2",
        "progress_callback",
        "v3.0.0"
    ]
    
    warnings_captured = []
    
    def warning_handler(message, category, filename, lineno, file=None, line=None):
        warnings_captured.append(str(message))
    
    # Capture warnings
    old_showwarning = warnings.showwarning
    warnings.showwarning = warning_handler
    
    try:
        # Trigger deprecation warnings
        from enhanced_sync_processor import EnhancedSyncProcessor
        processor = EnhancedSyncProcessor()
        
        # Check if warnings contain migration guidance
        guidance_found = []
        for warning_msg in warnings_captured:
            for guidance in expected_guidance:
                if guidance in warning_msg:
                    guidance_found.append(guidance)
        
        print(f"✅ Expected guidance elements: {expected_guidance}")
        print(f"✅ Found guidance elements: {list(set(guidance_found))}")
        
        if len(set(guidance_found)) >= 2:  # At least 2 out of 3 guidance elements
            print("🎉 SUCCESS: Deprecation warnings provide clear migration guidance!")
            return True
        else:
            print("❌ FAILURE: Deprecation warnings lack clear migration guidance")
            return False
            
    except Exception as e:
        print(f"❌ Error testing migration guidance: {e}")
        return False
    finally:
        warnings.showwarning = old_showwarning

def main():
    print("🔍 Testing Deprecation Warnings")
    print("=" * 70)
    print("Verifying that deprecated components issue proper warnings")
    print("=" * 70)
    
    results = {
        'enhanced_sync_processor': test_enhanced_sync_processor_deprecation(),
        'enhanced_sync_processor_refactored': test_enhanced_sync_processor_refactored_deprecation(),
        'unified_processor_no_warnings': test_unified_processor_no_warnings(),
        'migration_guidance': test_migration_guidance()
    }
    
    print(f"\n" + "=" * 70)
    print("📋 SUMMARY")
    print("=" * 70)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name.replace('_', ' ').title()}")
    
    total_passed = sum(results.values())
    total_tests = len(results)
    
    print(f"\n🎯 OVERALL RESULT: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("🎉 SUCCESS: All deprecation warnings are working properly!")
        print("✅ Deprecated components issue clear warnings")
        print("✅ Main pipeline components do not issue warnings")
        print("✅ Migration guidance is provided to users")
    else:
        print("⚠️ Some deprecation warnings need attention")
    
    print(f"\n💡 BENEFITS:")
    print("• Users are warned about deprecated components")
    print("• Clear migration path provided")
    print("• Gradual deprecation allows smooth transition")
    print("• Cleaner codebase in future versions")

if __name__ == "__main__":
    main()
