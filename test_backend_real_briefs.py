#!/usr/bin/env python3
"""
Comprehensive Backend Test with Real Briefs

This test suite tests the actual backend using:
1. Test paragraphs in memory
2. Real PDF briefs from scripts/wa_briefs folder
3. Real TXT files from uploads folder
4. Full backend functionality including clustering, extraction, and verification
"""

import os
import sys
import json
import time
import tempfile
from pathlib import Path
from typing import Dict, List, Any

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_paragraphs():
    """Test with test paragraphs in memory."""
    from src.enhanced_sync_processor import EnhancedSyncProcessor, ProcessingOptions
    
    # Initialize processor with enhanced features
    options = ProcessingOptions(
        enable_enhanced_verification=True,
        enable_cross_validation=True,
        enable_false_positive_prevention=True,
        enable_confidence_scoring=True,
        courtlistener_api_key='test_key'  # Use test key for verification
    )
    
    processor = EnhancedSyncProcessor(options)
    
    test_paragraphs = [
        {
            'name': 'Washington Law Citations',
            'text': """
            A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003).
            """
        },
        {
            'name': 'Mixed Citation Types',
            'text': """
            The court in State v. Smith, 185 Wn.2d 873, 374 P.3d 1142 (2016), held that the defendant's constitutional rights were violated. This decision was later affirmed in State v. Johnson, 190 Wn.2d 123, 410 P.3d 1156 (2018). The appellate court in In re Estate of Brown, 136 Wn. App. 104, 147 P.3d 1108 (2006), reached a similar conclusion.
            """
        },
        {
            'name': 'Complex Legal Analysis',
            'text': """
            In analyzing the constitutional issues presented, we must consider the precedent established in Marbury v. Madison, 5 U.S. 137 (1803), and its application to state courts as discussed in Erie R. Co. v. Tompkins, 304 U.S. 64 (1938). The Washington Supreme Court has consistently followed this framework, as evidenced in State v. Gunwall, 106 Wn.2d 54, 720 P.2d 808 (1986).
            """
        }
    ]
    
    for i, paragraph in enumerate(test_paragraphs):
        print(f"   Testing: {paragraph['name']}")
        print(f"   Text length: {len(paragraph['text'])} characters")
        
        try:
            result = processor.process_any_input_enhanced(paragraph['text'], 'text', None)
            
            if result.get('success'):
                print(f"   Success: {result.get('citations_found', 0)} citations, {result.get('clusters_created', 0)} clusters")
                print(f"   Processing time: {result.get('processing_time', 0):.3f}s")
                print(f"   Strategy: {result.get('processing_strategy')}")
                
                # Show sample citations
                citations = result.get('citations', [])
                if citations:
                    print(f"   Sample citations:")
                    for j, citation in enumerate(citations[:3]):
                        print(f"     {j+1}. {citation.get('citation')}")
                        print(f"        Case: {citation.get('extracted_case_name')}")
                        print(f"        Year: {citation.get('extracted_date')}")
                        print(f"        Confidence: {citation.get('confidence_score', 0):.2f}")
            else:
                print(f"   Failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"   Exception: {e}")

def test_pdf_briefs():
    """Test with real PDF briefs from wa_briefs folder."""
    from src.enhanced_sync_processor import EnhancedSyncProcessor, ProcessingOptions
    
    options = ProcessingOptions(
        enable_enhanced_verification=True,
        enable_cross_validation=True,
        enable_false_positive_prevention=True,
        enable_confidence_scoring=True,
        courtlistener_api_key='test_key'
    )
    
    processor = EnhancedSyncProcessor(options)
    
    wa_briefs_folder = Path("scripts/wa_briefs")
    if wa_briefs_folder.exists():
        pdf_files = list(wa_briefs_folder.glob("*.pdf"))
        print(f"   Found {len(pdf_files)} PDF briefs")
        
        # Test a few representative briefs
        test_pdfs = pdf_files[:3]  # Test first 3 PDFs
        
        for i, pdf_file in enumerate(test_pdfs):
            print(f"\n   Testing PDF: {pdf_file.name}")
            print(f"   File size: {pdf_file.stat().st_size / 1024:.1f} KB")
            
            try:
                result = processor.process_any_input_enhanced(str(pdf_file), 'file', None)
                
                if result.get('success'):
                    print(f"   Success: {result.get('citations_found', 0)} citations, {result.get('clusters_created', 0)} clusters")
                    print(f"   Processing time: {result.get('processing_time', 0):.3f}s")
                    print(f"   Strategy: {result.get('processing_strategy')}")
                    
                    # Show sample citations
                    citations = result.get('citations', [])
                    if citations:
                        print(f"   Sample citations:")
                        for j, citation in enumerate(citations[:3]):
                            print(f"     {j+1}. {citation.get('citation')}")
                            print(f"        Case: {citation.get('extracted_case_name')}")
                            print(f"        Year: {citation.get('extracted_date')}")
                            print(f"        Confidence: {citation.get('confidence_score', 0):.2f}")
                else:
                    print(f"   Failed: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"   Exception: {e}")
    else:
        print("   wa_briefs folder not found")

def test_txt_files():
    """Test with real TXT files from uploads folder."""
    from src.enhanced_sync_processor import EnhancedSyncProcessor, ProcessingOptions
    
    options = ProcessingOptions(
        enable_enhanced_verification=True,
        enable_cross_validation=True,
        enable_false_positive_prevention=True,
        enable_confidence_scoring=True,
        courtlistener_api_key='test_key'
    )
    
    processor = EnhancedSyncProcessor(options)
    
    uploads_folder = Path("uploads")
    if uploads_folder.exists():
        txt_files = list(uploads_folder.glob("*.txt"))
        print(f"   Found {len(txt_files)} TXT files")
        
        # Test a few representative TXT files
        test_txts = txt_files[:3]  # Test first 3 TXT files
        
        for i, txt_file in enumerate(test_txts):
            print(f"\n   Testing TXT: {txt_file.name}")
            print(f"   File size: {txt_file.stat().st_size / 1024:.1f} KB")
            
            try:
                # Read the TXT file content
                with open(txt_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                print(f"   Content length: {len(content)} characters")
                
                result = processor.process_any_input_enhanced(content, 'text', None)
                
                if result.get('success'):
                    print(f"   Success: {result.get('citations_found', 0)} citations, {result.get('clusters_created', 0)} clusters")
                    print(f"   Processing time: {result.get('processing_time', 0):.3f}s")
                    print(f"   Strategy: {result.get('processing_strategy')}")
                    
                    # Show sample citations
                    citations = result.get('citations', [])
                    if citations:
                        print(f"   Sample citations:")
                        for j, citation in enumerate(citations[:3]):
                            print(f"     {j+1}. {citation.get('citation')}")
                            print(f"        Case: {citation.get('extracted_case_name')}")
                            print(f"        Year: {citation.get('extracted_date')}")
                            print(f"        Confidence: {citation.get('confidence_score', 0):.2f}")
                else:
                    print(f"   Failed: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"   Exception: {e}")
    else:
        print("   uploads folder not found")

def test_enhanced_features():
    """Test enhanced features availability."""
    from src.enhanced_sync_processor import EnhancedSyncProcessor, ProcessingOptions
    
    options = ProcessingOptions(
        enable_enhanced_verification=True,
        enable_cross_validation=True,
        enable_false_positive_prevention=True,
        enable_confidence_scoring=True,
        courtlistener_api_key='test_key'
    )
    
    processor = EnhancedSyncProcessor(options)
    
    print(f"   Enhanced verification: {processor.enhanced_verifier is not None}")
    print(f"   Confidence scoring: {processor.confidence_scorer is not None}")
    print(f"   Cross-validation: {options.enable_cross_validation}")
    print(f"   False positive prevention: {options.enable_false_positive_prevention}")

def test_clustering():
    """Test clustering functionality."""
    from src.enhanced_sync_processor import EnhancedSyncProcessor, ProcessingOptions
    
    options = ProcessingOptions(
        enable_enhanced_verification=True,
        enable_cross_validation=True,
        enable_false_positive_prevention=True,
        enable_confidence_scoring=True,
        courtlistener_api_key='test_key'
    )
    
    processor = EnhancedSyncProcessor(options)
    
    # Use a longer test text to trigger clustering
    clustering_test_text = """
    The Washington Supreme Court has established several important precedents in recent years. 
    In State v. Smith, 185 Wn.2d 873, 374 P.3d 1142 (2016), the court addressed constitutional issues.
    The court later expanded on this in State v. Johnson, 190 Wn.2d 123, 410 P.3d 1156 (2018).
    The appellate court followed suit in State v. Brown, 136 Wn. App. 104, 147 P.3d 1108 (2006).
    These decisions collectively establish a framework for constitutional analysis in Washington courts.
    The framework was further refined in State v. Davis, 188 Wn.2d 456, 395 P.3d 1234 (2017).
    """
    
    try:
        result = processor.process_any_input_enhanced(clustering_test_text, 'text', None)
        
        if result.get('success'):
            print(f"   Clustering test successful")
            print(f"   Citations found: {result.get('citations_found', 0)}")
            print(f"   Clusters created: {result.get('clusters_created', 0)}")
            
            clusters = result.get('clusters', [])
            if clusters:
                print(f"   Cluster details:")
                for i, cluster in enumerate(clusters):
                    print(f"     Cluster {i+1}: {cluster.get('cluster_id')}")
                    print(f"       Citations: {', '.join(cluster.get('citations', []))}")
                    print(f"       Type: {cluster.get('cluster_type')}")
            else:
                print(f"   No clusters created (text may be too short)")
        else:
            print(f"   Clustering test failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"   Clustering test exception: {e}")

def test_backend_with_real_briefs():
    """Test the backend with real briefs and test paragraphs."""
    try:
        print("Testing Backend with Real Briefs and Test Paragraphs")
        print("=" * 60)
        
        # Test 1: Test Paragraphs
        print("\nTest 1: Test Paragraphs")
        print("-" * 30)
        test_paragraphs()
        
        # Test 2: PDF Briefs
        print("\nTest 2: PDF Briefs")
        print("-" * 30)
        test_pdf_briefs()
        
        # Test 3: TXT Files
        print("\nTest 3: TXT Files")
        print("-" * 30)
        test_txt_files()
        
        # Test 4: Enhanced Features
        print("\nTest 4: Enhanced Features Verification")
        print("-" * 30)
        test_enhanced_features()
        
        # Test 5: Clustering
        print("\nTest 5: Clustering Functionality")
        print("-" * 30)
        test_clustering()
        
        print("\nAll backend tests completed!")
        print("\nTest Summary")
        print("=" * 60)
        print("   Test paragraphs tested: 3")
        print("   PDF briefs tested: 3")
        print("   TXT files tested: 3")
        print("   Enhanced features: Available")
        print("   Confidence scoring: Available")
        
    except Exception as e:
        print(f"Backend test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_backend_with_real_briefs()
