#!/usr/bin/env python3
"""
Test clustering speed without verification to identify bottleneck
"""

import os
import sys
import time
import tempfile
import requests
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_clustering_without_verification():
    """Test clustering speed without verification"""
    print("=" * 80)
    print("TESTING CLUSTERING SPEED WITHOUT VERIFICATION")
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
        
        # Test 1: Extract citations only (no verification)
        print("\n" + "-" * 60)
        print("TEST 1: CITATION EXTRACTION ONLY")
        print("-" * 60)
        
        try:
            import asyncio
            from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
            from src.models import ProcessingConfig
            
            # Create config with verification disabled
            config = ProcessingConfig()
            config.enable_verification = False
            print(f"[CONFIG] Verification enabled: {config.enable_verification}")
            
            processor = UnifiedCitationProcessorV2(config=config)
            
            start = time.time()
            result = asyncio.run(processor.process_text(text))
            elapsed = time.time() - start
            print(f"[EXTRACTION] Completed in {elapsed:.2f}s")
            print(f"[RESULT] Citations: {len(result.get('citations', []))}")
            print(f"[RESULT] Clusters: {len(result.get('clusters', []))}")
            
        except Exception as e:
            print(f"[ERROR] Extraction failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Test 2: Extract citations WITH verification
        print("\n" + "-" * 60)
        print("TEST 2: CITATION EXTRACTION WITH VERIFICATION")
        print("-" * 60)
        
        try:
            # Create config with verification enabled
            config = ProcessingConfig()
            config.enable_verification = True
            print(f"[CONFIG] Verification enabled: {config.enable_verification}")
            
            processor = UnifiedCitationProcessorV2(config=config)
            
            start = time.time()
            result = asyncio.run(processor.process_text(text))
            elapsed = time.time() - start
            print(f"[EXTRACTION] Completed in {elapsed:.2f}s")
            print(f"[RESULT] Citations: {len(result.get('citations', []))}")
            print(f"[RESULT] Clusters: {len(result.get('clusters', []))}")
            
        except Exception as e:
            print(f"[ERROR] Extraction failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Test 3: Test clustering directly
        print("\n" + "-" * 60)
        print("TEST 3: CLUSTERING ONLY (NO VERIFICATION)")
        print("-" * 60)
        
        try:
            from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
            processor = UnifiedCitationProcessorV2()
            
            # Extract citations first
            result = asyncio.run(processor.process_text(text))
            citations = result.get('citations', [])
            
            print(f"[INFO] Testing clustering on {len(citations)} citations")
            
            # Test optimized clustering
            from src.unified_clustering_master_optimized import OptimizedClusteringMaster
            clusterer = OptimizedClusteringMaster()
            
            start = time.time()
            clusters = clusterer.cluster_citations(citations, text)
            elapsed = time.time() - start
            print(f"[OPTIMIZED CLUSTERING] Completed in {elapsed:.2f}s")
            print(f"[RESULT] Created {len(clusters)} clusters")
            
        except Exception as e:
            print(f"[ERROR] Clustering failed: {e}")
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
    test_clustering_without_verification()
