#!/usr/bin/env python3
"""
Automated test runner for citation clustering.
Starts backend, waits for health, tests API, and can iterate through fixes.
"""

import requests
import json
import time
import subprocess
import sys
import os
from typing import Dict, Any, Optional

def start_backend():
    """Start the backend using dplaunch in production mode."""
    print("🔄 Starting backend...")
    try:
        result = subprocess.run([
            "powershell", "-Command", 
            "./dplaunch.ps1 -Mode Production -QuickStart"
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("✅ Backend started successfully")
            return True
        else:
            print(f"❌ Backend start failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ Backend start timed out")
        return False
    except Exception as e:
        print(f"❌ Backend start error: {e}")
        return False

def wait_for_backend_health(timeout=60):
    """Wait for backend to be healthy."""
    print("⏳ Waiting for backend health...")
    start_time = time.time()
    
    health_urls = [
        "http://localhost:5001/casestrainer/api/health",
        "http://localhost:80/casestrainer/api/health",
        "http://localhost/casestrainer/api/health",
        "https://localhost/casestrainer/api/health"
    ]
    
    while time.time() - start_time < timeout:
        for url in health_urls:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    print(f"✅ Backend healthy at {url}")
                    return url.replace('/health', '')  # Return base URL
            except:
                continue
        
        print("⏳ Backend not ready yet, waiting...")
        time.sleep(5)
    
    print("❌ Backend health check timed out")
    return None

def test_citation_clustering(base_url: str) -> Dict[str, Any]:
    """Test citation clustering with the test paragraph."""
    test_text = '''A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)'''

    payload = {
        "type": "text",
        "text": test_text
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            f"{base_url}/casestrainer/api/analyze", 
            json=payload, 
            headers=headers, 
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ API error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ API request failed: {e}")
        return None

def analyze_clustering_results(data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze the clustering results and return metrics."""
    if not data:
        return {"error": "No data received"}
    
    citations = data.get('citations', [])
    clusters = data.get('clusters', [])
    
    # Count citations with cluster metadata
    citations_with_metadata = 0
    citations_in_clusters = 0
    
    for citation in citations:
        metadata = citation.get('metadata', {})
        if metadata:
            citations_with_metadata += 1
            if metadata.get('is_in_cluster'):
                citations_in_clusters += 1
    
    # Analyze clusters
    cluster_sizes = [len(cluster.get('citations', [])) for cluster in clusters]
    
    analysis = {
        "total_citations": len(citations),
        "total_clusters": len(clusters),
        "citations_with_metadata": citations_with_metadata,
        "citations_in_clusters": citations_in_clusters,
        "cluster_sizes": cluster_sizes,
        "expected_clusters": 3,
        "expected_cluster_size": 2,
        "success": False,
        "issues": []
    }
    
    # Check if we have the expected 3 clusters of 2 cases each
    if len(clusters) == 3:
        if all(size >= 2 for size in cluster_sizes):
            analysis["success"] = True
            analysis["message"] = "✅ Perfect! 3 clusters with 2+ cases each"
        else:
            analysis["issues"].append(f"Clusters too small: {cluster_sizes}")
    else:
        analysis["issues"].append(f"Wrong number of clusters: {len(clusters)} (expected 3)")
    
    if citations_in_clusters == 0:
        analysis["issues"].append("No citations have cluster metadata")
    
    return analysis

def print_analysis(analysis: Dict[str, Any]):
    """Print the analysis results."""
    print("\n" + "="*60)
    print("CLUSTERING ANALYSIS")
    print("="*60)
    print(f"Total citations: {analysis['total_citations']}")
    print(f"Total clusters: {analysis['total_clusters']}")
    print(f"Citations with metadata: {analysis['citations_with_metadata']}")
    print(f"Citations in clusters: {analysis['citations_in_clusters']}")
    print(f"Cluster sizes: {analysis['cluster_sizes']}")
    
    if analysis['success']:
        print(f"\n🎉 {analysis['message']}")
    else:
        print(f"\n❌ Issues found:")
        for issue in analysis['issues']:
            print(f"  - {issue}")

def stop_backend():
    """Stop the backend containers."""
    print("🛑 Stopping backend...")
    try:
        subprocess.run([
            "docker-compose", "-f", "docker-compose.prod.yml", "down"
        ], capture_output=True, text=True, timeout=30)
        print("✅ Backend stopped")
    except Exception as e:
        print(f"⚠️  Backend stop error: {e}")

def main():
    """Main test runner."""
    print("🚀 Starting automated citation clustering test")
    print("="*60)
    
    # Start backend
    if not start_backend():
        print("❌ Failed to start backend")
        return False
    
    # Wait for health
    base_url = wait_for_backend_health()
    if not base_url:
        print("❌ Backend not healthy")
        stop_backend()
        return False
    
    # Test clustering
    print(f"\n🧪 Testing citation clustering at {base_url}")
    data = test_citation_clustering(base_url)
    
    if not data:
        print("❌ Failed to get test data")
        stop_backend()
        return False
    
    # Analyze results
    analysis = analyze_clustering_results(data)
    print_analysis(analysis)
    
    # Save full response for debugging
    with open("test_response.json", "w") as f:
        json.dump(data, f, indent=2)
    print(f"\n📄 Full response saved to test_response.json")
    
    # Stop backend
    stop_backend()
    
    return analysis['success']

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 