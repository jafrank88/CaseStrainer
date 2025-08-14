#!/usr/bin/env python3
"""
Performance Comparison Test: Original vs Unified vs Optimized Pipelines

This test compares:
1. Original pipeline (fast but incomplete)
2. Unified pipeline (comprehensive but slow)
3. Optimized pipeline (comprehensive and fast)

Also compares results with Table of Authorities parser for ground truth.
"""

import os
import sys
import time
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
from src.unified_citation_processor_v2_optimized import OptimizedUnifiedCitationProcessorV2
from src.toa_parser import ImprovedToAParser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_original_pipeline(text: str) -> Dict[str, Any]:
    """Test the original regex-only pipeline for comparison."""
    logger.info("Testing ORIGINAL pipeline (regex-only)...")
    
    start_time = time.time()
    
    # Simulate original pipeline: basic regex extraction only
    import re
    citations = []
    
    # Basic citation patterns (simplified version of original)
    patterns = [
        r'\b\d+\s+U\.S\.\s+\d+\b',
        r'\b\d+\s+S\.Ct\.\s+\d+\b',
        r'\b\d+\s+F\.3d\s+\d+\b',
        r'\b\d+\s+F\.2d\s+\d+\b',
        r'\b\d+\s+P\.3d\s+\d+\b',
        r'\b\d+\s+P\.2d\s+\d+\b',
    ]
    
    seen = set()
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            citation = match.group(0)
            if citation not in seen:
                citations.append({
                    'citation': citation,
                    'extracted_case_name': None,  # Original didn't extract names
                    'extracted_date': None,       # Original didn't extract dates
                    'source': 'original_regex'
                })
                seen.add(citation)
    
    end_time = time.time()
    
    return {
        'pipeline': 'Original (regex-only)',
        'time': end_time - start_time,
        'citations': citations,
        'count': len(citations),
        'with_names': 0,  # Original didn't extract names
        'with_dates': 0,  # Original didn't extract dates
        'with_both': 0
    }

def test_unified_pipeline(text: str) -> Dict[str, Any]:
    """Test the comprehensive unified pipeline."""
    logger.info("Testing UNIFIED pipeline (comprehensive)...")
    
    processor = UnifiedCitationProcessorV2()
    
    start_time = time.time()
    citations = processor._extract_citations_unified(text)
    end_time = time.time()
    
    # Analyze results
    with_names = sum(1 for c in citations if c.extracted_case_name)
    with_dates = sum(1 for c in citations if c.extracted_date)
    with_both = sum(1 for c in citations if c.extracted_case_name and c.extracted_date)
    
    return {
        'pipeline': 'Unified (comprehensive)',
        'time': end_time - start_time,
        'citations': citations,
        'count': len(citations),
        'with_names': with_names,
        'with_dates': with_dates,
        'with_both': with_both
    }

def test_optimized_pipeline(text: str) -> Dict[str, Any]:
    """Test the optimized unified pipeline."""
    logger.info("Testing OPTIMIZED pipeline (comprehensive + fast)...")
    
    processor = OptimizedUnifiedCitationProcessorV2()
    
    start_time = time.time()
    citations, stats = processor.extract_citations_optimized(text)
    end_time = time.time()
    
    # Analyze results
    with_names = sum(1 for c in citations if c.extracted_case_name)
    with_dates = sum(1 for c in citations if c.extracted_date)
    with_both = sum(1 for c in citations if c.extracted_case_name and c.extracted_date)
    
    return {
        'pipeline': 'Optimized (comprehensive + fast)',
        'time': end_time - start_time,
        'citations': citations,
        'count': len(citations),
        'with_names': with_names,
        'with_dates': with_dates,
        'with_both': with_both,
        'stats': stats
    }

def test_toa_parser(text: str) -> Dict[str, Any]:
    """Test Table of Authorities parser for ground truth."""
    logger.info("Testing TOA parser (ground truth)...")
    
    try:
        toa_parser = ImprovedToAParser()
        
        start_time = time.time()
        toa_entries = toa_parser.parse_toa_section(text)
        end_time = time.time()
        
        # Convert to citation list
        toa_citations = []
        for entry in toa_entries:
            for citation in entry.citations:
                toa_citations.append({
                    'citation': citation,
                    'extracted_case_name': entry.case_name,
                    'extracted_date': entry.years[0] if entry.years else None,
                    'source': 'toa_parser'
                })
        
        with_names = sum(1 for c in toa_citations if c['extracted_case_name'])
        with_dates = sum(1 for c in toa_citations if c['extracted_date'])
        with_both = sum(1 for c in toa_citations if c['extracted_case_name'] and c['extracted_date'])
        
        return {
            'pipeline': 'TOA Parser (ground truth)',
            'time': end_time - start_time,
            'citations': toa_citations,
            'count': len(toa_citations),
            'with_names': with_names,
            'with_dates': with_dates,
            'with_both': with_both
        }
        
    except Exception as e:
        logger.error(f"TOA parser failed: {e}")
        return {
            'pipeline': 'TOA Parser (failed)',
            'time': 0,
            'citations': [],
            'count': 0,
            'with_names': 0,
            'with_dates': 0,
            'with_both': 0,
            'error': str(e)
        }

