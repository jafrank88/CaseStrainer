#!/usr/bin/env python3
"""
Test Washington parallel citation clustering fix
"""

def test_washington_parallel_clustering():
    """Test that Washington parallel citations with different volumes/pages are clustered correctly"""
    
    from src.unified_clustering_master import UnifiedClusteringMaster
    
    # Create clustering master
    clustering = UnifiedClusteringMaster()
    
    # Test citations - these are parallel citations for the same case
    citation1 = "520 P.3d 470"
    citation2 = "24 Wn. App. 2d 377"
    
    print("Testing Washington parallel citation clustering...")
    print(f"Citation 1: {citation1}")
    print(f"Citation 2: {citation2}")
    print()
    
    # Test the parallel pattern matching
    result = clustering._check_washington_parallel_patterns(citation1, citation2)
    
    print(f"Result: {'✅ MATCHED' if result else '❌ NOT MATCHED'}")
    print()
    
    if result:
        print("Success! Washington parallel citations are correctly recognized.")
        print("Note: Volume/page numbers are different (520 vs 24, 470 vs 377)")
        print("which is normal for Washington state parallel citations.")
    else:
        print("Failed! Washington parallel citations should be matched.")
        print("Washington reporter and Pacific Reporter use different numbering systems.")
    
    return result

if __name__ == "__main__":
    success = test_washington_parallel_clustering()
    exit(0 if success else 1)
