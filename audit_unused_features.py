#!/usr/bin/env python3
"""
Audit unused/deprecated functions and identify missing features in the main pipeline
"""

import sys
from pathlib import Path
import re

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

def analyze_deprecated_functions():
    """Analyze deprecated functions and their features."""
    print("🔍 AUDIT: Deprecated Functions and Missing Features")
    print("=" * 70)
    
    deprecated_analysis = {
        "Citation Normalization": {
            "deprecated": [
                "_normalize_citation (multiple versions)",
                "_normalize_citation_for_verification", 
                "_normalize_to_bluebook_format",
                "EnhancedCitationNormalizer.normalize_citation"
            ],
            "current": "_normalize_citation_comprehensive",
            "status": "✅ CONSOLIDATED - All functionality moved to comprehensive method"
        },
        
        "Citation Extraction": {
            "deprecated": [
                "_extract_with_regex",
                "UnifiedExtractionService",
                "extract_case_name_and_date (old versions)"
            ],
            "current": "_extract_citations_unified, extract_case_name_and_date_master",
            "status": "✅ CONSOLIDATED - Using unified extraction methods"
        },
        
        "Citation Clustering": {
            "deprecated": [
                "group_citations_into_clusters",
                "_propagate_best_extracted_to_clusters",
                "_detect_parallel_citations",
                "extract_case_clusters_by_name_and_year"
            ],
            "current": "cluster_citations_unified, UnifiedCitationClusterer",
            "status": "✅ CONSOLIDATED - Using unified clustering system"
        },
        
        "Verification": {
            "deprecated": [
                "verify_with_courtlistener (old)",
                "verify_citations_with_canonical_service",
                "verify_citations_with_legal_websearch",
                "CitationVerifier.verify_citations"
            ],
            "current": "cluster_citations_unified with enable_verification=True",
            "status": "✅ CONSOLIDATED - Using unified verification in clustering"
        },
        
        "Web Search": {
            "deprecated": [
                "search_vlex (blocked by site)"
            ],
            "current": "search_google_scholar, search_bing, search_duckduckgo",
            "status": "✅ REPLACED - Using reliable search engines"
        }
    }
    
    for category, info in deprecated_analysis.items():
        print(f"\n📋 {category}")
        print("-" * 40)
        print(f"Deprecated: {', '.join(info['deprecated'])}")
        print(f"Current: {info['current']}")
        print(f"Status: {info['status']}")
    
    return deprecated_analysis

def analyze_enhanced_processors():
    """Analyze what features the enhanced processors have that might be missing."""
    print(f"\n🔍 AUDIT: Enhanced Processor Features")
    print("=" * 50)
    
    enhanced_features = {
        "EnhancedSyncProcessor": {
            "unique_features": [
                "Progress callbacks for real-time updates",
                "Confidence scoring with thresholds",
                "False positive prevention filters",
                "Cross-validation confidence boost",
                "Adaptive processing thresholds",
                "Local clustering with size limits",
                "Enhanced case name extraction with master function",
                "Standalone page number detection",
                "Volume-without-reporter detection"
            ],
            "status": "🤔 POTENTIALLY USEFUL - Some features might enhance main pipeline"
        },
        
        "EnhancedCourtListenerVerifier": {
            "unique_features": [
                "Enhanced API error handling",
                "Rate limiting and retry logic",
                "Batch verification optimization",
                "Confidence scoring for verification results"
            ],
            "status": "🤔 POTENTIALLY USEFUL - Better verification reliability"
        },
        
        "EnhancedCitationClusterer": {
            "unique_features": [
                "Proximity-based parallel detection",
                "Advanced case name similarity matching",
                "Configurable clustering thresholds",
                "Debug mode with detailed logging"
            ],
            "status": "✅ ALREADY INTEGRATED - Features in unified clustering"
        }
    }
    
    for processor, info in enhanced_features.items():
        print(f"\n📋 {processor}")
        print("-" * 30)
        for feature in info['unique_features']:
            print(f"  • {feature}")
        print(f"Status: {info['status']}")
    
    return enhanced_features

