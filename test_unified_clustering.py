#!/usr/bin/env python3
"""
Test the UnifiedCitationClusterer for parallel citation detection.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from unified_citation_clustering import UnifiedCitationClusterer

def test_washington_parallel_detection():
    """Test Washington State parallel citation detection."""
    print("🧪 Testing UnifiedCitationClusterer for Washington parallel citations")
    
    # Initialize the clusterer
    clusterer = UnifiedCitationClusterer(config={'debug_mode': True})
    
    # Test citations from our standard test
    test_citations = [
        '200 Wn.2d 72',
        '514 P.3d 643',  # Should be parallel to 200 Wn.2d 72
        '171 Wn.2d 486',
        '256 P.3d 321',  # Should be parallel to 171 Wn.2d 486
        '146 Wn.2d 1',
        '43 P.3d 4'      # Should be parallel to 146 Wn.2d 1
    ]
    
    print(f"\n📋 Test citations: {test_citations}")
    
    # Test reporter type extraction
    print("\n🔍 Testing reporter type extraction:")
    for citation in test_citations:
        reporter_type = clusterer._extract_reporter_type(citation)
        print(f"  {citation} -> {reporter_type}")
    
    # Test Washington parallel pattern detection
    print("\n🔗 Testing Washington parallel pattern detection:")
    
    # Test the expected parallel pairs
    parallel_pairs = [
        ('200 Wn.2d 72', '514 P.3d 643'),  # Same case: Convoyant, LLC v. DeepThink, LLC
        ('171 Wn.2d 486', '256 P.3d 321'), # Same case: Carlson v. Glob. Client Sols., LLC
        ('146 Wn.2d 1', '43 P.3d 4')       # Same case: Dep't of Ecology v. Campbell & Gwinn, LLC
    ]
    
    for citation1, citation2 in parallel_pairs:
        is_parallel = clusterer._check_washington_parallel_patterns(citation1, citation2, "")
        print(f"  {citation1} + {citation2} -> Parallel: {is_parallel}")
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    test_washington_parallel_detection()
