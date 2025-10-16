#!/usr/bin/env python3
"""
Phase 2 and Phase 3 Deprecation Analysis and Implementation
"""

import sys
from pathlib import Path
import re

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

def analyze_phase2_components():
    """Analyze Phase 2 components for deprecation."""
    print("🔍 PHASE 2 ANALYSIS: Enhanced Verification Classes")
    print("=" * 60)
    
    phase2_components = {
        "enhanced_courtlistener_verification.py": {
            "main_class": "EnhancedCourtListenerVerifier",
            "unique_features": [
                "Enhanced API error handling",
                "Rate limiting and retry logic", 
                "Batch verification optimization",
                "Confidence scoring for verification results"
            ],
            "current_usage": "Used in verification_service.py, async_verification_worker.py",
            "replacement": "Verification now integrated into unified clustering system",
            "risk_assessment": "Medium - may have unique API handling logic"
        },
        
        "enhanced_fallback_verifier.py": {
            "main_class": "EnhancedFallbackVerifier",
            "unique_features": [
                "Multi-source fallback verification",
                "Enhanced error recovery",
                "Confidence aggregation from multiple sources"
            ],
            "current_usage": "Used in fallback_integration.py, unified_citation_processor_v2.py",
            "replacement": "Fallback verification integrated into main pipeline",
            "risk_assessment": "Medium - may have unique fallback logic"
        }
    }
    
    for component, info in phase2_components.items():
        print(f"\n📋 {component}")
        print("-" * 40)
        print(f"Main Class: {info['main_class']}")
        print(f"Unique Features: {', '.join(info['unique_features'])}")
        print(f"Current Usage: {info['current_usage']}")
        print(f"Replacement: {info['replacement']}")
        print(f"Risk: {info['risk_assessment']}")
    
    return phase2_components

def analyze_phase3_components():
    """Analyze Phase 3 components for deprecation."""
    print(f"\n🔍 PHASE 3 ANALYSIS: Core Processing Components")
    print("=" * 60)
    
    phase3_components = {
        "UnifiedSyncProcessor": {
            "file": "unified_sync_processor.py",
            "main_class": "UnifiedSyncProcessor", 
            "unique_features": [
                "Sync-specific processing logic",
                "Washington citation verification integration",
                "Clustering with verification coordination"
            ],
            "current_usage": "May still be used in some processing paths",
            "replacement": "UnifiedCitationProcessorV2 handles all processing directly",
            "risk_assessment": "High - may still have valid use cases",
            "bypass_status": "Largely bypassed by architectural simplification"
        },
        
        "ProcessingOptions": {
            "file": "enhanced_sync_processor.py, processors/sync_processor_core.py",
            "main_class": "ProcessingOptions",
            "unique_features": [
                "Enhanced processing configuration",
                "Threshold management",
                "Feature toggle system"
            ],
            "current_usage": "Still used in multiple places",
            "replacement": "ProcessingConfig in models.py",
            "risk_assessment": "High - widely used configuration class",
            "bypass_status": "Still actively used"
        }
    }
    
    for component, info in phase3_components.items():
        print(f"\n📋 {component}")
        print("-" * 40)
        print(f"File: {info['file']}")
        print(f"Main Class: {info['main_class']}")
        print(f"Unique Features: {', '.join(info['unique_features'])}")
        print(f"Current Usage: {info['current_usage']}")
        print(f"Replacement: {info['replacement']}")
        print(f"Risk: {info['risk_assessment']}")
        print(f"Status: {info['bypass_status']}")
    
    return phase3_components

