#!/usr/bin/env python3
"""
Test the optimized clustering implementation
"""

import os
import sys
import time
import tempfile
import requests
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_optimized_clustering():
    """Test optimized clustering performance"""
    print("=" * 80)
    print("TESTING OPTIMIZED CLUSTERING")
    print("=" * 80)
    
    # First, extract citations from the test PDF
    url = "https://www.courts.wa.gov/opinions/pdf/1031351.pdf"
    
    # Download PDF
    temp_file = download_pdf(url)
    if not temp_file:
        print("[ERROR] Failed to download PDF")
        return
        
    print(f"[INFO] PDF downloaded to: {temp_file}")
    
    try:
        # Extract text
        from src.robust_pdf_extractor import extract_pdf_text_robust
        start = time.time()
        text, library = extract_pdf_text_robust(temp_file, max_pages=10, verbose=False)
        elapsed = time.time() - start
        print(f"[SUCCESS] Extracted {len(text):,} chars in {elapsed:.2f}s using {library}")
        
        # Extract citations
        import asyncio
        from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
        processor = UnifiedCitationProcessorV2()
        
        start = time.time()
        citations = asyncio.run(processor.process_text(text))
        elapsed = time.time() - start
        print(f"[SUCCESS] Found {len(citations)} citations in {elapsed:.2f}s")
        
        # Test ORIGINAL clustering
        print("\n" + "-" * 60)
        print("TEST 1: ORIGINAL CLUSTERING")
        print("-" * 60)
        
        try:
            from src.unified_clustering_master import UnifiedClusteringMaster
            original_clusterer = UnifiedClusteringMaster(config={'debug_mode': False})
            
            start = time.time()
            original_clusters = original_clusterer.cluster_citations(citations, text)
            elapsed = time.time() - start
            print(f"[ORIGINAL] Created {len(original_clusters)} clusters in {elapsed:.2f}s")
        except Exception as e:
            print(f"[ORIGINAL] Failed: {e}")
            original_clusters = []
        
        # Test OPTIMIZED clustering
        print("\n" + "-" * 60)
        print("TEST 2: OPTIMIZED CLUSTERING")
        print("-" * 60)
        
        try:
            from src.unified_clustering_master_optimized import OptimizedClusteringMaster
            optimized_clusterer = OptimizedClusteringMaster()
            
            start = time.time()
            optimized_clusters = optimized_clusterer.cluster_citations(citations, text)
            elapsed = time.time() - start
            print(f"[OPTIMIZED] Created {len(optimized_clusters)} clusters in {elapsed:.2f}s")
            
            # Compare results
            print("\n" + "-" * 60)
            print("COMPARISON")
            print("-" * 60)
            
            if original_clusters and optimized_clusters:
                print(f"[INFO] Original clusters: {len(original_clusters)}")
                print(f"[INFO] Optimized clusters: {len(optimized_clusters)}")
                
                # Show cluster sizes
                orig_sizes = [c.get('cluster_size', 0) for c in original_clusters]
                opt_sizes = [c.get('cluster_size', 0) for c in optimized_clusters]
                
                print(f"[INFO] Original cluster sizes: {orig_sizes[:10]}...")
                print(f"[INFO] Optimized cluster sizes: {opt_sizes[:10]}...")
                
                # Check if parallel citations were detected
                orig_parallel = sum(1 for c in original_clusters if c.get('cluster_size', 0) > 1)
                opt_parallel = sum(1 for c in optimized_clusters if c.get('cluster_size', 0) > 1)
                
                print(f"[INFO] Original parallel groups: {orig_parallel}")
                print(f"[INFO] Optimized parallel groups: {opt_parallel}")
                
                if orig_parallel == opt_parallel:
                    print("[SUCCESS] Parallel detection matches!")
                else:
                    print("[WARNING] Parallel detection differs")
            
        except Exception as e:
            print(f"[OPTIMIZED] Failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Test with the actual processor
        print("\n" + "-" * 60)
        print("TEST 3: FULL PROCESSOR WITH OPTIMIZED CLUSTERING")
        print("-" * 60)
        
        try:
            start = time.time()
            result = asyncio.run(processor.process_text(text))
            elapsed = time.time() - start
            print(f"[SUCCESS] Full processor completed in {elapsed:.2f}s")
            print(f"[RESULT] Citations: {len(result.get('citations', []))}")
            print(f"[RESULT] Clusters: {len(result.get('clusters', []))}")
        except Exception as e:
            print(f"[ERROR] Full processor failed: {e}")
            import traceback
            traceback.print_exc()
        
    finally:
        # Cleanup
        try:
            os.unlink(temp_file)
        except:
            pass

def download_pdf(url: str) -> str:
    """Download PDF to temporary file"""
    try:
        print("[DOWNLOAD] Downloading PDF...")
        response = requests.get(url, timeout=30, stream=True)
        response.raise_for_status()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
            return f.name
    except Exception as e:
        print(f"[ERROR] Download failed: {e}")
        return None

if __name__ == "__main__":
    test_optimized_clustering()
