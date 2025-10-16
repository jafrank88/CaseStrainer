#!/usr/bin/env python3
"""
Analysis of which functions/classes can now be deprecated after feature extraction
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

def analyze_deprecation_candidates():
    """Analyze which processors and functions can now be deprecated."""
    print("🔍 DEPRECATION ANALYSIS")
    print("=" * 70)
    print("Identifying functions/classes that can be deprecated after feature extraction")
    print("=" * 70)
    
    deprecation_candidates = {
        "EnhancedSyncProcessor": {
            "file": "enhanced_sync_processor.py",
            "reason": "Features extracted to UnifiedCitationProcessorV2",
            "extracted_features": [
                "Progress callbacks",
                "False positive prevention",
                "_filter_false_positive_citations()",
                "_is_standalone_page_number()",
                "_is_volume_without_reporter()"
            ],
            "remaining_unique_features": [
                "ProcessingOptions class (still used elsewhere)",
                "Some threshold configurations"
            ],
            "deprecation_status": "PARTIAL - Keep ProcessingOptions, deprecate main class",
            "priority": "High"
        },
        
        "EnhancedSyncProcessorRefactored": {
            "file": "enhanced_sync_processor_refactored.py", 
            "reason": "Duplicate of EnhancedSyncProcessor with same features",
            "extracted_features": [
                "Basic processing options",
                "Modular component structure"
            ],
            "remaining_unique_features": [],
            "deprecation_status": "FULL DEPRECATION - No unique features",
            "priority": "High"
        },
        
        "UnifiedSyncProcessor": {
            "file": "unified_sync_processor.py",
            "reason": "Bypassed by architectural simplification",
            "extracted_features": [
                "Washington citation verification logic"
            ],
            "remaining_unique_features": [
                "Some specific sync processing logic",
                "Clustering with verification integration"
            ],
            "deprecation_status": "PARTIAL - May still be used in some paths",
            "priority": "Medium"
        },
        
        "Enhanced Clustering Classes": {
            "file": "enhanced_clustering.py",
            "reason": "Features moved to unified clustering system",
            "extracted_features": [
                "Proximity-based parallel detection",
                "Advanced similarity matching"
            ],
            "remaining_unique_features": [],
            "deprecation_status": "FULL DEPRECATION - Features in unified_citation_clustering.py",
            "priority": "Medium"
        },
        
        "Enhanced Verification Classes": {
            "file": "enhanced_courtlistener_verification.py, enhanced_fallback_verifier.py",
            "reason": "Verification now handled by unified clustering",
            "extracted_features": [
                "Enhanced error handling",
                "Rate limiting logic"
            ],
            "remaining_unique_features": [
                "Some specific API handling logic"
            ],
            "deprecation_status": "EVALUATE - May have unique API handling",
            "priority": "Low"
        }
    }
    
    for component, info in deprecation_candidates.items():
        print(f"\n📋 {component}")
        print("-" * 50)
        print(f"File: {info['file']}")
        print(f"Reason: {info['reason']}")
        print(f"Extracted Features: {', '.join(info['extracted_features'])}")
        print(f"Remaining Unique: {', '.join(info['remaining_unique_features']) if info['remaining_unique_features'] else 'None'}")
        print(f"Status: {info['deprecation_status']}")
        print(f"Priority: {info['priority']}")
    
    return deprecation_candidates

def check_current_usage():
    """Check which deprecated candidates are still being imported/used."""
    print(f"\n🔍 USAGE ANALYSIS")
    print("=" * 50)
    
    import os
    import re
    
    # Files to check for imports
    src_dir = Path(__file__).parent / 'src'
    usage_analysis = {}
    
    components_to_check = [
        "EnhancedSyncProcessor",
        "enhanced_sync_processor_refactored", 
        "enhanced_clustering",
        "enhanced_courtlistener_verification",
        "enhanced_fallback_verifier"
    ]
    
    for component in components_to_check:
        usage_analysis[component] = {
            "imported_by": [],
            "usage_count": 0
        }
        
        # Search for imports in all Python files
        for py_file in src_dir.glob("**/*.py"):
            try:
                content = py_file.read_text(encoding='utf-8')
                
                # Check for imports
                import_patterns = [
                    f"from.*{component}",
                    f"import.*{component}",
                    f"{component}\\(",  # Direct usage
                ]
                
                for pattern in import_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        usage_analysis[component]["imported_by"].append(str(py_file.name))
                        usage_analysis[component]["usage_count"] += len(re.findall(pattern, content, re.IGNORECASE))
                        
            except Exception as e:
                continue
    
    for component, usage in usage_analysis.items():
        print(f"\n📋 {component}")
        print(f"   Usage Count: {usage['usage_count']}")
        print(f"   Used By: {', '.join(set(usage['imported_by'])) if usage['imported_by'] else 'None'}")
        
        if usage['usage_count'] == 0:
            print(f"   ✅ SAFE TO DEPRECATE - No current usage found")
        else:
            print(f"   ⚠️ STILL IN USE - Need to update imports before deprecation")
    
    return usage_analysis

def recommend_deprecation_plan():
    """Recommend a phased deprecation plan."""
    print(f"\n📋 DEPRECATION PLAN")
    print("=" * 50)
    
    phases = [
        {
            "phase": "Phase 1: Immediate Deprecation",
            "components": [
                "enhanced_sync_processor_refactored.py",
                "enhanced_clustering.py (if not used)"
            ],
            "reason": "Complete duplicates with no unique features",
            "action": "Add deprecation warnings, mark for removal in next version",
            "risk": "Low"
        },
        {
            "phase": "Phase 2: Gradual Deprecation", 
            "components": [
                "EnhancedSyncProcessor class",
                "Enhanced verification classes"
            ],
            "reason": "Main features extracted, some edge cases may remain",
            "action": "Add deprecation warnings, migrate remaining usage",
            "risk": "Medium"
        },
        {
            "phase": "Phase 3: Evaluation",
            "components": [
                "UnifiedSyncProcessor",
                "ProcessingOptions class"
            ],
            "reason": "May still have valid use cases in specific scenarios",
            "action": "Evaluate usage patterns, consider keeping or deprecating",
            "risk": "High"
        }
    ]
    
    for phase in phases:
        print(f"\n🎯 {phase['phase']}")
        print(f"   Components: {', '.join(phase['components'])}")
        print(f"   Reason: {phase['reason']}")
        print(f"   Action: {phase['action']}")
        print(f"   Risk: {phase['risk']}")
    
    print(f"\n💡 IMPLEMENTATION STRATEGY:")
    print("1. Add deprecation warnings to identified components")
    print("2. Update imports to use UnifiedCitationProcessorV2")
    print("3. Test thoroughly to ensure no functionality loss")
    print("4. Remove deprecated code in next major version")
    print("5. Update documentation to reflect changes")

def generate_deprecation_warnings():
    """Generate deprecation warning code to add to identified files."""
    print(f"\n🔧 DEPRECATION WARNING CODE")
    print("=" * 50)
    
    warning_template = '''
import warnings

def deprecated_function_warning(old_name, new_name, version="v3.0.0"):
    """Generate a deprecation warning."""
    warnings.warn(
        f"{old_name} is deprecated and will be removed in {version}. "
        f"Use {new_name} instead.",
        DeprecationWarning,
        stacklevel=3
    )

# Example usage in EnhancedSyncProcessor:
class EnhancedSyncProcessor:
    def __init__(self, *args, **kwargs):
        deprecated_function_warning(
            "EnhancedSyncProcessor", 
            "UnifiedCitationProcessorV2"
        )
        # ... rest of init
'''
    
    print("📝 Add this template to deprecated classes:")
    print(warning_template)
    
    print("\n📝 Specific deprecation messages:")
    
    messages = {
        "EnhancedSyncProcessor": "Use UnifiedCitationProcessorV2 with progress_callback parameter",
        "enhanced_sync_processor_refactored": "Use UnifiedCitationProcessorV2 directly",
        "enhanced_clustering": "Use unified_citation_clustering.cluster_citations_unified()",
        "enhanced_verification": "Verification is now integrated into the main clustering system"
    }
    
    for component, message in messages.items():
        print(f"   {component}: {message}")

def main():
    print("🔍 CaseStrainer Deprecation Analysis")
    print("=" * 70)
    print("Analyzing which components can be deprecated after feature extraction")
    print("=" * 70)
    
    candidates = analyze_deprecation_candidates()
    usage = check_current_usage()
    recommend_deprecation_plan()
    generate_deprecation_warnings()
    
    print(f"\n" + "=" * 70)
    print("📋 SUMMARY")
    print("=" * 70)
    print("✅ Identified components ready for deprecation")
    print("✅ Analyzed current usage patterns")
    print("✅ Created phased deprecation plan")
    print("✅ Generated deprecation warning templates")
    
    print(f"\n🎯 NEXT STEPS:")
    print("1. Implement Phase 1 deprecations (safe, no usage)")
    print("2. Add deprecation warnings to Phase 2 components")
    print("3. Update any remaining imports to use main pipeline")
    print("4. Test thoroughly before removing deprecated code")
    
    print(f"\n💡 BENEFITS:")
    print("• Cleaner codebase with less duplication")
    print("• Clearer architecture with single main pipeline")
    print("• Easier maintenance with fewer code paths")
    print("• Better developer experience with unified API")

if __name__ == "__main__":
    main()
