#!/usr/bin/env python3
"""
Compare citation extraction for Raines v. Byrd in two contexts:
1. Embedded in complex paragraph with multiple citations
2. Isolated citation text
"""

import requests
import json
import time
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_citation_context(text, description):
    """Test citation extraction for given text."""
    
    print(f"\n🔄 Testing: {description}")
    print("-" * 50)
    print(f"📝 Text length: {len(text)} bytes")
    print(f"📄 Text preview: {text[:100]}...")
    
    try:
        response = requests.post(
            "http://localhost:5000/casestrainer/api/analyze",
            json={"type": "text", "text": text},
            headers={"Content-Type": "application/json"},
            timeout=30,
            verify=False
        )
        
        if response.status_code == 200:
            result = response.json()
            processing_mode = result.get('metadata', {}).get('processing_mode', 'unknown')
            
            print(f"✅ Status: {response.status_code}")
            print(f"📊 Processing mode: {processing_mode}")
            
            # Handle async if needed
            if processing_mode == 'queued':
                task_id = result.get('metadata', {}).get('job_id')
                if task_id:
                    print(f"📋 Waiting for task: {task_id}")
                    
                    for attempt in range(15):
                        time.sleep(2)
                        status_response = requests.get(
                            f"http://localhost:5000/casestrainer/api/task_status/{task_id}",
                            verify=False
                        )
                        
                        if status_response.status_code == 200:
                            status_result = status_response.json()
                            status = status_result.get('status', 'unknown')
                            
                            if status == 'completed':
                                result = status_result
                                break
                            elif status == 'failed':
                                print(f"❌ Failed: {status_result.get('error', 'Unknown')}")
                                return None
                        
                        if attempt == 14:
                            print("❌ Timeout waiting for results")
                            return None
            
            # Extract results
            citations = result.get('result', {}).get('citations', result.get('citations', []))
            clusters = result.get('result', {}).get('clusters', result.get('clusters', []))
            
            print(f"📝 Citations found: {len(citations)}")
            print(f"🔗 Clusters found: {len(clusters)}")
            
            # Look for Raines citations specifically
            raines_citations = []
            for citation in citations:
                citation_text = citation.get('citation', '')
                case_name = citation.get('extracted_case_name', '')
                canonical_name = citation.get('canonical_name', '')
                
                if ('Raines' in citation_text or 'Raines' in case_name or 'Raines' in canonical_name or
                    '521 U.S. 811' in citation_text):
                    raines_citations.append(citation)
            
            print(f"🎯 Raines-related citations: {len(raines_citations)}")
            
            if raines_citations:
                print("📋 Raines citations found:")
                for i, citation in enumerate(raines_citations):
                    citation_text = citation.get('citation', '')
                    case_name = citation.get('extracted_case_name', '')
                    canonical_name = citation.get('canonical_name', '')
                    verified = citation.get('verified', False) or citation.get('is_verified', False)
                    method = citation.get('method', 'unknown')
                    confidence = citation.get('confidence', 0)
                    
                    status_icon = "✅" if verified else "❌"
                    print(f"  {i+1}. {status_icon} {citation_text}")
                    print(f"     📖 Case name: {case_name}")
                    if canonical_name:
                        print(f"     🏛️  Canonical: {canonical_name}")
                    print(f"     🔧 Method: {method}, Confidence: {confidence}")
            
            # Look for Raines clusters
            raines_clusters = []
            for cluster in clusters:
                case_name = cluster.get('case_name', '')
                canonical_name = cluster.get('canonical_name', '')
                
                if 'Raines' in case_name or 'Raines' in canonical_name:
                    raines_clusters.append(cluster)
            
            print(f"🔗 Raines-related clusters: {len(raines_clusters)}")
            
            if raines_clusters:
                print("📋 Raines clusters found:")
                for i, cluster in enumerate(raines_clusters):
                    case_name = cluster.get('case_name', '')
                    canonical_name = cluster.get('canonical_name', '')
                    size = cluster.get('size', 0)
                    verified = cluster.get('verified', False)
                    cluster_citations = cluster.get('citations', [])
                    
                    status_icon = "✅" if verified else "❌"
                    print(f"  {i+1}. {status_icon} {case_name} ({size} citations)")
                    if canonical_name:
                        print(f"     🏛️  Canonical: {canonical_name}")
                    print(f"     📄 Citations in cluster: {cluster_citations}")
            
            return {
                'citations': citations,
                'clusters': clusters,
                'raines_citations': raines_citations,
                'raines_clusters': raines_clusters
            }
            
        else:
            print(f"❌ Request failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

def main():
    """Compare Raines citation extraction in different contexts."""
    
    print("🧪 RAINES v. BYRD CITATION COMPARISON")
    print("=" * 60)
    
    # Test 1: Complex paragraph with multiple citations
    complex_text = '''3 It also silently decides a major constitutional question: can a legislatively created statute grant a plaintiff the right to sue even though that plaintiff has suffered no harm or threat of harm and even thought that plaintiff falls outside the class of people whom the statute was designed to protect? The United States Supreme Court says no, under federal law: "Injury in fact is a constitutional requirement, and '[i]t is settled that Congress cannot erase Article III's standing requirements by statutorily granting the right to sue to a plaintiff who would not otherwise have standing.'" Spokeo, Inc. v. Robins, 578 U.S. 330, 339, 136 S. Ct. 1540, 194 L. Ed. 2d 635 (2016) (alteration in original) (quoting Raines v. Byrd, 521 U.S. 811, 820 n.3, 117 S. Ct. 2312, 138 L. Ed. 2d 849 (1997)). Washington courts suggest that the answer is no, under Washington law: "Generally, one must be protected by the provision of a statute to gain standing to sue for a violation of the provision." McFarland v. Tompkins, 34 Wn. App. 2d 280, 301, 567 P.3d 1128 (2025). We typically interpret statutes to avoid any question about their constitutionality. Utter ex rel. State v. Bldg. Indus. Ass'n of Wash., 182 Wn.2d 398, 434, 341 P.3d 953 (2015) (citing State v. Robinson, 153 Wn.2d 689, 693-94, 107 P.3d 90 (2005)). The majority,'''
    
    # Test 2: Isolated citation
    isolated_text = '''Raines v. Byrd, 521 U.S. 811, 820 n.3, 117 S. Ct. 2312, 138 L. Ed. 2d 849 (1997)'''
    
    # Run tests
    result1 = test_citation_context(complex_text, "Complex paragraph with multiple citations")
    result2 = test_citation_context(isolated_text, "Isolated Raines citation")
    
    # Compare results
    print("\n" + "=" * 60)
    print("🔍 COMPARISON ANALYSIS")
    print("=" * 60)
    
    if result1 and result2:
        print(f"📊 Complex text: {len(result1['citations'])} total citations, {len(result1['raines_citations'])} Raines")
        print(f"📊 Isolated text: {len(result2['citations'])} total citations, {len(result2['raines_citations'])} Raines")
        
        print(f"🔗 Complex text: {len(result1['clusters'])} total clusters, {len(result1['raines_clusters'])} Raines")
        print(f"🔗 Isolated text: {len(result2['clusters'])} total clusters, {len(result2['raines_clusters'])} Raines")
        
        # Detailed comparison of Raines citations
        print("\n📋 DETAILED RAINES CITATION COMPARISON:")
        
        print("\n🔸 Complex text Raines citations:")
        for i, citation in enumerate(result1['raines_citations']):
            print(f"  {i+1}. {citation.get('citation', '')}")
            print(f"     Method: {citation.get('method', 'unknown')}")
            print(f"     Confidence: {citation.get('confidence', 0)}")
            print(f"     Case name: {citation.get('extracted_case_name', '')}")
        
        print("\n🔸 Isolated text Raines citations:")
        for i, citation in enumerate(result2['raines_citations']):
            print(f"  {i+1}. {citation.get('citation', '')}")
            print(f"     Method: {citation.get('method', 'unknown')}")
            print(f"     Confidence: {citation.get('confidence', 0)}")
            print(f"     Case name: {citation.get('extracted_case_name', '')}")
        
        # Analysis
        print("\n🎯 ANALYSIS:")
        if len(result1['raines_citations']) != len(result2['raines_citations']):
            print("⚠️  Different number of Raines citations found!")
            print("   This suggests context affects citation extraction")
        else:
            print("✅ Same number of Raines citations found in both contexts")
        
        if len(result1['raines_clusters']) != len(result2['raines_clusters']):
            print("⚠️  Different number of Raines clusters found!")
            print("   This suggests context affects clustering")
        else:
            print("✅ Same number of Raines clusters found in both contexts")
    
    else:
        print("❌ Could not complete comparison due to processing errors")

if __name__ == "__main__":
    main()