def identify_missing_features():
    """Identify features that should be added to the main pipeline."""
    print(f"\n🎯 MISSING FEATURES ANALYSIS")
    print("=" * 50)
    
    missing_features = {
        "High Priority": [
            {
                "feature": "Progress Callbacks",
                "description": "Real-time progress updates for long-running operations",
                "current_status": "❌ Missing from UnifiedCitationProcessorV2",
                "benefit": "Better user experience, especially for large documents",
                "implementation": "Add progress_callback parameter to process_text()"
            },
            {
                "feature": "False Positive Prevention",
                "description": "Filter standalone page numbers and volume-only citations",
                "current_status": "❌ Missing systematic filtering",
                "benefit": "Cleaner results, fewer false positives",
                "implementation": "Add _filter_false_positive_citations() to main pipeline"
            },
            {
                "feature": "Confidence Scoring",
                "description": "Assign confidence scores to extracted citations",
                "current_status": "❌ Missing from main pipeline",
                "benefit": "Users can assess citation reliability",
                "implementation": "Add confidence calculation to citation extraction"
            }
        ],
        
        "Medium Priority": [
            {
                "feature": "Adaptive Processing Thresholds",
                "description": "Dynamic thresholds based on content type and size",
                "current_status": "❌ Fixed thresholds only",
                "benefit": "Better performance optimization",
                "implementation": "Add adaptive threshold logic"
            },
            {
                "feature": "Enhanced Error Recovery",
                "description": "Multiple fallback extraction methods",
                "current_status": "⚠️ Basic fallback only",
                "benefit": "More robust extraction",
                "implementation": "Add layered fallback system"
            }
        ],
        
        "Low Priority": [
            {
                "feature": "Cross-validation Confidence Boost",
                "description": "Boost confidence when multiple methods agree",
                "current_status": "❌ Missing",
                "benefit": "More accurate confidence scores",
                "implementation": "Add cross-validation logic"
            }
        ]
    }
    
    for priority, features in missing_features.items():
        print(f"\n🔥 {priority}")
        print("-" * 30)
        for feature in features:
            print(f"📌 {feature['feature']}")
            print(f"   Description: {feature['description']}")
            print(f"   Status: {feature['current_status']}")
            print(f"   Benefit: {feature['benefit']}")
            print(f"   Implementation: {feature['implementation']}")
            print()
    
    return missing_features

def recommend_integration_plan():
    """Recommend how to integrate missing features."""
    print(f"\n📋 INTEGRATION RECOMMENDATIONS")
    print("=" * 50)
    
    recommendations = [
        {
            "phase": "Phase 1: Core Improvements",
            "features": ["Progress Callbacks", "False Positive Prevention"],
            "effort": "Medium",
            "impact": "High",
            "description": "Add essential features that improve user experience and result quality"
        },
        {
            "phase": "Phase 2: Quality Enhancements", 
            "features": ["Confidence Scoring", "Enhanced Error Recovery"],
            "effort": "Medium",
            "impact": "Medium",
            "description": "Add features that improve citation quality assessment and reliability"
        },
        {
            "phase": "Phase 3: Optimization",
            "features": ["Adaptive Thresholds", "Cross-validation Boost"],
            "effort": "Low",
            "impact": "Low",
            "description": "Fine-tuning features for optimal performance"
        }
    ]
    
    for rec in recommendations:
        print(f"\n🎯 {rec['phase']}")
        print(f"   Features: {', '.join(rec['features'])}")
        print(f"   Effort: {rec['effort']} | Impact: {rec['impact']}")
        print(f"   Description: {rec['description']}")
    
    print(f"\n💡 IMPLEMENTATION STRATEGY:")
    print("1. Extract useful functions from EnhancedSyncProcessor")
    print("2. Integrate them into UnifiedCitationProcessorV2")
    print("3. Add configuration options to enable/disable features")
    print("4. Test thoroughly to ensure no regressions")
    print("5. Deprecate redundant enhanced processors")

def main():
    print("🔍 CaseStrainer Feature Audit")
    print("=" * 70)
    print("Analyzing deprecated functions and identifying missing features")
    print("=" * 70)
    
    deprecated = analyze_deprecated_functions()
    enhanced = analyze_enhanced_processors()
    missing = identify_missing_features()
    recommend_integration_plan()
    
    print(f"\n" + "=" * 70)
    print("📋 SUMMARY")
    print("=" * 70)
    print("✅ Most deprecated functions have been properly consolidated")
    print("✅ Core functionality is unified in main pipeline")
    print("🎯 Key missing features identified for integration:")
    print("   • Progress callbacks for better UX")
    print("   • False positive prevention for cleaner results")
    print("   • Confidence scoring for result assessment")
    print("🔧 Enhanced processors contain valuable features worth extracting")
    print("📈 Integration would significantly improve the main pipeline")
    
    print(f"\n🎯 NEXT STEPS:")
    print("1. Implement Phase 1 features (Progress + False Positive Prevention)")
    print("2. Test integration thoroughly")
    print("3. Consider Phase 2 features based on user feedback")

if __name__ == "__main__":
    main()
