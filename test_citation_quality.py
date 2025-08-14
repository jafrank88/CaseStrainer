#!/usr/bin/env python3
"""
Comprehensive test to verify citation extraction quality:
- Does every citation have a correct extracted name?
- Does every citation have a correct extracted year?
- Are citations properly clustered (parallel citations grouped)?

Compares results with Table of Authorities parser for ground truth.
"""

import os
import sys
import time
import logging
from pathlib import Path
from typing import List, Dict, Set

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
from src.toa_parser import ImprovedToAParser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def analyze_citation_quality(citations: List, file_name: str) -> Dict:
    """Analyze the quality of extracted citations."""
    if not citations:
        return {
            'total_citations': 0,
            'with_names': 0,
            'with_dates': 0,
            'with_both': 0,
            'name_rate': 0.0,
            'date_rate': 0.0,
            'complete_rate': 0.0,
            'parallel_groups': 0,
            'citations_in_parallel': 0
        }
    
    total = len(citations)
    with_names = 0
    with_dates = 0
    with_both = 0
    parallel_groups = set()
    citations_in_parallel = 0
    
    for citation in citations:
        # Check for extracted names
        name = None
        if hasattr(citation, 'extracted_case_name'):
            name = citation.extracted_case_name
        elif isinstance(citation, dict):
            name = citation.get('extracted_case_name')
        
        if name and name.strip():
            with_names += 1
        
        # Check for extracted dates/years
        date = None
        if hasattr(citation, 'extracted_date'):
            date = citation.extracted_date
        elif isinstance(citation, dict):
            date = citation.get('extracted_date')
        
        if date and str(date).strip():
            with_dates += 1
        
        # Check for both
        if name and name.strip() and date and str(date).strip():
            with_both += 1
        
        # Check for parallel citations
        is_parallel = False
        parallel_cites = []
        
        if hasattr(citation, 'is_parallel'):
            is_parallel = citation.is_parallel
        elif hasattr(citation, 'parallel_citations'):
            parallel_cites = citation.parallel_citations or []
            is_parallel = len(parallel_cites) > 0
        elif isinstance(citation, dict):
            is_parallel = citation.get('is_parallel', False)
            parallel_cites = citation.get('parallel_citations', [])
        
        if is_parallel:
            citations_in_parallel += 1
            # Create a group identifier
            cite_text = citation.citation if hasattr(citation, 'citation') else str(citation)
            group_key = tuple(sorted([cite_text] + parallel_cites))
            parallel_groups.add(group_key)
    
    return {
        'total_citations': total,
        'with_names': with_names,
        'with_dates': with_dates,
        'with_both': with_both,
        'name_rate': (with_names / total * 100) if total > 0 else 0.0,
        'date_rate': (with_dates / total * 100) if total > 0 else 0.0,
        'complete_rate': (with_both / total * 100) if total > 0 else 0.0,
        'parallel_groups': len(parallel_groups),
        'citations_in_parallel': citations_in_parallel
    }

def get_toa_ground_truth(text: str) -> Dict:
    """Get ground truth from Table of Authorities."""
    try:
        toa_parser = ImprovedToAParser()
        toa_entries = toa_parser.parse_toa_section(text)
        
        toa_citations = []
        for entry in toa_entries:
            for citation in entry.citations:
                toa_citations.append({
                    'citation': citation,
                    'extracted_case_name': entry.case_name,
                    'extracted_date': entry.years[0] if entry.years else None,
                    'confidence': entry.confidence
                })
        
        return {
            'toa_entries': toa_entries,
            'toa_citations': toa_citations,
            'analysis': analyze_citation_quality(toa_citations, 'TOA')
        }
    except Exception as e:
        logger.warning(f"TOA parsing failed: {e}")
        return {
            'toa_entries': [],
            'toa_citations': [],
            'analysis': analyze_citation_quality([], 'TOA'),
            'error': str(e)
        }

def remove_toa_section(text: str) -> str:
    """Remove Table of Authorities section from text."""
    # Find TOA section
    toa_start = text.upper().find("TABLE OF AUTHORITIES")
    if toa_start == -1:
        # Try alternative patterns
        patterns = [
            "AUTHORITIES CITED",
            "CITED AUTHORITIES",
            "CASES CITED",
            "LEGAL AUTHORITIES"
        ]
        for pattern in patterns:
            toa_start = text.upper().find(pattern)
            if toa_start != -1:
                break
    
    if toa_start == -1:
        logger.info("No TOA section found, using full text")
        return text
    
    # Find end of TOA (look for next major section)
    possible_ends = [
        text.upper().find("STATEMENT OF THE CASE", toa_start),
        text.upper().find("STATEMENT OF ISSUES", toa_start),
        text.upper().find("ARGUMENT", toa_start),
        text.upper().find("INTRODUCTION", toa_start),
        text.upper().find("SUMMARY", toa_start),
        text.upper().find("BACKGROUND", toa_start),
        text.upper().find("FACTS", toa_start)
    ]
    
    valid_ends = [end for end in possible_ends if end > toa_start]
    if valid_ends:
        toa_end = min(valid_ends)
        body_text = text[:toa_start] + text[toa_end:]
        logger.info(f"Removed TOA section ({toa_end - toa_start:,} characters)")
        return body_text
    else:
        logger.warning("Could not find end of TOA section, using text after TOA start")
        return text[toa_start + 1000:]  # Skip first 1000 chars of TOA

