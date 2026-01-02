#!/usr/bin/env python3
"""
Compare file upload, URL, and text processing for the same PDF document.
This helps identify differences in processing pipelines.
"""

import sys
import os
import json
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup logging
logging.basicConfig(
    level=logging.WARNING,  # Reduce noise
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_file_upload(file_path: str):
    """Test file upload processing."""
    logger.info(f"\n{'='*80}")
    logger.info("TESTING FILE UPLOAD PROCESSING")
    logger.info(f"{'='*80}")
    
    try:
        from src.unified_input_processor import UnifiedInputProcessor
        from werkzeug.datastructures import FileStorage
        
        # Create a FileStorage-like object
        with open(file_path, 'rb') as f:
            from io import BytesIO
            file_storage = FileStorage(
                stream=BytesIO(f.read()),
                filename=os.path.basename(file_path),
                name='file'
            )
        
        processor = UnifiedInputProcessor()
        request_id = "test_file_upload"
        
        result = processor.process_any_input(
            file_storage, 'file', request_id, 'test', enable_verification=True, force_mode='sync'
        )
        
        print(f"File Upload: {len(result.get('citations', []))} citations, {len(result.get('clusters', []))} clusters")
        
        citations = result.get('citations', [])
        clusters = result.get('clusters', [])
        
        logger.info(f"\nFILE UPLOAD RESULTS:")
        logger.info(f"  Citations found: {len(citations)}")
        logger.info(f"  Clusters found: {len(clusters)}")
        
        # Count unique case names
        unique_names = set()
        for cit in citations:
            name = cit.get('extracted_case_name') or cit.get('canonical_name')
            if name and name != 'N/A':
                unique_names.add(name)
        
        # Get citation texts
        citation_texts = {cit.get('citation') for cit in citations if cit.get('citation')}
        
        return {
            'method': 'file_upload',
            'citations_count': len(citations),
            'clusters_count': len(clusters),
            'unique_names_count': len(unique_names),
            'citation_texts': citation_texts,
            'citations': citations[:10]  # First 10 for comparison
        }
        
    except Exception as e:
        logger.error(f"File upload processing failed: {e}", exc_info=True)
        return {'method': 'file_upload', 'error': str(e)}


def test_url_processing(url: str):
    """Test URL processing."""
    logger.info(f"\n{'='*80}")
    logger.info("TESTING URL PROCESSING")
    logger.info(f"{'='*80}")
    
    try:
        from src.unified_input_processor import UnifiedInputProcessor
        
        processor = UnifiedInputProcessor()
        request_id = "test_url_processing"
        
        result = processor.process_any_input(
            url, 'url', request_id, 'test', enable_verification=True, force_mode='sync'
        )
        
        print(f"URL: {len(result.get('citations', []))} citations, {len(result.get('clusters', []))} clusters")
        
        citations = result.get('citations', [])
        clusters = result.get('clusters', [])
        
        logger.info(f"\nURL PROCESSING RESULTS:")
        logger.info(f"  Citations found: {len(citations)}")
        logger.info(f"  Clusters found: {len(clusters)}")
        
        # Count unique case names
        unique_names = set()
        for cit in citations:
            name = cit.get('extracted_case_name') or cit.get('canonical_name')
            if name and name != 'N/A':
                unique_names.add(name)
        
        # Get citation texts
        citation_texts = {cit.get('citation') for cit in citations if cit.get('citation')}
        
        return {
            'method': 'url',
            'citations_count': len(citations),
            'clusters_count': len(clusters),
            'unique_names_count': len(unique_names),
            'citation_texts': citation_texts,
            'citations': citations[:10]  # First 10 for comparison
        }
        
    except Exception as e:
        logger.error(f"URL processing failed: {e}", exc_info=True)
        return {'method': 'url', 'error': str(e)}


def test_text_processing(file_path: str):
    """Test text processing by extracting text first, then processing as text."""
    logger.info(f"\n{'='*80}")
    logger.info("TESTING TEXT PROCESSING")
    logger.info(f"{'='*80}")
    
    try:
        from src.unified_input_processor import UnifiedInputProcessor
        from src.unified_text_extractor import extract_text_from_file_unified
        
        # First extract text from PDF
        text, method = extract_text_from_file_unified(file_path, verbose=True)
        logger.info(f"Extracted {len(text):,} characters using {method}")
        
        if not text or len(text.strip()) < 10:
            return {'method': 'text', 'error': 'Failed to extract text from PDF'}
        
        processor = UnifiedInputProcessor()
        request_id = "test_text_processing"
        
        result = processor.process_any_input(
            text, 'text', request_id, 'test', enable_verification=True, force_mode='sync'
        )
        
        print(f"Text: {len(result.get('citations', []))} citations, {len(result.get('clusters', []))} clusters")
        
        citations = result.get('citations', [])
        clusters = result.get('clusters', [])
        
        logger.info(f"\nTEXT PROCESSING RESULTS:")
        logger.info(f"  Citations found: {len(citations)}")
        logger.info(f"  Clusters found: {len(clusters)}")
        
        # Count unique case names
        unique_names = set()
        for cit in citations:
            name = cit.get('extracted_case_name') or cit.get('canonical_name')
            if name and name != 'N/A':
                unique_names.add(name)
        
        # Get citation texts
        citation_texts = {cit.get('citation') for cit in citations if cit.get('citation')}
        
        return {
            'method': 'text',
            'citations_count': len(citations),
            'clusters_count': len(clusters),
            'unique_names_count': len(unique_names),
            'citation_texts': citation_texts,
            'text_length': len(text),
            'citations': citations[:10]  # First 10 for comparison
        }
        
    except Exception as e:
        logger.error(f"Text processing failed: {e}", exc_info=True)
        return {'method': 'text', 'error': str(e)}


def compare_results(file_result: dict, url_result: dict, text_result: dict):
    """Compare results from all three methods."""
    print(f"\n{'='*80}")
    print("COMPARISON SUMMARY - ALL THREE METHODS")
    print(f"{'='*80}")
    
    if 'error' in file_result:
        print(f"❌ File upload failed: {file_result['error']}")
        return
    
    if 'error' in url_result:
        print(f"❌ URL processing failed: {url_result['error']}")
        return
    
    if 'error' in text_result:
        print(f"❌ Text processing failed: {text_result['error']}")
        return
    
    print(f"\n{'Metric':<30} {'File Upload':<15} {'URL':<15} {'Text':<15} {'Notes':<20}")
    print(f"{'-'*95}")
    
    metrics = [
        ('Citations', 'citations_count'),
        ('Clusters', 'clusters_count'),
        ('Unique Names', 'unique_names_count'),
    ]
    
    for label, key in metrics:
        file_val = file_result.get(key, 0)
        url_val = url_result.get(key, 0)
        text_val = text_result.get(key, 0)
        
        # Determine if all match
        if file_val == url_val == text_val:
            notes = "[OK] All match"
        elif file_val == url_val:
            notes = f"[WARN] File=URL, Text differs by {text_val - file_val:+d}"
        elif file_val == text_val:
            notes = f"[WARN] File=Text, URL differs by {url_val - file_val:+d}"
        elif url_val == text_val:
            notes = f"[WARN] URL=Text, File differs by {file_val - url_val:+d}"
        else:
            notes = "[ERROR] All differ"
        
        print(f"{label:<30} {file_val:<15} {url_val:<15} {text_val:<15} {notes:<20}")
    
    # Compare citation texts
    print(f"\n{'='*80}")
    print("CITATION TEXT COMPARISON")
    print(f"{'='*80}")
    
    file_citations = file_result.get('citation_texts', set())
    url_citations = url_result.get('citation_texts', set())
    text_citations = text_result.get('citation_texts', set())
    
    # Find citations in all three
    all_three = file_citations & url_citations & text_citations
    print(f"\n[OK] Citations found in ALL THREE methods: {len(all_three)}")
    
    # Find citations only in file
    only_file = file_citations - url_citations - text_citations
    if only_file:
        print(f"\n[FILE ONLY] Citations ONLY in file upload ({len(only_file)}):")
        for cit in sorted(only_file)[:10]:
            print(f"    - {cit}")
    
    # Find citations only in URL
    only_url = url_citations - file_citations - text_citations
    if only_url:
        print(f"\n[URL ONLY] Citations ONLY in URL ({len(only_url)}):")
        for cit in sorted(only_url)[:10]:
            print(f"    - {cit}")
    
    # Find citations only in text
    only_text = text_citations - file_citations - url_citations
    if only_text:
        print(f"\n[TEXT ONLY] Citations ONLY in text ({len(only_text)}):")
        for cit in sorted(only_text)[:10]:
            print(f"    - {cit}")
    
    # Find citations in file and URL but not text
    file_url_not_text = (file_citations & url_citations) - text_citations
    if file_url_not_text:
        print(f"\n[WARN] Citations in File+URL but NOT in Text ({len(file_url_not_text)}):")
        for cit in sorted(file_url_not_text)[:10]:
            print(f"    - {cit}")
    
    # Find citations in file and text but not URL
    file_text_not_url = (file_citations & text_citations) - url_citations
    if file_text_not_url:
        print(f"\n[WARN] Citations in File+Text but NOT in URL ({len(file_text_not_url)}):")
        for cit in sorted(file_text_not_url)[:10]:
            print(f"    - {cit}")
    
    # Find citations in URL and text but not file
    url_text_not_file = (url_citations & text_citations) - file_citations
    if url_text_not_file:
        print(f"\n[WARN] Citations in URL+Text but NOT in File ({len(url_text_not_file)}):")
        for cit in sorted(url_text_not_file)[:10]:
            print(f"    - {cit}")


if __name__ == '__main__':
    # Test with the PDF file
    pdf_path = r'D:\dev\casestrainer\1031351.pdf'
    pdf_url = 'https://www.courts.wa.gov/opinions/pdf/1031351.pdf'
    
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        logger.info("Please ensure the PDF file exists at the specified path")
        sys.exit(1)
    
    print("="*80)
    print("COMPARING FILE UPLOAD, URL, AND TEXT PROCESSING")
    print("="*80)
    
    # Run all three tests
    print("\n1. Testing FILE UPLOAD...")
    file_result = test_file_upload(pdf_path)
    
    print("\n2. Testing URL PROCESSING...")
    url_result = test_url_processing(pdf_url)
    
    print("\n3. Testing TEXT PROCESSING...")
    text_result = test_text_processing(pdf_path)
    
    # Compare results
    compare_results(file_result, url_result, text_result)
    
    # Save detailed results to JSON
    output_file = 'comparison_all_three_methods.json'
    with open(output_file, 'w') as f:
        json.dump({
            'file_upload': {
                'citations_count': file_result.get('citations_count', 0),
                'clusters_count': file_result.get('clusters_count', 0),
                'unique_names_count': file_result.get('unique_names_count', 0),
                'citation_texts': list(file_result.get('citation_texts', set()))
            },
            'url': {
                'citations_count': url_result.get('citations_count', 0),
                'clusters_count': url_result.get('clusters_count', 0),
                'unique_names_count': url_result.get('unique_names_count', 0),
                'citation_texts': list(url_result.get('citation_texts', set()))
            },
            'text': {
                'citations_count': text_result.get('citations_count', 0),
                'clusters_count': text_result.get('clusters_count', 0),
                'unique_names_count': text_result.get('unique_names_count', 0),
                'citation_texts': list(text_result.get('citation_texts', set())),
                'text_length': text_result.get('text_length', 0)
            },
            'comparison': {
                'all_match': (
                    file_result.get('citations_count', 0) == url_result.get('citations_count', 0) == text_result.get('citations_count', 0)
                ),
                'common_citations': len(
                    file_result.get('citation_texts', set()) & 
                    url_result.get('citation_texts', set()) & 
                    text_result.get('citation_texts', set())
                )
            }
        }, f, indent=2)
    
    print(f"\n{'='*80}")
    print(f"Detailed results saved to: {output_file}")
    print(f"{'='*80}")

