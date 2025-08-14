#!/usr/bin/env python3
"""
Step-by-step Citation Extraction Test
Test each component of the pipeline individually to identify issues
"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_step_1_eyecite_extraction():
    """Step 1: Test basic eyecite citation extraction."""
    print("\n🔍 STEP 1: EYECITE EXTRACTION")
    print("-" * 40)
    
    test_text = "In Luis v. United States, 578 U.S. 5, 136 S. Ct. 1083, 194 L. Ed. 2d 256 (2016)"
    
    try:
        import eyecite
        from eyecite import get_citations
        
        citations = get_citations(test_text)
        print(f"Found {len(citations)} citations:")
        for i, citation in enumerate(citations):
            print(f"  {i+1}. {citation} (type: {type(citation).__name__})")
        
        return citations
        
    except Exception as e:
        print(f"❌ Eyecite extraction failed: {e}")
        return []

def test_step_2_citation_normalization():
    """Step 2: Test citation normalization."""
    print("\n🔍 STEP 2: CITATION NORMALIZATION")
    print("-" * 40)
    
    raw_citations = ["578 U.S. 5", "136 S. Ct. 1083", "194 L. Ed. 2d 256"]
    
    try:
        from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
        
        processor = UnifiedCitationProcessorV2()
        normalized = []
        for citation in raw_citations:
            norm = processor._normalize_citation_comprehensive(citation, purpose="general")
            print(f"  {citation} → {norm}")
            normalized.append(norm)
        
        return normalized
        
    except Exception as e:
        print(f"❌ Citation normalization failed: {e}")
        import traceback
        traceback.print_exc()
        return []

class SimpleCitation:
    """Simple citation object for testing."""
    def __init__(self, citation, case_name=None, year=None):
        self.citation = citation
        self.case_name = case_name
        self.extracted_case_name = case_name
        self.year = year
        self.extracted_date = year
        self.canonical_name = None
        self.canonical_date = None
        self.verified = False
        self.court = None
        self.confidence = 0.0
        self.method = 'test'
        self.pattern = None
        self.context = ''
        self.start_index = 0
        self.end_index = 0
        self.is_parallel = False
        self.metadata = {}
        self.parallel_citations = []

def test_step_3_clustering():
    """Step 3: Test citation clustering."""
    print("\n🔍 STEP 3: CITATION CLUSTERING")
    print("-" * 40)
    
    # Create test citation objects with proper structure
    test_citations = [
        SimpleCitation('578 U.S. 5', 'Luis v. United States', '2016'),
        SimpleCitation('136 S. Ct. 1083', 'Luis v. United States', '2016'),
        SimpleCitation('194 L. Ed. 2d 256', 'Luis v. United States', '2016')
    ]
    
    try:
        from src.unified_citation_clustering import UnifiedCitationClusterer
        
        clusterer = UnifiedCitationClusterer()
        clusters = clusterer.cluster_citations(test_citations)
        
        print(f"Found {len(clusters)} clusters:")
        for i, cluster in enumerate(clusters):
            print(f"  Cluster {i+1}: {len(cluster.get('citations', []))} citations")
            print(f"    Name: {cluster.get('case_name', 'N/A')}")
            print(f"    Year: {cluster.get('year', 'N/A')}")
            print(f"    Citations: {[c.citation for c in cluster.get('citations', [])]}")
        
        return clusters
        
    except Exception as e:
        print(f"❌ Citation clustering failed: {e}")
        import traceback
        traceback.print_exc()
        return []

def test_step_4_name_year_extraction():
    """Step 4: Test case name and year extraction."""
    print("\n🔍 STEP 4: NAME & YEAR EXTRACTION")
    print("-" * 40)
    
    test_text = "In Luis v. United States, 578 U.S. 5, 136 S. Ct. 1083, 194 L. Ed. 2d 256 (2016)"
    
    try:
        from src.unified_case_name_extractor import extract_case_name_and_date_unified
        
        result = extract_case_name_and_date_unified(test_text)
        print(f"Extraction result: {result}")
        
        if isinstance(result, dict):
            print(f"  Case name: {result.get('case_name', 'N/A')}")
            print(f"  Year: {result.get('year', 'N/A')}")
        
        return result
        
    except Exception as e:
        print(f"❌ Name/year extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return {}

def test_step_5_courtlistener_verification():
    """Step 5: Test CourtListener verification."""
    print("\n🔍 STEP 5: COURTLISTENER VERIFICATION")
    print("-" * 40)
    
    try:
        from src.config import get_config_value
        from src.courtlistener_verification import verify_with_courtlistener
        
        api_key = get_config_value("COURTLISTENER_API_KEY", "")
        if not api_key:
            print("⚠️  No API key, skipping verification test")
            return True
        
        test_citation = "578 U.S. 5"
        test_case_name = "Luis v. United States"
        
        print(f"Verifying: {test_citation} ({test_case_name})")
        result = verify_with_courtlistener(api_key, test_citation, extracted_case_name=test_case_name)
        
        print(f"Verification result: {result}")
        return result and result.get('verified', False)
        
    except Exception as e:
        print(f"❌ CourtListener verification failed: {e}")
        return False

def main():
    """Run step-by-step extraction tests."""
    print("🧪 STEP-BY-STEP CITATION EXTRACTION TEST")
    print("="*60)
    
    # Run each step
    step1_citations = test_step_1_eyecite_extraction()
    step2_normalized = test_step_2_citation_normalization()
    step3_clusters = test_step_3_clustering()
    step4_names_years = test_step_4_name_year_extraction()
    step5_verification = test_step_5_courtlistener_verification()
    
    print(f"\n" + "="*60)
    print("📊 STEP-BY-STEP RESULTS")
    print("="*60)
    print(f"Step 1 - Eyecite Extraction: {'✅ PASSED' if step1_citations else '❌ FAILED'}")
    print(f"Step 2 - Normalization: {'✅ PASSED' if step2_normalized else '❌ FAILED'}")
    print(f"Step 3 - Clustering: {'✅ PASSED' if step3_clusters else '❌ FAILED'}")
    print(f"Step 4 - Name/Year Extraction: {'✅ PASSED' if step4_names_years else '❌ FAILED'}")
    print(f"Step 5 - CourtListener Verification: {'✅ PASSED' if step5_verification else '❌ FAILED'}")
    
    all_passed = all([step1_citations, step2_normalized, step3_clusters, step4_names_years, step5_verification])
    print(f"\nOverall: {'✅ ALL STEPS PASSED' if all_passed else '❌ SOME STEPS FAILED'}")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