def compare_pipelines(file_path: str):
    """Compare all pipelines on a single file."""
    logger.info(f"\n{'='*80}")
    logger.info(f"COMPARING PIPELINES: {os.path.basename(file_path)}")
    logger.info(f"{'='*80}")
    
    # Read file
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        logger.info(f"File size: {len(text):,} characters")
        
        # Test all pipelines
        results = []
        
        # 1. Original pipeline
        results.append(test_original_pipeline(text))
        
        # 2. Unified pipeline
        results.append(test_unified_pipeline(text))
        
        # 3. Optimized pipeline
        results.append(test_optimized_pipeline(text))
        
        # 4. TOA parser (ground truth)
        results.append(test_toa_parser(text))
        
        # Print comparison
        logger.info(f"\nPERFORMANCE COMPARISON:")
        logger.info(f"{'Pipeline':<30} {'Time (s)':<10} {'Citations':<10} {'Names':<8} {'Dates':<8} {'Both':<8} {'Rate':<15}")
        logger.info(f"{'-'*90}")
        
        for result in results:
            if 'error' not in result:
                rate = f"{result['count']/result['time']:.1f} cit/s" if result['time'] > 0 else "N/A"
                logger.info(f"{result['pipeline']:<30} {result['time']:<10.2f} {result['count']:<10} {result['with_names']:<8} {result['with_dates']:<8} {result['with_both']:<8} {rate:<15}")
            else:
                logger.info(f"{result['pipeline']:<30} {'ERROR':<10} {'-':<10} {'-':<8} {'-':<8} {'-':<8} {'-':<15}")
        
        # Show sample citations from each pipeline
        logger.info(f"\nSAMPLE CITATIONS (first 3 from each pipeline):")
        for result in results:
            if 'error' not in result and result['citations']:
                logger.info(f"\n{result['pipeline']}:")
                for i, citation in enumerate(result['citations'][:3], 1):
                    if isinstance(citation, dict):
                        logger.info(f"  {i}. {citation['citation']}")
                        logger.info(f"     Name: {citation.get('extracted_case_name', 'None')}")
                        logger.info(f"     Date: {citation.get('extracted_date', 'None')}")
                    else:
                        logger.info(f"  {i}. {citation.citation}")
                        logger.info(f"     Name: {getattr(citation, 'extracted_case_name', 'None')}")
                        logger.info(f"     Date: {getattr(citation, 'extracted_date', 'None')}")
        
        return results
        
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {e}")
        return []

def main():
    """Run performance comparison on selected files."""
    logger.info("Starting pipeline performance comparison")
    
    # Test files
    test_dir = Path("D:/dev/casestrainer/wa_briefs_txt")
    test_files = [
        "001_Answer to Petition for Review.txt",  # Medium size (~32KB)
        "020_Appellants Brief.txt",              # Medium size (~60KB)
    ]
    
    all_results = []
    
    for filename in test_files:
        file_path = test_dir / filename
        if file_path.exists():
            results = compare_pipelines(str(file_path))
            all_results.extend(results)
        else:
            logger.warning(f"File not found: {file_path}")
    
    # Overall summary
    logger.info(f"\n{'='*80}")
    logger.info("OVERALL PERFORMANCE SUMMARY")
    logger.info(f"{'='*80}")
    
    # Group results by pipeline
    pipeline_results = {}
    for result in all_results:
        if 'error' not in result:
            pipeline = result['pipeline']
            if pipeline not in pipeline_results:
                pipeline_results[pipeline] = []
            pipeline_results[pipeline].append(result)
    
    # Calculate averages
    logger.info(f"{'Pipeline':<30} {'Avg Time (s)':<12} {'Avg Citations':<12} {'Avg Names %':<12} {'Avg Dates %':<12}")
    logger.info(f"{'-'*80}")
    
    for pipeline, results in pipeline_results.items():
        if results:
            avg_time = sum(r['time'] for r in results) / len(results)
            avg_citations = sum(r['count'] for r in results) / len(results)
            avg_names_pct = sum(r['with_names']/r['count']*100 if r['count'] > 0 else 0 for r in results) / len(results)
            avg_dates_pct = sum(r['with_dates']/r['count']*100 if r['count'] > 0 else 0 for r in results) / len(results)
            
            logger.info(f"{pipeline:<30} {avg_time:<12.2f} {avg_citations:<12.1f} {avg_names_pct:<12.1f} {avg_dates_pct:<12.1f}")
    
    # Performance insights
    logger.info(f"\nPERFORMANCE INSIGHTS:")
    
    original_times = [r['time'] for r in all_results if r['pipeline'].startswith('Original')]
    unified_times = [r['time'] for r in all_results if r['pipeline'].startswith('Unified')]
    optimized_times = [r['time'] for r in all_results if r['pipeline'].startswith('Optimized')]
    
    if original_times and unified_times:
        slowdown = (sum(unified_times) / len(unified_times)) / (sum(original_times) / len(original_times))
        logger.info(f"📊 Unified pipeline is {slowdown:.1f}x slower than original")
    
    if unified_times and optimized_times:
        speedup = (sum(unified_times) / len(unified_times)) / (sum(optimized_times) / len(optimized_times))
        logger.info(f"🚀 Optimized pipeline is {speedup:.1f}x faster than unified")
    
    if original_times and optimized_times:
        overall_slowdown = (sum(optimized_times) / len(optimized_times)) / (sum(original_times) / len(original_times))
        logger.info(f"⚖️  Optimized pipeline is {overall_slowdown:.1f}x slower than original (but much more comprehensive)")

if __name__ == "__main__":
    main()
