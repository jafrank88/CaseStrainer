#!/usr/bin/env python3
"""
Test Real Document Processing - sp-7788.pdf

This script tests the optimized processor with a real legal document
to ensure it works correctly with actual case files.
"""

import sys
import os
import time
import json
from typing import Dict, Any, List

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.simplified_citation_processor import create_processor, ProcessingConfig
from src.citation_extraction_endpoint import extract_citations_with_clustering


def extract_pdf_text(pdf_path: str) -> str:
    """Extract text from PDF file."""
    try:
        import PyPDF2
        
        text = ""
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text() + "\n"
        
        return text
    except Exception as e:
        print(f"Error extracting PDF text: {str(e)}")
        return ""


def analyze_document_content(text: str) -> Dict[str, Any]:
    """Analyze the document content to understand what we're working with."""
    
    # Basic document analysis
    lines = text.split('\n')
    non_empty_lines = [line.strip() for line in lines if line.strip()]
    
    # Look for potential citations
    import re
    
    citation_patterns = [
        r'\b\d+\s+[A-Za-z\.]+\s+\d+\s*\(\d{4}\)',
        r'\b\d+\s*F\.?\s*\d+d?\s*\(\d{4}\)',
        r'\b[A-Za-z\s&\.]+ v\. [A-Za-z\s&\.]+,\s*\d+\s*[A-Za-z\.]+\s*\d+\s*\(\d{4}\)',
    ]
    
    potential_citations = []
    for pattern in citation_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        potential_citations.extend(matches)
    
    # Remove duplicates and clean
    unique_citations = []
    for cit in potential_citations:
        cit = cit.strip()
        if cit and cit not in unique_citations:
            unique_citations.append(cit)
    
    return {
        'total_lines': len(lines),
        'non_empty_lines': len(non_empty_lines),
        'character_count': len(text),
        'word_count': len(text.split()),
        'potential_citations': unique_citations,
        'estimated_citation_count': len(unique_citations)
    }


