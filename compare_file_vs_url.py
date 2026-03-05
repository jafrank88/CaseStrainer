#!/usr/bin/env python3
"""
Compare file upload vs URL processing for the same PDF document.
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
    level=logging.INFO,
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
            file_storage, 'file', request_id, 'test', force_mode='sync', enable_verification=True
        )
        
        citations = result.get('citations', [])
        clusters = result.get('clusters', [])
        
        logger.info(f"\nFILE UPLOAD RESULTS:")
        logger.info(f"  Citations found: {len(citations)}")
        logger.info(f"  Clusters found: {len(clusters)}")
        logger.info(f"  Text length: {len(result.get('text', ''))}")
        
        # Count unique case names
        unique_names = set()
        for cit in citations:
            name = cit.get('extracted_case_name') or cit.get('canonical_name')
            if name and name != 'N/A':
                unique_names.add(name)
        
        logger.info(f"  Unique case names: {len(unique_names)}")
        
        # Check for header contamination
        header_contaminated = []
        for cit in citations:
            extracted = cit.get('extracted_case_name', '')
            if 'ET AL' in extracted.upper() and 'PETITIONERS' in extracted.upper():
                header_contaminated.append({
                    'citation': cit.get('citation'),
                    'extracted_name': extracted
                })
        
        if header_contaminated:
            logger.warning(f"  Header contamination found: {len(header_contaminated)} citations")
            for item in header_contaminated[:5]:  # Show first 5
                logger.warning(f"    - {item['citation']}: {item['extracted_name']}")
        
        return {
            'method': 'file_upload',
            'citations_count': len(citations),
            'clusters_count': len(clusters),
            'unique_names_count': len(unique_names),
            'text_length': len(result.get('text', '')),
            'header_contaminated': len(header_contaminated),
            'citations': citations[:10],  # First 10 for comparison
            'clusters': clusters[:5]  # First 5 for comparison
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
            url, 'url', request_id, 'test', force_mode='sync', enable_verification=True
        )
        
        citations = result.get('citations', [])
        clusters = result.get('clusters', [])
        
        logger.info(f"\nURL PROCESSING RESULTS:")
        logger.info(f"  Citations found: {len(citations)}")
        logger.info(f"  Clusters found: {len(clusters)}")
        logger.info(f"  Text length: {len(result.get('text', ''))}")
        
        # Count unique case names
        unique_names = set()
        for cit in citations:
            name = cit.get('extracted_case_name') or cit.get('canonical_name')
            if name and name != 'N/A':
                unique_names.add(name)
        
        logger.info(f"  Unique case names: {len(unique_names)}")
        
        # Check for header contamination
        header_contaminated = []
        for cit in citations:
            extracted = cit.get('extracted_case_name', '')
            if 'ET AL' in extracted.upper() and 'PETITIONERS' in extracted.upper():
                header_contaminated.append({
                    'citation': cit.get('citation'),
                    'extracted_name': extracted
                })
        
        if header_contaminated:
            logger.warning(f"  Header contamination found: {len(header_contaminated)} citations")
            for item in header_contaminated[:5]:  # Show first 5
                logger.warning(f"    - {item['citation']}: {item['extracted_name']}")
        
        return {
            'method': 'url',
            'citations_count': len(citations),
            'clusters_count': len(clusters),
            'unique_names_count': len(unique_names),
            'text_length': len(result.get('text', '')),
            'header_contaminated': len(header_contaminated),
            'citations': citations[:10],  # First 10 for comparison
            'clusters': clusters[:5]  # First 5 for comparison
        }
        
    except Exception as e:
        logger.error(f"URL processing failed: {e}", exc_info=True)
        return {'method': 'url', 'error': str(e)}


def compare_results(file_result: dict, url_result: dict):
    """Compare results from both methods."""
    logger.info(f"\n{'='*80}")
    logger.info("COMPARISON SUMMARY")
    logger.info(f"{'='*80}")
    
    if 'error' in file_result:
        logger.error(f"File upload failed: {file_result['error']}")
        return
    
    if 'error' in url_result:
        logger.error(f"URL processing failed: {url_result['error']}")
        return
    
    print(f"\n{'Metric':<30} {'File Upload':<20} {'URL':<20} {'Difference':<20}")
    print(f"{'-'*90}")
    
    metrics = [
        ('Citations', 'citations_count'),
        ('Clusters', 'clusters_count'),
        ('Unique Names', 'unique_names_count'),
        ('Text Length', 'text_length'),
        ('Header Contaminated', 'header_contaminated')
    ]
    
    for label, key in metrics:
        file_val = file_result.get(key, 0)
        url_val = url_result.get(key, 0)
        diff = file_val - url_val
        diff_str = f"{diff:+d}" if diff != 0 else "0"
        print(f"{label:<30} {file_val:<20} {url_val:<20} {diff_str:<20}")
    
    # Compare extracted case names
    logger.info(f"\n{'='*80}")
    logger.info("EXTRACTED CASE NAMES COMPARISON")
    logger.info(f"{'='*80}")
    
    file_names = {cit.get('citation'): cit.get('extracted_case_name') 
                  for cit in file_result.get('citations', [])}
    url_names = {cit.get('citation'): cit.get('extracted_case_name') 
                 for cit in url_result.get('citations', [])}
    
    # Find citations in both
    common_citations = set(file_names.keys()) & set(url_names.keys())
    logger.info(f"Common citations: {len(common_citations)}")
    
    # Find differences
    differences = []
    for citation in common_citations:
        file_name = file_names.get(citation)
        url_name = url_names.get(citation)
        if file_name != url_name:
            differences.append({
                'citation': citation,
                'file_upload': file_name,
                'url': url_name
            })
    
    if differences:
        logger.warning(f"\nFound {len(differences)} citations with different extracted names:")
        for diff in differences[:10]:  # Show first 10
            logger.warning(f"  {diff['citation']}:")
            logger.warning(f"    File: {diff['file_upload']}")
            logger.warning(f"    URL:  {diff['url']}")
    else:
        logger.info("No differences in extracted case names for common citations")


if __name__ == '__main__':
    # Test with the PDF file
    pdf_path = r'D:\dev\casestrainer\1031351.pdf'
    pdf_url = 'https://www.courts.wa.gov/opinions/pdf/1031351.pdf'
    
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        logger.info("Please ensure the PDF file exists at the specified path")
        sys.exit(1)
    
    # Run both tests
    file_result = test_file_upload(pdf_path)
    url_result = test_url_processing(pdf_url)
    
    # Compare results
    compare_results(file_result, url_result)
    
    # Save detailed results to JSON
    output_file = 'comparison_results.json'
    with open(output_file, 'w') as f:
        json.dump({
            'file_upload': file_result,
            'url': url_result,
            'comparison': {
                'citations_diff': file_result.get('citations_count', 0) - url_result.get('citations_count', 0),
                'clusters_diff': file_result.get('clusters_count', 0) - url_result.get('clusters_count', 0),
                'text_length_diff': file_result.get('text_length', 0) - url_result.get('text_length', 0)
            }
        }, f, indent=2)
    
    logger.info(f"\nDetailed results saved to: {output_file}")

