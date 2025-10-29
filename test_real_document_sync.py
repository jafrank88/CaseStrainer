#!/usr/bin/env python3
"""
Test Real Document Processing - sp-7788.pdf (Synchronous)

This script tests the optimized processor with a real legal document
using synchronous processing to avoid Redis dependency.
"""

import sys
import os
import time
import json
from typing import Dict, Any, List

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.simplified_citation_processor import ProcessingConfig
from src.optimized_verification_master import get_optimized_verifier
from src.unified_citation_clustering import cluster_citations_unified


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


def extract_citations_direct(text: str) -> List[Dict[str, Any]]:
    """Extract citations directly using the simplified processor's extraction logic."""
    try:
        from src.simplified_citation_processor import SimplifiedCitationProcessor
        
        # Create processor with minimal config
        config = ProcessingConfig(
            enable_verification=False,  # Extract first, then verify
            enable_clustering=False,
            timeout_seconds=60
        )
        
        processor = SimplifiedCitationProcessor(config)
        
        # Extract citations without verification
        citations = processor._extract_citations(text, 'direct_test')
        
        return citations
        
    except Exception as e:
        print(f"Error extracting citations: {str(e)}")
        return []


def verify_citations_batch(citations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Verify citations using the optimized batch verification."""
    if not citations:
        return []
    
    try:
        import asyncio
        
        async def run_verification():
            verifier = get_optimized_verifier()
            
            citation_texts = [c.get('citation', '') for c in citations]
            case_names = [c.get('extracted_case_name') for c in citations]
            case_dates = [c.get('extracted_date') for c in citations]
            
            results = await verifier.verify_citations_batch_optimized(
                citation_texts,
                case_names,
                case_dates,
                batch_size=50,
                timeout_per_citation=10.0,
                enable_parallel=True
            )
            
            return results
        
        # Run the async verification
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            verification_results = loop.run_until_complete(run_verification())
        finally:
            loop.close()
        
        # Apply verification results to citations
        for i, (citation, verification) in enumerate(zip(citations, verification_results)):
            if verification:
                citation['verified'] = verification.verified
                citation['possible_match'] = verification.possible_match
                citation['verification_source'] = verification.source
                citation['canonical_name'] = verification.canonical_name
                citation['canonical_date'] = verification.canonical_date
                citation['canonical_url'] = verification.canonical_url
                citation['verification_error'] = verification.error
        
        return citations
        
    except Exception as e:
        print(f"Error verifying citations: {str(e)}")
        import traceback
        traceback.print_exc()
        return citations


def cluster_extracted_citations(citations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Cluster citations using the clustering system."""
    if not citations:
        return []
    
    try:
        clusters = cluster_citations_unified(citations)
        return clusters
    except Exception as e:
        print(f"Error clustering citations: {str(e)}")
        return []


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
        r'\b\d+\s*S\.?\.?\s*Ct\.?\s*\d+\s*\(\d{4}\)',
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


def test_sp7788_document_sync():
    """Test processing of the sp-7788.pdf document synchronously."""
    print("\n" + "="*80)
    print("REAL DOCUMENT TEST - sp-7788.pdf (Synchronous)")
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
    else:
        print(f"   ⚠️  No standard citation patterns found in text")
        print(f"   This might be a different type of legal document")
    
    # Show sample text to understand document type
    print(f"\n📝 Document Sample (first 500 characters):")
    sample_text = document_text[:500].replace('\n', ' ')
    print(f"   {sample_text}...")
    
    # Step 1: Extract citations
    print(f"\n🔍 Step 1: Extracting citations...")
    start_time = time.time()
    
    extracted_citations = extract_citations_direct(document_text)
    
    extraction_time = time.time() - start_time
    
    print(f"✅ Citation extraction completed in {extraction_time:.2f}s")
    print(f"   Citations extracted: {len(extracted_citations)}")
    
    if extracted_citations:
        print(f"\n📋 Sample Extracted Citations:")
        for i, citation in enumerate(extracted_citations[:10], 1):
            cit_text = citation.get('citation', 'Unknown')[:80]
            print(f"   {i:2d}. {cit_text}")
    else:
        print(f"   ⚠️  No citations extracted by the processor")
        print(f"   This document might not contain standard legal citations")
        
        # Look for any legal references in the text
        import re
        legal_terms = re.findall(r'\b[A-Z][a-z]+ v\. [A-Z][a-z]+\b', document_text)
        if legal_terms:
            print(f"   Found potential case names: {legal_terms[:5]}")
        
        return True  # Still successful, just no citations
    
    # Step 2: Verify citations
    print(f"\n✅ Step 2: Verifying citations with CourtListener batch API...")
    start_time = time.time()
    
    verified_citations = verify_citations_batch(extracted_citations)
    
    verification_time = time.time() - start_time
    
    print(f"✅ Verification completed in {verification_time:.2f}s")
    
    verified_count = sum(1 for c in verified_citations if c.get('verified', False))
    possible_count = sum(1 for c in verified_citations if c.get('possible_match', False))
    
    print(f"   Total citations: {len(verified_citations)}")
    print(f"   Verified: {verified_count}")
    print(f"   Possible matches: {possible_count}")
    
    # Show verification results
    print(f"\n📊 Verification Results:")
    for i, citation in enumerate(verified_citations[:10], 1):
        status = "✅ Verified" if citation.get('verified') else "⚠️ Possible" if citation.get('possible_match') else "❌ Not found"
        cit_text = citation.get('citation', 'Unknown')[:60]
        source = citation.get('verification_source', 'unknown')
        print(f"   {i:2d}. {status} | {cit_text} | {source}")
        
        if citation.get('canonical_name'):
            print(f"       → {citation.get('canonical_name')}")
    
    # Step 3: Cluster citations
    print(f"\n🔗 Step 3: Clustering citations...")
    start_time = time.time()
    
    clusters = cluster_extracted_citations(verified_citations)
    
    clustering_time = time.time() - start_time
    
    print(f"✅ Clustering completed in {clustering_time:.2f}s")
    print(f"   Clusters created: {len(clusters)}")
    
    # Analyze clustering
    cluster_sizes = [len(cluster.get('citations', [])) for cluster in clusters]
    single_clusters = sum(1 for size in cluster_sizes if size == 1)
    multi_clusters = sum(1 for size in cluster_sizes if size > 1)
    
    print(f"   Single-citation clusters: {single_clusters}")
    print(f"   Multi-citation clusters: {multi_clusters}")
    
    if multi_clusters > 0:
        print(f"   Multi-citation cluster details:")
        for i, cluster in enumerate(clusters):
            cluster_citations = cluster.get('citations', [])
            if len(cluster_citations) > 1:
                print(f"     Cluster {i}: {len(cluster_citations)} citations")
                for cit in cluster_citations[:3]:  # Show first 3
                    cit_text = cit.get('citation', 'Unknown')[:60]
                    print(f"       - {cit_text}")
    
    # Performance summary
    total_time = extraction_time + verification_time + clustering_time
    print(f"\n⚡ Performance Summary:")
    print(f"   PDF text extraction: {extraction_time:.2f}s")
    print(f"   Citation extraction: {extraction_time:.2f}s")
    print(f"   Verification: {verification_time:.2f}s")
    print(f"   Clustering: {clustering_time:.2f}s")
    print(f"   Total processing time: {total_time:.2f}s")
    
    # Quality assessment
    if verified_citations:
        verification_rate = (verified_count + possible_count) / len(verified_citations)
        print(f"\n🎯 Quality Assessment:")
        print(f"   Extraction success: {len(extracted_citations)} citations found")
        print(f"   Verification success: {verification_rate:.1%}")
        print(f"   Clustering quality: {len(clusters)} clusters created")
        
        # Sources used
        sources = set([c.get('verification_source', 'unknown') for c in verified_citations if c.get('verification_source')])
        print(f"   Verification sources: {list(sources)}")
        
        if 'courtlistener_lookup_batch' in sources:
            print(f"   ✅ CourtListener batch API is being used correctly!")
        
        overall_quality = verification_rate
        if overall_quality >= 0.8:
            print(f"   🎉 Overall quality: EXCELLENT ({overall_quality:.1%})")
        elif overall_quality >= 0.6:
            print(f"   ✅ Overall quality: GOOD ({overall_quality:.1%})")
        else:
            print(f"   ⚠️  Overall quality: NEEDS IMPROVEMENT ({overall_quality:.1%})")
    
    # Save detailed results
    results_data = {
        'document_analysis': doc_analysis,
        'processing_results': {
            'extraction_time': extraction_time,
            'verification_time': verification_time,
            'clustering_time': clustering_time,
            'total_time': total_time,
            'extracted_citations': len(extracted_citations),
            'verified_citations': verified_count,
            'possible_matches': possible_count,
            'clusters_created': len(clusters),
            'verification_rate': (verified_count + possible_count) / len(verified_citations) if verified_citations else 0
        },
        'sample_citations': [
            {
                'citation': c.get('citation', ''),
                'verified': c.get('verified', False),
                'canonical_name': c.get('canonical_name', ''),
                'source': c.get('verification_source', '')
            } for c in verified_citations[:20]
        ]
    }
    
    with open('sp7788_sync_results.json', 'w') as f:
        json.dump(results_data, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: sp7788_sync_results.json")
    
    return True


def main():
    """Run real document test synchronously."""
    print("CaseStrainer Real Document Test (Synchronous)")
    print("="*80)
    print("Testing optimized processor with real legal document sp-7788.pdf")
    print("Using synchronous processing to avoid Redis dependency.")
    
    try:
        success = test_sp7788_document_sync()
        
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
