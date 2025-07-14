#!/usr/bin/env python3
"""
Process downloaded Washington State Courts Briefs through citation extraction pipeline.
This script runs the citation extraction and clustering logic on the downloaded briefs
to test and validate the extraction algorithms.
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Any
import argparse
import logging
from collections import Counter

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from unified_citation_processor_v2 import UnifiedCitationProcessorV2
from file_utils import extract_text_from_pdf
from citation_utils import CitationCluster

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('wa_briefs_processing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WABriefsProcessor:
    """Process WA briefs through citation extraction pipeline."""
    
    def __init__(self, briefs_dir: str = "wa_briefs", output_dir: str = "wa_briefs_results"):
        self.briefs_dir = Path(briefs_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize citation processor
        self.citation_processor = UnifiedCitationProcessorV2()
        
        # Track processing results
        self.processed_count = 0
        self.failed_count = 0
        self.total_citations = 0
        self.total_clusters = 0
        self.total_citations_with_years = 0
        
    def get_pdf_files(self) -> List[Path]:
        """Get all PDF files in the briefs directory."""
        pdf_files = list(self.briefs_dir.glob("*.pdf"))
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        return pdf_files
    
    def extract_text_from_brief(self, pdf_path: Path) -> str:
        """Extract text from a brief PDF."""
        try:
            logger.info(f"Extracting text from: {pdf_path.name}")
            text = extract_text_from_pdf(str(pdf_path))
            
            if not text or len(text.strip()) < 100:
                logger.warning(f"Extracted text too short for {pdf_path.name}")
                return ""
            
            logger.info(f"Extracted {len(text)} characters from {pdf_path.name}")
            return text
            
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path.name}: {e}")
            return ""
    
    def analyze_year_extraction(self, citations: List[str]) -> Dict[str, Any]:
        """Analyze year extraction from citations."""
        from case_name_extraction_core import extract_case_name_triple_comprehensive
        import re
        
        year_results = []
        year_counts = Counter()
        extraction_methods = Counter()
        
        for citation in citations:
            result = {
                'citation': citation,
                'extracted_years': [],
                'extraction_method': None,
                'confidence': 0.0
            }
            
            # Method 1: Direct regex extraction
            year_matches = re.findall(r'\b(19|20)\d{2}\b', citation)
            if year_matches:
                result['extracted_years'].extend([int(year) for year in year_matches])
                result['extraction_method'] = 'regex'
                result['confidence'] = 0.9
            
            # Method 2: Use case name extraction core
            try:
                extraction_result = extract_case_name_triple_comprehensive(citation)
                if extraction_result and 'extracted_year' in extraction_result:
                    extracted_year = extraction_result['extracted_year']
                    if extracted_year and extracted_year not in result['extracted_years']:
                        result['extracted_years'].append(extracted_year)
                        if result['extraction_method']:
                            result['extraction_method'] += '+core'
                        else:
                            result['extraction_method'] = 'core'
                        result['confidence'] = max(result['confidence'], 0.8)
            except Exception as e:
                pass
            
            # Method 3: Look for year patterns in context
            context_patterns = [
                r'\((\d{4})\)',  # Year in parentheses
                r',\s*(\d{4})\s*$',  # Year at end after comma
                r'\s+(\d{4})\s*$',  # Year at end
            ]
            
            for pattern in context_patterns:
                matches = re.findall(pattern, citation)
                for match in matches:
                    year = int(match)
                    if 1900 <= year <= 2030 and year not in result['extracted_years']:
                        result['extracted_years'].append(year)
                        if result['extraction_method']:
                            result['extraction_method'] += '+context'
                        else:
                            result['extraction_method'] = 'context'
                        result['confidence'] = max(result['confidence'], 0.7)
            
            # Remove duplicates and sort
            result['extracted_years'] = sorted(list(set(result['extracted_years'])))
            year_results.append(result)
            
            for year in result['extracted_years']:
                year_counts[year] += 1
            
            if result['extraction_method']:
                extraction_methods[result['extraction_method']] += 1
        
        return {
            'year_results': year_results,
            'year_distribution': dict(year_counts.most_common()),
            'extraction_methods': dict(extraction_methods),
            'total_citations': len(citations),
            'citations_with_years': len([r for r in year_results if r['extracted_years']]),
            'year_extraction_rate': len([r for r in year_results if r['extracted_years']]) / len(citations) if citations else 0
        }

    def process_brief_citations(self, pdf_path: Path, text: str) -> Dict[str, Any]:
        """Process citations from a brief."""
        try:
            logger.info(f"Processing citations for: {pdf_path.name}")
            
            # Extract citations using the unified processor
            extraction_result = self.citation_processor.process_text(text)
            
            if not extraction_result:
                logger.warning(f"No extraction result for {pdf_path.name}")
                return {}
            
            # Get extracted citations - process_text returns a list of CitationResult objects
            extracted_citations = [citation.citation_text for citation in extraction_result] if extraction_result else []
            
            # Analyze year extraction
            year_analysis = self.analyze_year_extraction(extracted_citations)
            
            # Process through clustering
            clusters = self.citation_processor.group_citations_into_clusters(
                extraction_result, text
            )
            
            # Convert clusters to serializable format
            serializable_clusters = []
            for cluster in clusters:
                if isinstance(cluster, CitationCluster):
                    serializable_clusters.append(cluster.to_dict())
                else:
                    serializable_clusters.append(cluster)
            
            result = {
                'filename': pdf_path.name,
                'file_size': pdf_path.stat().st_size,
                'text_length': len(text),
                'extracted_citations': extracted_citations,
                'clusters': serializable_clusters,
                'cluster_count': len(serializable_clusters),
                'citation_count': len(extracted_citations),
                'year_analysis': year_analysis,
                'processing_timestamp': time.time()
            }
            
            logger.info(f"Processed {pdf_path.name}: {len(extracted_citations)} citations, {len(serializable_clusters)} clusters, "
                       f"{year_analysis['citations_with_years']} with years")
            return result
            
        except Exception as e:
            logger.error(f"Error processing citations for {pdf_path.name}: {e}")
            return {
                'filename': pdf_path.name,
                'error': str(e),
                'processing_timestamp': time.time()
            }
    
    def save_results(self, results: List[Dict[str, Any]], summary_file: str = "processing_summary.json"):
        """Save processing results to files."""
        try:
            # Save individual results
            for result in results:
                if 'filename' in result and 'error' not in result:
                    filename = result['filename'].replace('.pdf', '_results.json')
                    result_file = self.output_dir / filename
                    
                    with open(result_file, 'w') as f:
                        json.dump(result, f, indent=2, default=str)
            
            # Save summary
            summary_data = {
                'processing_summary': {
                    'total_files': len(results),
                    'processed_successfully': self.processed_count,
                    'failed': self.failed_count,
                    'total_citations': self.total_citations,
                    'total_clusters': self.total_clusters,
                    'total_citations_with_years': self.total_citations_with_years,
                    'average_citations_per_brief': self.total_citations / max(1, self.processed_count),
                    'average_clusters_per_brief': self.total_clusters / max(1, self.processed_count),
                    'year_extraction_rate': self.total_citations_with_years / max(1, self.total_citations)
                },
                'file_results': results
            }
            
            summary_path = self.output_dir / summary_file
            with open(summary_path, 'w') as f:
                json.dump(summary_data, f, indent=2, default=str)
            
            logger.info(f"Results saved to {self.output_dir}")
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
    
    def generate_analysis_report(self, results: List[Dict[str, Any]]):
        """Generate analysis report of processing results."""
        try:
            report_file = self.output_dir / "analysis_report.txt"
            
            with open(report_file, 'w') as f:
                f.write("Washington State Courts Briefs Citation Analysis Report\n")
                f.write("=" * 60 + "\n\n")
                
                # Summary statistics
                f.write("SUMMARY STATISTICS:\n")
                f.write(f"Total briefs processed: {len(results)}\n")
                f.write(f"Successfully processed: {self.processed_count}\n")
                f.write(f"Failed processing: {self.failed_count}\n")
                f.write(f"Total citations extracted: {self.total_citations}\n")
                f.write(f"Total clusters created: {self.total_clusters}\n")
                f.write(f"Total citations with years: {self.total_citations_with_years}\n")
                f.write(f"Year extraction rate: {self.total_citations_with_years / max(1, self.total_citations):.1%}\n")
                f.write(f"Average citations per brief: {self.total_citations / max(1, self.processed_count):.1f}\n")
                f.write(f"Average clusters per brief: {self.total_clusters / max(1, self.processed_count):.1f}\n\n")
                
                # Year extraction analysis
                f.write("YEAR EXTRACTION ANALYSIS:\n")
                f.write("-" * 40 + "\n")
                
                # Aggregate year distribution across all briefs
                all_year_distributions = {}
                all_extraction_methods = Counter()
                
                for result in results:
                    if 'year_analysis' in result:
                        year_analysis = result['year_analysis']
                        
                        # Aggregate year distributions
                        for year, count in year_analysis['year_distribution'].items():
                            all_year_distributions[year] = all_year_distributions.get(year, 0) + count
                        
                        # Aggregate extraction methods
                        for method, count in year_analysis['extraction_methods'].items():
                            all_extraction_methods[method] += count
                
                if all_year_distributions:
                    f.write(f"Overall year distribution: {dict(all_year_distributions)}\n")
                if all_extraction_methods:
                    f.write(f"Extraction methods used: {dict(all_extraction_methods)}\n")
                
                f.write("\n")
                
                # Brief-by-brief breakdown
                f.write("BRIEF-BY-BRIEF BREAKDOWN:\n")
                f.write("-" * 40 + "\n")
                
                for result in results:
                    if 'error' in result:
                        f.write(f"{result['filename']}: ERROR - {result['error']}\n")
                    else:
                        year_info = ""
                        if 'year_analysis' in result:
                            year_analysis = result['year_analysis']
                            year_info = f", {year_analysis['citations_with_years']} with years ({year_analysis['year_extraction_rate']:.1%})"
                        
                        f.write(f"{result['filename']}: {result.get('citation_count', 0)} citations, "
                               f"{result.get('cluster_count', 0)} clusters{year_info}\n")
                
                f.write("\n")
                
                # Citation patterns analysis
                f.write("CITATION PATTERNS ANALYSIS:\n")
                f.write("-" * 40 + "\n")
                
                successful_results = [r for r in results if 'error' not in r]
                if successful_results:
                    citation_counts = [r.get('citation_count', 0) for r in successful_results]
                    cluster_counts = [r.get('cluster_count', 0) for r in successful_results]
                    
                    f.write(f"Citation count range: {min(citation_counts)} - {max(citation_counts)}\n")
                    f.write(f"Cluster count range: {min(cluster_counts)} - {max(cluster_counts)}\n")
                    
                    # Find briefs with most citations
                    most_citations = max(successful_results, key=lambda x: x.get('citation_count', 0))
                    f.write(f"Brief with most citations: {most_citations['filename']} "
                           f"({most_citations.get('citation_count', 0)} citations)\n")
                    
                    # Find briefs with most clusters
                    most_clusters = max(successful_results, key=lambda x: x.get('cluster_count', 0))
                    f.write(f"Brief with most clusters: {most_clusters['filename']} "
                           f"({most_clusters.get('cluster_count', 0)} clusters)\n")
                    
                    # Find briefs with best year extraction
                    if any('year_analysis' in r for r in successful_results):
                        best_year_extraction = max(
                            [r for r in successful_results if 'year_analysis' in r],
                            key=lambda x: x['year_analysis']['year_extraction_rate']
                        )
                        rate = best_year_extraction['year_analysis']['year_extraction_rate']
                        f.write(f"Brief with best year extraction: {best_year_extraction['filename']} "
                               f"({rate:.1%} rate)\n")
            
            logger.info(f"Analysis report saved to {report_file}")
            
        except Exception as e:
            logger.error(f"Error generating analysis report: {e}")
    
    def process_all_briefs(self):
        """Process all briefs in the directory."""
        logger.info("Starting WA briefs processing...")
        
        pdf_files = self.get_pdf_files()
        if not pdf_files:
            logger.warning("No PDF files found to process")
            return
        
        results = []
        
        for pdf_path in pdf_files:
            logger.info(f"Processing {pdf_path.name} ({self.processed_count + 1}/{len(pdf_files)})")
            
            # Extract text
            text = self.extract_text_from_brief(pdf_path)
            if not text:
                self.failed_count += 1
                results.append({
                    'filename': pdf_path.name,
                    'error': 'Failed to extract text',
                    'processing_timestamp': time.time()
                })
                continue
            
            # Process citations
            result = self.process_brief_citations(pdf_path, text)
            
            if result and 'error' not in result:
                self.processed_count += 1
                self.total_citations += result.get('citation_count', 0)
                self.total_clusters += result.get('cluster_count', 0)
                
                # Track year extraction stats
                if 'year_analysis' in result:
                    self.total_citations_with_years += result['year_analysis']['citations_with_years']
            else:
                self.failed_count += 1
            
            results.append(result)
            
            # Rate limiting
            time.sleep(0.1)
        
        # Save results
        self.save_results(results)
        self.generate_analysis_report(results)
        
        logger.info(f"Processing complete. Processed: {self.processed_count}, Failed: {self.failed_count}")
        logger.info(f"Total citations: {self.total_citations}, Total clusters: {self.total_clusters}")
        logger.info(f"Citations with years: {self.total_citations_with_years} ({self.total_citations_with_years / max(1, self.total_citations):.1%})")

def main():
    parser = argparse.ArgumentParser(description='Process WA briefs through citation extraction')
    parser.add_argument('--briefs-dir', default='wa_briefs', help='Directory containing downloaded briefs')
    parser.add_argument('--output-dir', default='wa_briefs_results', help='Output directory for results')
    
    args = parser.parse_args()
    
    processor = WABriefsProcessor(
        briefs_dir=args.briefs_dir,
        output_dir=args.output_dir
    )
    
    processor.process_all_briefs()

if __name__ == "__main__":
    main()
