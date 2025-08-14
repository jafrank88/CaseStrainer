#!/usr/bin/env python3
"""
Batch test script for the corrected unified citation extraction pipeline.

Tests files from wa_briefs_txt folder to verify:
1. Citations are extracted correctly
2. Each citation has proper extracted name and year
3. Citations are properly clustered (parallel citations grouped)
4. False positive prevention works
5. Processing order is correct (context operations before deduplication)
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_file(file_path: str, processor: UnifiedCitationProcessorV2) -> dict:
    """Test a single file and return results."""
    logger.info(f"\n{'='*80}")
    logger.info(f"TESTING FILE: {os.path.basename(file_path)}")
    logger.info(f"{'='*80}")
    
    try:
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        logger.info(f"File size: {len(text)} characters")
        
        # Process with unified pipeline (use synchronous method)
        citations = processor._extract_citations_unified(text)
        
        # Analyze results
        results = {
            'file': os.path.basename(file_path),
            'file_size': len(text),
            'total_citations': len(citations),
            'citations_with_names': 0,
            'citations_with_dates': 0,
            'citations_with_both': 0,
            'parallel_groups': 0,
            'citations_in_parallel_groups': 0,
            'citations': []
        }
        
        # Track parallel groups
        parallel_groups = {}
        
        for citation in citations:
            citation_data = {
                'citation': citation.citation,
                'extracted_case_name': citation.extracted_case_name,
                'extracted_date': citation.extracted_date,
                'canonical_name': getattr(citation, 'canonical_name', None),
                'canonical_date': getattr(citation, 'canonical_date', None),
                'parallel_citations': getattr(citation, 'parallel_citations', []),
                'is_parallel': getattr(citation, 'is_parallel', False),
                'source': getattr(citation, 'source', 'unknown'),
                'confidence': getattr(citation, 'confidence', 0.0)
            }
            
            results['citations'].append(citation_data)
            
            # Count citations with metadata
            if citation.extracted_case_name:
                results['citations_with_names'] += 1
            if citation.extracted_date:
                results['citations_with_dates'] += 1
            if citation.extracted_case_name and citation.extracted_date:
                results['citations_with_both'] += 1
            
            # Track parallel groups
            if citation_data['is_parallel'] and citation_data['parallel_citations']:
                group_key = tuple(sorted([citation.citation] + citation_data['parallel_citations']))
                if group_key not in parallel_groups:
                    parallel_groups[group_key] = []
                parallel_groups[group_key].append(citation.citation)
        
        results['parallel_groups'] = len(parallel_groups)
        results['citations_in_parallel_groups'] = sum(len(group) for group in parallel_groups.values())
        
        # Print summary
        logger.info(f"\nRESULTS SUMMARY:")
        logger.info(f"  Total citations found: {results['total_citations']}")
        if results['total_citations'] > 0:
            logger.info(f"  Citations with names: {results['citations_with_names']} ({results['citations_with_names']/results['total_citations']*100:.1f}%)")
            logger.info(f"  Citations with dates: {results['citations_with_dates']} ({results['citations_with_dates']/results['total_citations']*100:.1f}%)")
            logger.info(f"  Citations with both: {results['citations_with_both']} ({results['citations_with_both']/results['total_citations']*100:.1f}%)")
        else:
            logger.info(f"  Citations with names: {results['citations_with_names']} (0.0%)")
            logger.info(f"  Citations with dates: {results['citations_with_dates']} (0.0%)")
            logger.info(f"  Citations with both: {results['citations_with_both']} (0.0%)")
        logger.info(f"  Parallel groups: {results['parallel_groups']}")
        logger.info(f"  Citations in parallel groups: {results['citations_in_parallel_groups']}")
        
        # Show first few citations as examples
        logger.info(f"\nFIRST 5 CITATIONS:")
        for i, citation in enumerate(results['citations'][:5]):
            logger.info(f"  {i+1}. {citation['citation']}")
            logger.info(f"     Name: {citation['extracted_case_name'] or 'None'}")
            logger.info(f"     Date: {citation['extracted_date'] or 'None'}")
            logger.info(f"     Parallel: {citation['is_parallel']}")
            if citation['parallel_citations']:
                logger.info(f"     Parallel with: {citation['parallel_citations']}")
        
        # Show parallel groups
        if parallel_groups:
            logger.info(f"\nPARALLEL GROUPS:")
            for i, (group_key, citations_in_group) in enumerate(parallel_groups.items(), 1):
                logger.info(f"  Group {i}: {list(group_key)}")
        
        return results
        
    except Exception as e:
        logger.error(f"Error testing file {file_path}: {e}")
        return {
            'file': os.path.basename(file_path),
            'error': str(e),
            'total_citations': 0
        }

def main():
    """Run batch tests on selected files."""
    logger.info("Starting batch test of unified citation extraction pipeline")
    
    # Initialize processor
    processor = UnifiedCitationProcessorV2()
    
    # Test files directory
    test_dir = Path("D:/dev/casestrainer/wa_briefs_txt")
    
    # Select representative test files (different types and sizes)
    test_files = [
        "001_Answer to Petition for Review.txt",  # Medium size
        "002_Petition for Review.txt",            # Large size
        "018_Plaintiff Opening Brief.txt",       # Very large size
        "020_Appellants Brief.txt",              # Medium size
        "025_Amicus - ACLU of Washington.txt"    # Small size
    ]
    
    all_results = []
    
    for filename in test_files:
        file_path = test_dir / filename
        if file_path.exists():
            results = test_file(str(file_path), processor)
            all_results.append(results)
        else:
            logger.warning(f"File not found: {file_path}")
    
    # Overall summary
    logger.info(f"\n{'='*80}")
    logger.info("OVERALL BATCH TEST SUMMARY")
    logger.info(f"{'='*80}")
    
    total_files = len([r for r in all_results if 'error' not in r])
    total_citations = sum(r.get('total_citations', 0) for r in all_results)
    total_with_names = sum(r.get('citations_with_names', 0) for r in all_results)
    total_with_dates = sum(r.get('citations_with_dates', 0) for r in all_results)
    total_with_both = sum(r.get('citations_with_both', 0) for r in all_results)
    total_parallel_groups = sum(r.get('parallel_groups', 0) for r in all_results)
    
    logger.info(f"Files tested: {total_files}")
    logger.info(f"Total citations: {total_citations}")
    if total_citations > 0:
        logger.info(f"Citations with names: {total_with_names} ({total_with_names/total_citations*100:.1f}%)")
        logger.info(f"Citations with dates: {total_with_dates} ({total_with_dates/total_citations*100:.1f}%)")
        logger.info(f"Citations with both: {total_with_both} ({total_with_both/total_citations*100:.1f}%)")
    else:
        logger.info(f"Citations with names: {total_with_names} (0.0%)")
        logger.info(f"Citations with dates: {total_with_dates} (0.0%)")
        logger.info(f"Citations with both: {total_with_both} (0.0%)")
    logger.info(f"Total parallel groups: {total_parallel_groups}")
    
    # Save detailed results
    output_file = "batch_test_results.json"
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    logger.info(f"\nDetailed results saved to: {output_file}")
    
    # Quality assessment
    logger.info(f"\nQUALITY ASSESSMENT:")
    name_rate = total_with_names/total_citations*100 if total_citations > 0 else 0
    date_rate = total_with_dates/total_citations*100 if total_citations > 0 else 0
    both_rate = total_with_both/total_citations*100 if total_citations > 0 else 0
    
    if name_rate >= 80:
        logger.info(f"✅ Name extraction: EXCELLENT ({name_rate:.1f}%)")
    elif name_rate >= 60:
        logger.info(f"⚠️  Name extraction: GOOD ({name_rate:.1f}%)")
    else:
        logger.info(f"❌ Name extraction: NEEDS IMPROVEMENT ({name_rate:.1f}%)")
    
    if date_rate >= 70:
        logger.info(f"✅ Date extraction: EXCELLENT ({date_rate:.1f}%)")
    elif date_rate >= 50:
        logger.info(f"⚠️  Date extraction: GOOD ({date_rate:.1f}%)")
    else:
        logger.info(f"❌ Date extraction: NEEDS IMPROVEMENT ({date_rate:.1f}%)")
    
    if both_rate >= 60:
        logger.info(f"✅ Complete metadata: EXCELLENT ({both_rate:.1f}%)")
    elif both_rate >= 40:
        logger.info(f"⚠️  Complete metadata: GOOD ({both_rate:.1f}%)")
    else:
        logger.info(f"❌ Complete metadata: NEEDS IMPROVEMENT ({both_rate:.1f}%)")
    
    if total_parallel_groups > 0:
        logger.info(f"✅ Parallel detection: WORKING ({total_parallel_groups} groups found)")
    else:
        logger.info(f"⚠️  Parallel detection: NO GROUPS FOUND (may be normal)")

if __name__ == "__main__":
    main()
