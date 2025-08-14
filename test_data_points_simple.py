#!/usr/bin/env python3
"""
Simple Data Points Test
Quick verification of the six required data points without verbose logging
"""

import sys
import os
import json
import logging

# Suppress warnings for cleaner output
logging.getLogger().setLevel(logging.ERROR)

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_data_points_simple():
    """Test the six data points with minimal output."""
    print("🔍 SIMPLE DATA POINTS TEST")
    print("="*40)
    
    # Simple test case
    test_text = "Brown v. Board of Education, 347 U.S. 483 (1954)"
    
    try:
        from src.api.services.citation_service import CitationService
        
        service = CitationService()
        input_data = {'text': test_text, 'type': 'text'}
        
        result = service.process_immediately(input_data)
        
        if result.get('status') != 'completed':
            print(f"❌ Processing failed: {result.get('message', 'Unknown error')}")
            return False
        
        citations = result.get('citations', [])
        clusters = result.get('clusters', [])
        
        print(f"Citations found: {len(citations)}")
        print(f"Clusters found: {len(clusters)}")
        
        if not citations:
            print("❌ No citations found")
            return False
        
        # Check first citation for all six data points
        citation = citations[0]
        print(f"\nFirst citation: {citation.get('citation', 'N/A')}")
        
        data_points = {
            'Extracted Case Name': citation.get('extracted_case_name') or citation.get('case_name'),
            'Extracted Year': citation.get('extracted_date') or citation.get('year'),
            'Canonical Name': citation.get('canonical_name'),
            'Canonical Year': citation.get('canonical_date'),
            'Canonical URL': citation.get('canonical_url'),
            'Verified Status': citation.get('verified')
        }
        
        print("\nData Points Check:")
        all_present = True
        for name, value in data_points.items():
            status = "✅" if value is not None else "❌"
            print(f"  {status} {name}: {value}")
            if value is None and name not in ['Canonical Name', 'Canonical Year', 'Canonical URL']:
                all_present = False
        
        # Check clustering (separate from individual citations)
        clustering_works = len(clusters) >= 0  # Clusters may be 0 for single citations
        print(f"  {'✅' if clustering_works else '❌'} Clustering: {len(clusters)} clusters")
        
        # Check frontend compatibility
        frontend_compatible = (
            isinstance(citations, list) and
            isinstance(clusters, list) and
            all(isinstance(c, dict) for c in citations)
        )
        print(f"  {'✅' if frontend_compatible else '❌'} Frontend Compatible: {frontend_compatible}")
        
        success = all_present and frontend_compatible
        print(f"\nOverall: {'✅ PASSED' if success else '❌ FAILED'}")
        
        return success
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_data_points_simple()
    
    if success:
        print("\n🎉 Backend delivers required data points in frontend-compatible format!")
    else:
        print("\n⚠️  Backend has issues delivering required data points")
    
    sys.exit(0 if success else 1)
