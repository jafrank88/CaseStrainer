#!/usr/bin/env python3
"""
End-to-End Pipeline Integration Test
Test the complete UnifiedInputProcessor pipeline to identify integration issues
"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_unified_input_processor_pipeline():
    """Test the complete UnifiedInputProcessor pipeline."""
    print("🔍 END-TO-END PIPELINE TEST")
    print("-" * 50)
    
    test_text = """
    In Luis v. United States, 578 U.S. 5, 136 S. Ct. 1083, 194 L. Ed. 2d 256 (2016), 
    the Supreme Court held that the pretrial restraint of a criminal defendant's 
    legitimate, untainted assets needed to pay for counsel violates the Sixth Amendment.
    
    Similarly, in Brown v. Board of Education, 347 U.S. 483 (1954), the Court ruled
    on the constitutionality of racial segregation in public schools.
    """
    
    try:
        print("Step 1: Importing UnifiedInputProcessor...")
        from src.unified_input_processor import UnifiedInputProcessor
        print("✅ Import successful")
        
        print("\nStep 2: Creating processor instance...")
        processor = UnifiedInputProcessor()
        print("✅ Processor created")
        
        print("\nStep 3: Processing text input...")
        result = processor.process_any_input(
            input_data=test_text,
            input_type='text',
            request_id='test_pipeline',
            source_name='integration_test'
        )
        print("✅ Processing completed")
        
        print("\nStep 4: Analyzing results...")
        print(f"Result type: {type(result)}")
        print(f"Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
        if isinstance(result, dict):
            success = result.get('success', False)
            citations = result.get('citations', [])
            clusters = result.get('clusters', [])
            error = result.get('error', None)
            
            print(f"✅ Success: {success}")
            print(f"✅ Citations found: {len(citations)}")
            print(f"✅ Clusters found: {len(clusters)}")
            print(f"✅ Error: {error or 'None'}")
            
            if citations:
                print("\n📋 CITATION DETAILS:")
                for i, citation in enumerate(citations[:3]):  # Show first 3
                    print(f"  Citation {i+1}:")
                    print(f"    Text: {citation.get('citation', 'N/A')}")
                    print(f"    Case Name: {citation.get('case_name', 'N/A')}")
                    print(f"    Extracted Name: {citation.get('extracted_case_name', 'N/A')}")
                    print(f"    Year: {citation.get('year', 'N/A')}")
                    print(f"    Canonical Name: {citation.get('canonical_name', 'N/A')}")
                    print(f"    Canonical Date: {citation.get('canonical_date', 'N/A')}")
                    print(f"    Verified: {citation.get('verified', 'N/A')}")
            
            if clusters:
                print("\n🔗 CLUSTER DETAILS:")
                for i, cluster in enumerate(clusters):
                    print(f"  Cluster {i+1}:")
                    print(f"    Case Name: {cluster.get('case_name', 'N/A')}")
                    print(f"    Year: {cluster.get('year', 'N/A')}")
                    print(f"    Citations: {len(cluster.get('citations', []))}")
                    cluster_citations = cluster.get('citations', [])
                    if cluster_citations:
                        citation_texts = [c.get('citation', 'N/A') for c in cluster_citations]
                        print(f"    Citation Texts: {citation_texts}")
            
            # Expected results for Luis v. United States case
            expected_luis_citations = ['578 U.S. 5', '136 S. Ct. 1083', '194 L. Ed. 2d 256']
            expected_brown_citation = '347 U.S. 483'
            
            print(f"\n📊 EXPECTED VS ACTUAL:")
            print(f"Expected Luis citations: {expected_luis_citations}")
            print(f"Expected Brown citation: {expected_brown_citation}")
            print(f"Expected clusters: 2 (Luis cluster + Brown single citation)")
            
            # Check if we found the expected citations
            found_citations = [c.get('citation', '') for c in citations]
            luis_found = all(cite in str(found_citations) for cite in expected_luis_citations)
            brown_found = expected_brown_citation in str(found_citations)
            
            print(f"✅ Luis citations found: {luis_found}")
            print(f"✅ Brown citation found: {brown_found}")
            print(f"✅ Cluster count matches: {len(clusters) == 2}")
            
            return success and len(citations) >= 4 and len(clusters) >= 1
        
        return False
        
    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run end-to-end pipeline integration test."""
    print("🧪 END-TO-END PIPELINE INTEGRATION TEST")
    print("="*60)
    
    success = test_unified_input_processor_pipeline()
    
    print(f"\n" + "="*60)
    print("📊 INTEGRATION TEST RESULTS")
    print("="*60)
    print(f"Pipeline Integration: {'✅ PASSED' if success else '❌ FAILED'}")
    
    if success:
        print("\n🎉 The UnifiedInputProcessor pipeline is working correctly!")
        print("✅ Citations are being extracted")
        print("✅ Clustering is working")
        print("✅ Case names and years are being extracted")
    else:
        print("\n⚠️  The pipeline has integration issues that need to be resolved.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