def check_detailed_usage():
    """Check detailed usage of Phase 2 and 3 components."""
    print(f"\n🔍 DETAILED USAGE ANALYSIS")
    print("=" * 50)
    
    import os
    src_dir = Path(__file__).parent / 'src'
    
    components_to_check = [
        "EnhancedCourtListenerVerifier",
        "EnhancedFallbackVerifier", 
        "UnifiedSyncProcessor",
        "ProcessingOptions"
    ]
    
    usage_results = {}
    
    for component in components_to_check:
        usage_results[component] = {
            "files": [],
            "import_count": 0,
            "usage_count": 0
        }
        
        # Search for usage in all Python files
        for py_file in src_dir.glob("**/*.py"):
            try:
                content = py_file.read_text(encoding='utf-8')
                
                # Check for imports and usage
                patterns = [
                    f"from.*{component}",
                    f"import.*{component}",
                    f"{component}\\(",
                    f"class.*{component}"
                ]
                
                file_has_usage = False
                for pattern in patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        usage_results[component]["usage_count"] += len(matches)
                        if not file_has_usage:
                            usage_results[component]["files"].append(py_file.name)
                            file_has_usage = True
                        
            except Exception:
                continue
    
    for component, usage in usage_results.items():
        print(f"\n📋 {component}")
        print(f"   Files using it: {len(usage['files'])}")
        print(f"   Usage count: {usage['usage_count']}")
        print(f"   Files: {', '.join(usage['files'][:5])}{'...' if len(usage['files']) > 5 else ''}")
        
        if usage['usage_count'] == 0:
            print(f"   ✅ SAFE TO DEPRECATE - No usage found")
        elif usage['usage_count'] < 5:
            print(f"   ⚠️ LOW USAGE - Consider deprecation with migration")
        else:
            print(f"   🔴 HIGH USAGE - Careful evaluation needed")
    
    return usage_results

def recommend_phase2_phase3_plan():
    """Recommend implementation plan for Phase 2 and 3."""
    print(f"\n📋 PHASE 2 & 3 IMPLEMENTATION PLAN")
    print("=" * 50)
    
    plan = {
        "Phase 2": {
            "components": ["EnhancedCourtListenerVerifier", "EnhancedFallbackVerifier"],
            "approach": "Conditional Deprecation",
            "steps": [
                "1. Analyze unique API handling logic",
                "2. Extract any valuable error handling patterns", 
                "3. Integrate into main verification system",
                "4. Add deprecation warnings with migration timeline",
                "5. Test verification still works correctly"
            ],
            "timeline": "Immediate - Medium risk",
            "success_criteria": "Verification functionality maintained"
        },
        
        "Phase 3": {
            "components": ["UnifiedSyncProcessor", "ProcessingOptions"],
            "approach": "Careful Evaluation",
            "steps": [
                "1. Assess current usage patterns",
                "2. Identify any remaining unique functionality",
                "3. Create migration path to ProcessingConfig",
                "4. Update imports gradually",
                "5. Add deprecation warnings only after migration ready"
            ],
            "timeline": "Gradual - High risk",
            "success_criteria": "No functionality loss, smooth migration"
        }
    }
    
    for phase, info in plan.items():
        print(f"\n🎯 {phase}")
        print(f"   Components: {', '.join(info['components'])}")
        print(f"   Approach: {info['approach']}")
        print(f"   Timeline: {info['timeline']}")
        print(f"   Success Criteria: {info['success_criteria']}")
        print("   Steps:")
        for step in info['steps']:
            print(f"     {step}")
    
    return plan

def main():
    print("🔍 Phase 2 & 3 Deprecation Analysis")
    print("=" * 70)
    print("Analyzing remaining components for deprecation")
    print("=" * 70)
    
    phase2 = analyze_phase2_components()
    phase3 = analyze_phase3_components()
    usage = check_detailed_usage()
    plan = recommend_phase2_phase3_plan()
    
    print(f"\n" + "=" * 70)
    print("📋 ANALYSIS SUMMARY")
    print("=" * 70)
    print("✅ Phase 2 components analyzed - Enhanced verification classes")
    print("✅ Phase 3 components analyzed - Core processing components")
    print("✅ Detailed usage patterns identified")
    print("✅ Implementation plan created")
    
    print(f"\n🎯 RECOMMENDATIONS:")
    print("• Phase 2: Proceed with careful verification testing")
    print("• Phase 3: Evaluate UnifiedSyncProcessor bypass status")
    print("• ProcessingOptions: Plan gradual migration to ProcessingConfig")
    print("• Test thoroughly at each step")

if __name__ == "__main__":
    main()
