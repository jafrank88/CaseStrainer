#!/usr/bin/env python3
"""
Test the structural clustering with a simple case to verify it's working.
"""

import requests
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_simple_structural():
    """Test with a simple structural pattern."""
    
    # Simple test case that should clearly show structural clustering
    simple_text = "The court in Smith v. Jones, 123 U.S. 456, 78 S. Ct. 901 (1999) held that..."
    
    print("🧪 TESTING SIMPLE STRUCTURAL CLUSTERING")
    print("=" * 60)
    print(f"📝 Text: {simple_text}")
    print()
    
    response = requests.post(
        "http://localhost:5000/casestrainer/api/analyze",
        json={"type": "text", "text": simple_text},
        headers={"Content-Type": "application/json"},
        timeout=30,
        verify=False
    )
    
    if response.status_code == 200:
        result = response.json()
        citations = result.get('citations', [])
        clusters = result.get('clusters', [])
        
        print(f"✅ Status: {response.status_code}")
        print(f"📝 Citations found: {len(citations)}")
        print(f"🔗 Clusters found: {len(clusters)}")
        
        print("\n📋 Citations:")
        for i, cite in enumerate(citations):
            citation_text = cite.get('citation', '')
            case_name = cite.get('extracted_case_name', '')
            canonical = cite.get('canonical_name', '')
            
            print(f"  {i+1}. {citation_text}")
            print(f"     📖 Case: {case_name}")
            if canonical:
                print(f"     🏛️  Canonical: {canonical}")
        
        print("\n🔗 Clusters:")
        for i, cluster in enumerate(clusters):
            case_name = cluster.get('case_name', '')
            size = cluster.get('size', 0)
            cluster_citations = cluster.get('citations', [])
            
            print(f"  {i+1}. {case_name} ({size} citations)")
            print(f"     📄 Citations: {cluster_citations}")
        
        # Check if structural clustering worked
        if len(clusters) == 1 and len(citations) == 2:
            cluster = clusters[0]
            if 'Smith v. Jones' in cluster.get('case_name', ''):
                print("\n✅ SUCCESS: Structural clustering appears to be working!")
                return True
        
        print("\n⚠️  Structural clustering may not be working as expected")
        return False
    else:
        print(f"❌ Request failed: {response.status_code}")
        return False

def test_complex_structural():
    """Test with the complex Spokeo/Raines case."""
    
    complex_text = 'The Supreme Court held in Spokeo, Inc. v. Robins, 578 U.S. 330 (2016) (quoting Raines v. Byrd, 521 U.S. 811, 820 n.3, 117 S. Ct. 2312, 138 L. Ed. 2d 849 (1997)) that standing requirements cannot be erased.'
    
    print("\n🧪 TESTING COMPLEX STRUCTURAL CLUSTERING")
    print("=" * 60)
    print(f"📝 Text: {complex_text}")
    print()
    
    response = requests.post(
        "http://localhost:5000/casestrainer/api/analyze",
        json={"type": "text", "text": complex_text},
        headers={"Content-Type": "application/json"},
        timeout=30,
        verify=False
    )
    
    if response.status_code == 200:
        result = response.json()
        citations = result.get('citations', [])
        clusters = result.get('clusters', [])
        
        print(f"✅ Status: {response.status_code}")
        print(f"📝 Citations found: {len(citations)}")
        print(f"🔗 Clusters found: {len(clusters)}")
        
        print("\n📋 Citations:")
        for i, cite in enumerate(citations):
            citation_text = cite.get('citation', '')
            case_name = cite.get('extracted_case_name', '')
            canonical = cite.get('canonical_name', '')
            
            print(f"  {i+1}. {citation_text}")
            print(f"     📖 Case: {case_name}")
            if canonical:
                print(f"     🏛️  Canonical: {canonical}")
        
        print("\n🔗 Clusters:")
        for i, cluster in enumerate(clusters):
            case_name = cluster.get('case_name', '')
            size = cluster.get('size', 0)
            cluster_citations = cluster.get('citations', [])
            
            print(f"  {i+1}. {case_name} ({size} citations)")
            print(f"     📄 Citations: {cluster_citations}")
        
        # Expected results
        print("\n🎯 EXPECTED RESULTS:")
        print("   Cluster 1: Spokeo, Inc. v. Robins (1 citation: 578 U.S. 330)")
        print("   Cluster 2: Raines v. Byrd (3 citations: 521 U.S. 811, 117 S. Ct. 2312, 138 L. Ed. 2d 849)")
        
        # Check results
        spokeo_cluster = None
        raines_cluster = None
        
        for cluster in clusters:
            case_name = cluster.get('case_name', '')
            if 'Spokeo' in case_name or 'Robins' in case_name:
                spokeo_cluster = cluster
            elif 'Raines' in case_name or 'Byrd' in case_name:
                raines_cluster = cluster
        
        success = True
        if spokeo_cluster:
            spokeo_citations = spokeo_cluster.get('citations', [])
            if '578 U.S. 330' not in spokeo_citations:
                print("❌ FAIL: 578 U.S. 330 not in Spokeo cluster")
                success = False
            else:
                print("✅ PASS: 578 U.S. 330 correctly in Spokeo cluster")
        else:
            print("❌ FAIL: No Spokeo cluster found")
            success = False
        
        if raines_cluster:
            raines_citations = raines_cluster.get('citations', [])
            expected_raines = ['521 U.S. 811', '117 S. Ct. 2312', '138 L. Ed. 2d 849']
            missing = [cite for cite in expected_raines if cite not in raines_citations]
            if missing:
                print(f"❌ FAIL: Missing from Raines cluster: {missing}")
                success = False
            else:
                print("✅ PASS: All Raines citations correctly clustered")
        else:
            print("❌ FAIL: No Raines cluster found")
            success = False
        
        return success
    else:
        print(f"❌ Request failed: {response.status_code}")
        return False

if __name__ == "__main__":
    print("🔍 STRUCTURAL CLUSTERING VALIDATION")
    print("=" * 60)
    
    simple_success = test_simple_structural()
    complex_success = test_complex_structural()
    
    print("\n" + "=" * 60)
    print("📊 FINAL RESULTS:")
    print(f"   Simple test: {'✅ PASS' if simple_success else '❌ FAIL'}")
    print(f"   Complex test: {'✅ PASS' if complex_success else '❌ FAIL'}")
    
    if simple_success and complex_success:
        print("\n🎉 SUCCESS: Structural clustering is working correctly!")
    else:
        print("\n⚠️  ISSUES: Structural clustering needs further debugging")
