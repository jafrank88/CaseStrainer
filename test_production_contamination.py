#!/usr/bin/env python3

import requests
import json

def test_production_contamination():
    """Test contamination fixes in production environment."""
    
    print("🧪 PRODUCTION CONTAMINATION TEST")
    print("=" * 60)
    
    # Test case with known extracted case name
    test_text = '''Lopez Demetrio v. Sakuma Bros. Farms, 183 Wn.2d 649, 655, 355 P.3d 258 (2015).'''
    
    print(f"📝 Test text: {test_text}")
    print()
    
    url = "http://localhost:5000/casestrainer/api/analyze"
    data = {"text": test_text, "type": "text"}
    
    try:
        response = requests.post(url, data=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('citations', [])
            
            print(f"✅ Found {len(citations)} citations")
            print()
            
            contamination_detected = False
            
            for i, citation in enumerate(citations, 1):
                citation_text = citation.get('citation', '')
                extracted_case_name = citation.get('extracted_case_name', 'N/A')
                canonical_name = citation.get('canonical_name', 'N/A')
                cluster_case_name = citation.get('cluster_case_name', 'N/A')
                
                print(f"📋 Citation {i}: {citation_text}")
                print(f"   🔍 extracted_case_name: '{extracted_case_name}'")
                print(f"   🔍 canonical_name: '{canonical_name}'")
                print(f"   🔍 cluster_case_name: '{cluster_case_name}'")
                
                # Check for contamination patterns
                if canonical_name != 'N/A' and canonical_name is not None:
                    if extracted_case_name == canonical_name and extracted_case_name != 'Lopez Demetrio v. Sakuma Bros. Farms':
                        print(f"   🚨 POTENTIAL CONTAMINATION: extracted matches canonical but not expected")
                        contamination_detected = True
                    elif extracted_case_name == 'N/A' and canonical_name != 'N/A':
                        print(f"   🚨 EXTRACTION FAILURE: No extracted name but canonical available")
                        contamination_detected = True
                    else:
                        print(f"   ✅ DATA SEPARATION: Extracted and canonical properly separated")
                else:
                    if extracted_case_name and extracted_case_name != 'N/A':
                        print(f"   ✅ EXTRACTION WORKING: Found extracted name without canonical contamination")
                    else:
                        print(f"   ⚠️  NO EXTRACTION: Neither extracted nor canonical name available")
                
                print()
            
            # Check clustering
            clusters = result.get('clusters', [])
            print(f"🔗 Found {len(clusters)} clusters")
            
            if clusters:
                for i, cluster in enumerate(clusters, 1):
                    cluster_extracted = cluster.get('extracted_case_name', 'N/A')
                    cluster_canonical = cluster.get('canonical_name', 'N/A')
                    print(f"   Cluster {i}: extracted='{cluster_extracted}', canonical='{cluster_canonical}'")
            
            print()
            if not contamination_detected:
                print("🎉 SUCCESS: No contamination detected!")
                print("✅ Data separation is working correctly")
            else:
                print("❌ FAILURE: Contamination issues detected")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_production_contamination()