def test_citation_quality(file_path: str):
    """Test citation extraction quality on a single file."""
    logger.info(f"\n{'='*80}")
    logger.info(f"TESTING CITATION QUALITY: {os.path.basename(file_path)}")
    logger.info(f"{'='*80}")
    
    try:
        # Read file
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        logger.info(f"File size: {len(text):,} characters")
        
        # Get TOA ground truth
        logger.info("Extracting Table of Authorities (ground truth)...")
        toa_data = get_toa_ground_truth(text)
        toa_analysis = toa_data['analysis']
        
        # Remove TOA section for body extraction
        body_text = remove_toa_section(text)
        logger.info(f"Body text size: {len(body_text):,} characters")
        
        # Extract citations from body using unified pipeline
        logger.info("Extracting citations from body using unified pipeline...")
        processor = UnifiedCitationProcessorV2()
        
        start_time = time.time()
        body_citations = processor._extract_citations_unified(body_text)
        extraction_time = time.time() - start_time
        
        logger.info(f"Extraction completed in {extraction_time:.2f} seconds")
        
        # Analyze body extraction quality
        body_analysis = analyze_citation_quality(body_citations, 'Body')
        
        # Print detailed comparison
        logger.info(f"\nQUALITY ANALYSIS:")
        logger.info(f"{'Metric':<25} {'TOA (Ground Truth)':<20} {'Body (Extracted)':<20} {'Difference':<15}")
        logger.info(f"{'-'*80}")
        
        metrics = [
            ('Total Citations', toa_analysis['total_citations'], body_analysis['total_citations']),
            ('With Names', toa_analysis['with_names'], body_analysis['with_names']),
            ('With Dates', toa_analysis['with_dates'], body_analysis['with_dates']),
            ('Complete (Both)', toa_analysis['with_both'], body_analysis['with_both']),
            ('Name Rate %', f"{toa_analysis['name_rate']:.1f}", f"{body_analysis['name_rate']:.1f}"),
            ('Date Rate %', f"{toa_analysis['date_rate']:.1f}", f"{body_analysis['date_rate']:.1f}"),
            ('Complete Rate %', f"{toa_analysis['complete_rate']:.1f}", f"{body_analysis['complete_rate']:.1f}"),
            ('Parallel Groups', toa_analysis['parallel_groups'], body_analysis['parallel_groups']),
        ]
        
        for metric, toa_val, body_val in metrics:
            if isinstance(toa_val, (int, float)) and isinstance(body_val, (int, float)):
                diff = body_val - toa_val
                diff_str = f"{diff:+.1f}" if isinstance(diff, float) else f"{diff:+d}"
            else:
                diff_str = "N/A"
            
            logger.info(f"{metric:<25} {str(toa_val):<20} {str(body_val):<20} {diff_str:<15}")
        
        # Show sample citations
        logger.info(f"\nSAMPLE CITATIONS FROM BODY (first 5):")
        for i, citation in enumerate(body_citations[:5], 1):
            logger.info(f"  {i}. {citation.citation}")
            logger.info(f"     Name: {citation.extracted_case_name or 'MISSING'}")
            logger.info(f"     Date: {citation.extracted_date or 'MISSING'}")
            logger.info(f"     Parallel: {getattr(citation, 'is_parallel', False)}")
            if hasattr(citation, 'parallel_citations') and citation.parallel_citations:
                logger.info(f"     Parallel with: {citation.parallel_citations}")
        
        # Quality assessment
        logger.info(f"\nQUALITY ASSESSMENT:")
        
        if body_analysis['name_rate'] >= 80:
            logger.info(f"✅ Name extraction: EXCELLENT ({body_analysis['name_rate']:.1f}%)")
        elif body_analysis['name_rate'] >= 60:
            logger.info(f"⚠️  Name extraction: GOOD ({body_analysis['name_rate']:.1f}%)")
        else:
            logger.info(f"❌ Name extraction: NEEDS IMPROVEMENT ({body_analysis['name_rate']:.1f}%)")
        
        if body_analysis['date_rate'] >= 70:
            logger.info(f"✅ Date extraction: EXCELLENT ({body_analysis['date_rate']:.1f}%)")
        elif body_analysis['date_rate'] >= 50:
            logger.info(f"⚠️  Date extraction: GOOD ({body_analysis['date_rate']:.1f}%)")
        else:
            logger.info(f"❌ Date extraction: NEEDS IMPROVEMENT ({body_analysis['date_rate']:.1f}%)")
        
        if body_analysis['complete_rate'] >= 60:
            logger.info(f"✅ Complete metadata: EXCELLENT ({body_analysis['complete_rate']:.1f}%)")
        elif body_analysis['complete_rate'] >= 40:
            logger.info(f"⚠️  Complete metadata: GOOD ({body_analysis['complete_rate']:.1f}%)")
        else:
            logger.info(f"❌ Complete metadata: NEEDS IMPROVEMENT ({body_analysis['complete_rate']:.1f}%)")
        
        if body_analysis['parallel_groups'] > 0:
            logger.info(f"✅ Parallel detection: WORKING ({body_analysis['parallel_groups']} groups found)")
        else:
            logger.info(f"⚠️  Parallel detection: NO GROUPS FOUND")
        
        return {
            'file': os.path.basename(file_path),
            'toa_analysis': toa_analysis,
            'body_analysis': body_analysis,
            'extraction_time': extraction_time
        }
        
    except Exception as e:
        logger.error(f"Error testing file {file_path}: {e}")
        return {
            'file': os.path.basename(file_path),
            'error': str(e)
        }