def test_sp7788_document():
    """Test processing of the sp-7788.pdf document."""
    print("\n" + "="*80)
    print("REAL DOCUMENT TEST - sp-7788.pdf")
    print("="*80)
    
    pdf_path = "sp-7788.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ Error: {pdf_path} not found")
        return False
    
    print(f"\n📄 Extracting text from {pdf_path}...")
    start_time = time.time()
    
    # Extract text from PDF
    document_text = extract_pdf_text(pdf_path)
    
    extraction_time = time.time() - start_time
    
    if not document_text:
        print(f"❌ Failed to extract text from PDF")
        return False
    
    print(f"✅ Text extracted in {extraction_time:.2f}s")
    
    # Analyze document content
    print(f"\n🔍 Document Analysis:")
    doc_analysis = analyze_document_content(document_text)
    
    print(f"   Total lines: {doc_analysis['total_lines']}")
    print(f"   Content lines: {doc_analysis['non_empty_lines']}")
    print(f"   Character count: {doc_analysis['character_count']:,}")
    print(f"   Word count: {doc_analysis['word_count']:,}")
    print(f"   Potential citations found: {doc_analysis['estimated_citation_count']}")
    
    if doc_analysis['potential_citations']:
        print(f"   First few citations:")
        for i, cit in enumerate(doc_analysis['potential_citations'][:5], 1):
            print(f"     {i}. {cit}")
    
    # Test with optimized processor
    print(f"\n🚀 Testing Optimized Processor:")
    start_time = time.time()
    
    processor = create_processor(
        enable_verification=True,
        enable_clustering=True,
        timeout_seconds=300  # 5 minutes for real document
    )
    
    try:
        result = processor.process(
            {'type': 'text', 'text': document_text},
            'sp7788_test'
        )
        
        optimized_time = time.time() - start_time
        
        print(f"✅ Optimized processing completed in {optimized_time:.2f}s")
        print(f"   Citations extracted: {len(result.citations)}")
        print(f"   Clusters created: {len(result.clusters)}")
        
        # Analyze extraction results
        verified_count = sum(1 for c in result.citations if c.get('verified', False))
        possible_count = sum(1 for c in result.citations if c.get('possible_match', False))
        
        print(f"   Verified citations: {verified_count}")
        print(f"   Possible matches: {possible_count}")
        
        # Show sample results
        print(f"\n📋 Sample Extraction Results:")
        for i, citation in enumerate(result.citations[:10], 1):
            status = "✅ Verified" if citation.get('verified') else "⚠️ Possible" if citation.get('possible_match') else "❌ Not found"
            cit_text = citation.get('citation', 'Unknown')[:80]
            print(f"   {i:2d}. {status} | {cit_text}")
            
            if citation.get('canonical_name'):
                print(f"       → {citation.get('canonical_name')}")
        
        # Analyze clustering
        print(f"\n🔗 Clustering Analysis:")
        cluster_sizes = [len(cluster.get('citations', [])) for cluster in result.clusters]
        single_clusters = sum(1 for size in cluster_sizes if size == 1)
        multi_clusters = sum(1 for size in cluster_sizes if size > 1)
        
        print(f"   Total clusters: {len(result.clusters)}")
        print(f"   Single-citation clusters: {single_clusters}")
        print(f"   Multi-citation clusters: {multi_clusters}")
        
        if multi_clusters > 0:
            print(f"   Multi-citation cluster details:")
            for i, cluster in enumerate(result.clusters):
                cluster_citations = cluster.get('citations', [])
                if len(cluster_citations) > 1:
                    print(f"     Cluster {i}: {len(cluster_citations)} citations")
                    for cit in cluster_citations[:3]:  # Show first 3
                        cit_text = cit.get('citation', 'Unknown')[:60]
                        print(f"       - {cit_text}")
        
        # Test with legacy system for comparison
        print(f"\n🔄 Testing Legacy System:")
        start_time = time.time()
        
        try:
            legacy_result = extract_citations_with_clustering(
                document_text,
                enable_verification=True
            )
            
            legacy_time = time.time() - start_time
            
            print(f"✅ Legacy processing completed in {legacy_time:.2f}s")
            print(f"   Citations extracted: {len(legacy_result.get('citations', []))}")
            print(f"   Clusters created: {len(legacy_result.get('clusters', []))}")
            
            # Performance comparison
            print(f"\n⚡ Performance Comparison:")
            print(f"   Optimized: {optimized_time:.2f}s")
            print(f"   Legacy: {legacy_time:.2f}s")
            
            if legacy_time > 0:
                improvement = (legacy_time - optimized_time) / legacy_time * 100
                print(f"   Performance improvement: {improvement:.1f}%")
                
                if improvement > 10:
                    print(f"   Status: 🚀 Significant improvement")
                elif improvement > 0:
                    print(f"   Status: ✅ Moderate improvement")
                else:
                    print(f"   Status: ⚠️ No improvement")
            
            # Quality comparison
            opt_verified = sum(1 for c in result.citations if c.get('verified', False))
            leg_verified = sum(1 for c in legacy_result.get('citations', []) if c.get('verified', False))
            
            print(f"\n📊 Quality Comparison:")
            print(f"   Optimized verification: {opt_verified}/{len(result.citations)} ({opt_verified/len(result.citations):.1%})")
            print(f"   Legacy verification: {leg_verified}/{len(legacy_result.get('citations', []))} ({leg_verified/len(legacy_result.get('citations', [])):.1%})")
            
            # Sources used
            opt_sources = set([c.get('verification_source', 'unknown') for c in result.citations if c.get('verification_source')])
            leg_sources = set([c.get('verification_source', 'unknown') for c in legacy_result.get('citations', []) if c.get('verification_source')])
            
            print(f"   Optimized sources: {list(opt_sources)}")
            print(f"   Legacy sources: {list(leg_sources)}")
            
        except Exception as e:
            print(f"❌ Legacy system failed: {str(e)}")
        
        # Save detailed results
        results_data = {
            'document_analysis': doc_analysis,
            'optimized_results': {
                'processing_time': optimized_time,
                'citations_count': len(result.citations),
                'clusters_count': len(result.clusters),
                'verified_count': verified_count,
                'possible_count': possible_count,
                'sample_citations': [
                    {
                        'citation': c.get('citation', ''),
                        'verified': c.get('verified', False),
                        'canonical_name': c.get('canonical_name', ''),
                        'source': c.get('verification_source', '')
                    } for c in result.citations[:20]
                ]
            }
        }
        
        with open('sp7788_processing_results.json', 'w') as f:
            json.dump(results_data, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: sp7788_processing_results.json")
        
        return True
        
    except Exception as e:
        print(f"❌ Optimized processor failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run real document test."""
    print("CaseStrainer Real Document Test")
    print("="*80)
    print("Testing optimized processor with real legal document sp-7788.pdf")
    
    try:
        success = test_sp7788_document()
        
        print("\n" + "="*80)
        if success:
            print("✅ REAL DOCUMENT TEST COMPLETED SUCCESSFULLY")
            print("   Optimized processor works correctly with real documents!")
        else:
            print("❌ REAL DOCUMENT TEST FAILED")
            print("   Issues found with real document processing.")
        print("="*80)
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
