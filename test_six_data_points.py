#!/usr/bin/env python3
"""
Six Data Points Test
Verify that the backend consistently delivers all six required data points:
1. Extracted case name
2. Extracted case year  
3. Clustering
4. Canonical URL
5. Canonical name
6. Canonical year
"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_six_data_points():
    """Test that all six data points are delivered consistently."""
    print("🔍 SIX DATA POINTS COMPREHENSIVE TEST")
    print("="*60)
    
    # Test with Luis v. United States (should have parallel citations for clustering)
    test_text = """
    In Luis v. United States, 578 U.S. 5, 136 S. Ct. 1083, 194 L. Ed. 2d 256 (2016), 
    the Supreme Court held that the pretrial restraint of a criminal defendant's 
    legitimate, untainted assets needed to pay for counsel violates the Sixth Amendment.
    
    Similarly, in Brown v. Board of Education, 347 U.S. 483 (1954), the Court ruled
    on the constitutionality of racial segregation in public schools.
    """
    
    try:
        print("Step 1: Testing CitationService (frontend-facing API)...")
        from src.api.services.citation_service import CitationService
        
        service = CitationService()
        input_data = {'text': test_text, 'type': 'text'}
        
        print(f"Processing text: {test_text[:100]}...")
        result = service.process_immediately(input_data)
        
        print(f"Result status: {result.get('status')}")
        print(f"Result message: {result.get('message')}")
        
        if result.get('status') != 'completed':
            print(f"❌ Processing failed: {result}")
            return False
        
        citations = result.get('citations', [])
        clusters = result.get('clusters', [])
        
        print(f"\n📊 OVERALL RESULTS:")
        print(f"Citations found: {len(citations)}")
        print(f"Clusters found: {len(clusters)}")
        
        if not citations:
            print("❌ No citations found - test failed")
            return False
        
        print(f"\n📋 DETAILED CITATION ANALYSIS:")
        print("-" * 50)
        
        all_data_points_present = True
        
        for i, citation in enumerate(citations):
            print(f"\nCitation {i+1}: {citation.get('citation', 'N/A')}")
            
            # Check all six data points
            data_points = {
                '1. Extracted Case Name': citation.get('extracted_case_name') or citation.get('case_name'),
                '2. Extracted Case Year': citation.get('extracted_date') or citation.get('year'),
                '3. Clustering': 'Will check clusters separately',
                '4. Canonical URL': citation.get('canonical_url'),
                '5. Canonical Name': citation.get('canonical_name'),
                '6. Canonical Year': citation.get('canonical_date')
            }
            
            for point_name, value in data_points.items():
                status = "✅" if value else "❌"
                if point_name == '3. Clustering':
                    print(f"  {status} {point_name}: {value}")
                else:
                    print(f"  {status} {point_name}: {value}")
                    if not value and point_name != '3. Clustering':
                        all_data_points_present = False
        
        print(f"\n🔗 CLUSTERING ANALYSIS:")
        print("-" * 30)
        
        if clusters:
            for i, cluster in enumerate(clusters):
                print(f"\nCluster {i+1}:")
                print(f"  Case Name: {cluster.get('case_name', 'N/A')}")
                print(f"  Year: {cluster.get('year', 'N/A')}")
                print(f"  Citations Count: {len(cluster.get('citations', []))}")
                cluster_citations = cluster.get('citations', [])
                if cluster_citations:
                    citation_texts = []
                    for c in cluster_citations:
                        if isinstance(c, dict):
                            citation_texts.append(c.get('citation', 'N/A'))
                        else:
                            citation_texts.append(str(c))
                    print(f"  Citation Texts: {citation_texts}")
        else:
            print("❌ No clusters found")
            all_data_points_present = False
        
        print(f"\n📈 FRONTEND COMPATIBILITY CHECK:")
        print("-" * 40)
        
        # Check if the data structure is frontend-compatible
        frontend_compatible = True
        
        # Check citations structure
        if not isinstance(citations, list):
            print("❌ Citations is not a list")
            frontend_compatible = False
        else:
            print(f"✅ Citations is a list with {len(citations)} items")
        
        # Check clusters structure  
        if not isinstance(clusters, list):
            print("❌ Clusters is not a list")
            frontend_compatible = False
        else:
            print(f"✅ Clusters is a list with {len(clusters)} items")
        
        # Check citation objects have required fields
        required_fields = ['citation', 'case_name', 'extracted_case_name', 'canonical_name', 
                          'extracted_date', 'canonical_date', 'verified']
        
        for i, citation in enumerate(citations[:2]):  # Check first 2
            missing_fields = []
            for field in required_fields:
                if field not in citation:
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"❌ Citation {i+1} missing fields: {missing_fields}")
                frontend_compatible = False
            else:
                print(f"✅ Citation {i+1} has all required fields")
        
        print(f"\n🎯 FINAL ASSESSMENT:")
        print("="*50)
        print(f"All 6 data points present: {'✅ YES' if all_data_points_present else '❌ NO'}")
        print(f"Frontend compatible format: {'✅ YES' if frontend_compatible else '❌ NO'}")
        print(f"Citations extracted: {'✅ YES' if citations else '❌ NO'}")
        print(f"Clustering working: {'✅ YES' if clusters else '❌ NO'}")
        
        overall_success = all_data_points_present and frontend_compatible and citations and clusters
        print(f"\nOverall Success: {'✅ PASSED' if overall_success else '❌ FAILED'}")
        
        return overall_success
        
    except Exception as e:
        print(f"❌ Six data points test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run six data points test."""
    print("🧪 SIX DATA POINTS COMPREHENSIVE TEST")
    print("="*70)
    
    success = test_six_data_points()
    
    if success:
        print("\n🎉 SUCCESS: Backend delivers all 6 data points consistently!")
        print("✅ Extracted case name and year")
        print("✅ Clustering functionality")  
        print("✅ Canonical URL, name, and year")
        print("✅ Frontend-compatible format")
    else:
        print("\n⚠️  ISSUES: Backend does not deliver all 6 data points consistently")
        print("❌ Some data points are missing or incorrectly formatted")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