def main():
    """Run comprehensive citation quality tests."""
    logger.info("Starting comprehensive citation quality analysis")
    logger.info("="*80)
    
    # Test files - select a variety of sizes
    test_dir = Path("D:/dev/casestrainer/wa_briefs_txt")
    test_files = [
        "001_Answer to Petition for Review.txt",  # Medium size (~32KB)
        "020_Appellants Brief.txt",              # Medium-large size (~60KB)
        "025_Amicus - ACLU of Washington.txt"    # Small size (~16KB)
    ]
    
    results = []
    
    for filename in test_files:
        file_path = test_dir / filename
        if file_path.exists():
            result = test_citation_quality(str(file_path))
            results.append(result)
        else:
            logger.warning(f"File not found: {file_path}")
    
    # Overall summary
    logger.info(f"\n{'='*80}")
    logger.info("OVERALL CITATION QUALITY SUMMARY")
    logger.info(f"{'='*80}")
    
    valid_results = [r for r in results if 'error' not in r]
    
    if valid_results:
        # Calculate averages
        avg_name_rate = sum(r['body_analysis']['name_rate'] for r in valid_results) / len(valid_results)
        avg_date_rate = sum(r['body_analysis']['date_rate'] for r in valid_results) / len(valid_results)
        avg_complete_rate = sum(r['body_analysis']['complete_rate'] for r in valid_results) / len(valid_results)
        avg_extraction_time = sum(r['extraction_time'] for r in valid_results) / len(valid_results)
        total_parallel_groups = sum(r['body_analysis']['parallel_groups'] for r in valid_results)
        
        logger.info(f"Files tested: {len(valid_results)}")
        logger.info(f"Average name extraction rate: {avg_name_rate:.1f}%")
        logger.info(f"Average date extraction rate: {avg_date_rate:.1f}%")
        logger.info(f"Average complete metadata rate: {avg_complete_rate:.1f}%")
        logger.info(f"Average extraction time: {avg_extraction_time:.2f} seconds")
        logger.info(f"Total parallel groups found: {total_parallel_groups}")
        
        # Final assessment
        logger.info(f"\nFINAL ASSESSMENT:")
        
        if avg_name_rate >= 80 and avg_date_rate >= 70 and avg_complete_rate >= 60:
            logger.info("🎉 EXCELLENT: Citation extraction quality is very high!")
        elif avg_name_rate >= 60 and avg_date_rate >= 50 and avg_complete_rate >= 40:
            logger.info("👍 GOOD: Citation extraction quality is acceptable with room for improvement")
        else:
            logger.info("⚠️  NEEDS WORK: Citation extraction quality needs significant improvement")
        
        # Answer the user's question directly
        logger.info(f"\n🔍 ANSWER TO YOUR QUESTION:")
        logger.info(f"Does every citation have correct extracted name, year and cluster?")
        
        if avg_complete_rate >= 90:
            logger.info("✅ YES: Nearly all citations have complete metadata")
        elif avg_complete_rate >= 70:
            logger.info("⚠️  MOSTLY: Most citations have complete metadata, but some are missing")
        else:
            logger.info("❌ NO: Many citations are missing names, dates, or clustering information")
    
    else:
        logger.error("No valid results to analyze")

if __name__ == "__main__":
    main()
