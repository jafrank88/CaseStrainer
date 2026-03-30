"""
CaseStrainer Integration Tests
=============================

These tests verify end-to-end functionality to prevent regression issues.
"""

import requests
import json
import time
import pytest
from typing import Dict, List, Any

# Test data
TEST_PARAGRAPH = """Certified questions are questions of law that this court reviews de novo and in light
of the record certified by the federal court. Lopez Demetrio v. Sakuma Bros. Farms, 183
Wn.2d 649, 655, 355 P.3d 258 (2015). Statutory interpretation is also an issue of law we
review de novo. Spokane County v. Dep't of Fish & Wildlife, 192 Wn.2d 453, 457, 430 P.3d 655 (2018)."""

EXPECTED_RESULTS = {
    "183 Wn.2d 649": "Lopez Demetrio v. Sakuma Bros. Farms",
    "192 Wn.2d 453": "Spokane County v. Dep't of Fish & Wildlife", 
    "355 P.3d 258": "Lopez Demetrio v. Sakuma Bros. Farms",
    "430 P.3d 655": "Spokane County v. Dep't of Fish & Wildlife"
}

EXPECTED_CLUSTERS = [
    {
        "case_name": "Lopez Demetrio v. Sakuma Bros. Farms",
        "size": 2,
        "citations": ["183 Wn.2d 649", "355 P.3d 258"]
    },
    {
        "case_name": "Spokane County v. Dep't of Fish & Wildlife", 
        "size": 2,
        "citations": ["192 Wn.2d 453", "430 P.3d 655"]
    }
]

class TestCaseStrainerIntegration:
    """Integration tests for CaseStrainer API."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment."""
        self.base_url = "https://wolf.law.uw.edu/casestrainer/api"
        self.test_payload = {
            "type": "text",
            "text": TEST_PARAGRAPH
        }
    
    def test_api_health(self):
        """Test that the API is responding."""
        response = requests.get(f"{self.base_url}/health_check", timeout=10)
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_case_name_extraction(self):
        """Test that case names are extracted correctly."""
        response = requests.post(
            f"{self.base_url}/analyze",
            json=self.test_payload,
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check that we have citations
        assert "result" in data
        assert "citations" in data["result"]
        assert len(data["result"]["citations"]) == 4
        
        # Check each citation
        for citation in data["result"]["citations"]:
            citation_text = citation["citation"]
            case_name = citation["extracted_case_name"]
            expected_case = EXPECTED_RESULTS.get(citation_text)
            
            assert expected_case is not None, f"Unexpected citation: {citation_text}"
            assert case_name == expected_case, f"Case name mismatch for {citation_text}: got '{case_name}', expected '{expected_case}'"
            assert case_name != "N/A", f"Case name should not be 'N/A' for {citation_text}"
    
    def test_clustering(self):
        """Test that citations are clustered correctly."""
        response = requests.post(
            f"{self.base_url}/analyze",
            json=self.test_payload,
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check clustering
        assert "clusters" in data["result"]
        clusters = data["result"]["clusters"]
        
        # Should have exactly 2 clusters
        assert len(clusters) == 2, f"Expected 2 clusters, got {len(clusters)}"
        
        # Check each cluster
        for expected_cluster in EXPECTED_CLUSTERS:
            found_cluster = None
            for cluster in clusters:
                if cluster["extracted_case_name"] == expected_cluster["case_name"]:
                    found_cluster = cluster
                    break
            
            assert found_cluster is not None, f"Cluster not found: {expected_cluster['case_name']}"
            assert found_cluster["size"] == expected_cluster["size"], f"Cluster size mismatch for {expected_cluster['case_name']}"
            assert set(found_cluster["citations"]) == set(expected_cluster["citations"]), f"Cluster citations mismatch for {expected_cluster['case_name']}"
    
    def test_no_n_a_values(self):
        """Test that no extracted case names are 'N/A'."""
        response = requests.post(
            f"{self.base_url}/analyze",
            json=self.test_payload,
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check citations
        for citation in data["result"]["citations"]:
            assert citation["extracted_case_name"] != "N/A", f"Citation {citation['citation']} has 'N/A' case name"
        
        # Check clusters
        for cluster in data["result"]["clusters"]:
            assert cluster["extracted_case_name"] != "N/A", f"Cluster has 'N/A' case name"
    
    def test_processing_time(self):
        """Test that processing completes within reasonable time."""
        start_time = time.time()
        response = requests.post(
            f"{self.base_url}/analyze",
            json=self.test_payload,
            timeout=30
        )
        end_time = time.time()
        
        assert response.status_code == 200
        processing_time = end_time - start_time
        
        # Should complete within 30 seconds
        assert processing_time < 30, f"Processing took too long: {processing_time:.2f} seconds"
        
        # Log processing time for monitoring
        print(f"Processing time: {processing_time:.2f} seconds")

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
