#!/usr/bin/env python3
"""
Process 50 briefs using the existing production pipeline
"""

import os
import sys
import time
import json
import logging
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
project_root = Path(__file__).parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import the production pipeline
from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
from src.citation_clustering import group_citations_into_clusters

def setup_logging():
    """Setup logging for the brief processing"""
    log_filename = f"brief_processing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def process_50_briefs():
    """Process all 50 briefs using the production pipeline"""
    
    logger = setup_logging()
    logger.info("Starting processing of 50 briefs using production pipeline")
    
    # Brief directory
    briefs_dir = Path("wa_briefs")
    if not briefs_dir.exists():
        logger.error(f"Briefs directory not found: {briefs_dir}")
        return False
    
    # Get all PDF files
    pdf_files = list(briefs_dir.glob("*.pdf"))
    logger.info(f"Found {len(pdf_files)} PDF files in {briefs_dir}")
    
    # Filter to exactly 50 briefs (exclude any extra files)
    brief_files = [f for f in pdf_files if f.name.startswith(('0', '1', '2', '3', '4', '5'))][:50]
    logger.info(f"Processing {len(brief_files)} briefs")
    
    # Initialize the production processor
    logger.info("Initializing UnifiedCitationProcessorV2 (production pipeline)")
    processor = UnifiedCitationProcessorV2()
    
    # Results storage
    all_results = []
    processing_stats = {
        'total_briefs': len(brief_files),
        'successfully_processed': 0,
        'failed_processing': 0,
        'total_citations': 0,
        'total_verified': 0,
        'total_clusters': 0,
        'processing_times': [],
        'start_time': datetime.now().isoformat()
    }
    
    # Process each brief
    for i, brief_file in enumerate(brief_files, 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing Brief {i}/{len(brief_files)}: {brief_file.name}")
        logger.info(f"{'='*60}")
        
        start_time = time.time()
        
        try:
            # Read the PDF file and extract text first
            logger.info(f"Extracting text from PDF: {brief_file}")
            
            # Import PDF text extraction
            try:
                import PyPDF2
                with open(brief_file, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
            except ImportError:
                logger.error("PyPDF2 not available. Install with: pip install PyPDF2")
                raise
            except Exception as e:
                logger.error(f"Failed to extract text from PDF: {e}")
                raise
            
            logger.info(f"Extracted {len(text)} characters from PDF")
            
            # Process the text using the production pipeline
            logger.info(f"Processing text with UnifiedCitationProcessorV2")
            result = processor.process_text(text)
            
            processing_time = time.time() - start_time
            processing_stats['processing_times'].append(processing_time)
            
            # Extract results
            citations = result.get('citations', [])
            clusters = result.get('clusters', [])
            
            # Count verified citations
            verified_count = sum(1 for c in citations if getattr(c, 'verified', False))
            
            # Create summary for this brief
            brief_summary = {
                'brief_number': i,
                'filename': brief_file.name,
                'processing_time': processing_time,
                'citations_found': len(citations),
                'citations_verified': verified_count,
                'verification_rate': (verified_count / len(citations) * 100) if citations else 0,
                'clusters_created': len(clusters),
                'text_length': result.get('text_length', 0),
                'success': True
            }
            
            # Add detailed citation information
            brief_summary['citations'] = []
            for citation in citations:
                citation_info = {
                    'citation': getattr(citation, 'citation', ''),
                    'verified': getattr(citation, 'verified', False),
                    'canonical_name': getattr(citation, 'canonical_name', None),
                    'extracted_case_name': getattr(citation, 'extracted_case_name', None),
                    'source': getattr(citation, 'source', None),
                    'confidence': getattr(citation, 'confidence', None),
                    'court': getattr(citation, 'court', None)
                }
                brief_summary['citations'].append(citation_info)
            
            all_results.append(brief_summary)
            
            # Update stats
            processing_stats['successfully_processed'] += 1
            processing_stats['total_citations'] += len(citations)
            processing_stats['total_verified'] += verified_count
            processing_stats['total_clusters'] += len(clusters)
            
            # Log summary for this brief
            logger.info(f"Brief {i} Results:")
            logger.info(f"  Citations found: {len(citations)}")
            logger.info(f"  Citations verified: {verified_count} ({verified_count/len(citations)*100:.1f}%)" if citations else "  No citations found")
            logger.info(f"  Clusters created: {len(clusters)}")
            logger.info(f"  Processing time: {processing_time:.2f} seconds")
            
            # Show some example citations
            if citations:
                logger.info(f"  Example citations:")
                for j, citation in enumerate(citations[:3], 1):
                    status = "VERIFIED" if getattr(citation, 'verified', False) else "UNVERIFIED"
                    logger.info(f"    {j}. {getattr(citation, 'citation', '')} - {status}")
                if len(citations) > 3:
                    logger.info(f"    ... and {len(citations) - 3} more citations")
            
        except Exception as e:
            processing_time = time.time() - start_time
            processing_stats['processing_times'].append(processing_time)
            processing_stats['failed_processing'] += 1
            
            logger.error(f"Failed to process brief {i} ({brief_file.name}): {str(e)}")
            
            # Add failed result
            brief_summary = {
                'brief_number': i,
                'filename': brief_file.name,
                'processing_time': processing_time,
                'citations_found': 0,
                'citations_verified': 0,
                'verification_rate': 0,
                'clusters_created': 0,
                'text_length': 0,
                'success': False,
                'error': str(e)
            }
            all_results.append(brief_summary)
    
    # Calculate final statistics
    processing_stats['end_time'] = datetime.now().isoformat()
    processing_stats['total_processing_time'] = sum(processing_stats['processing_times'])
    processing_stats['average_processing_time'] = sum(processing_stats['processing_times']) / len(processing_stats['processing_times']) if processing_stats['processing_times'] else 0
    processing_stats['overall_verification_rate'] = (processing_stats['total_verified'] / processing_stats['total_citations'] * 100) if processing_stats['total_citations'] > 0 else 0
    
    # Save results to file
    results_filename = f"50_briefs_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_filename, 'w', encoding='utf-8') as f:
        json.dump({
            'processing_stats': processing_stats,
            'brief_results': all_results
        }, f, indent=2, ensure_ascii=False)
    
    # Print final summary
    logger.info(f"\n{'='*80}")
    logger.info(f"FINAL PROCESSING SUMMARY - 50 BRIEFS")
    logger.info(f"{'='*80}")
    logger.info(f"Total briefs processed: {processing_stats['total_briefs']}")
    logger.info(f"Successfully processed: {processing_stats['successfully_processed']}")
    logger.info(f"Failed processing: {processing_stats['failed_processing']}")
    logger.info(f"Success rate: {processing_stats['successfully_processed']/processing_stats['total_briefs']*100:.1f}%")
    logger.info(f"")
    logger.info(f"Total citations found: {processing_stats['total_citations']}")
    logger.info(f"Total citations verified: {processing_stats['total_verified']}")
    logger.info(f"Overall verification rate: {processing_stats['overall_verification_rate']:.1f}%")
    logger.info(f"Total clusters created: {processing_stats['total_clusters']}")
    logger.info(f"")
    logger.info(f"Total processing time: {processing_stats['total_processing_time']:.2f} seconds")
    logger.info(f"Average time per brief: {processing_stats['average_processing_time']:.2f} seconds")
    logger.info(f"")
    logger.info(f"Results saved to: {results_filename}")
    logger.info(f"{'='*80}")
    
    return True

if __name__ == "__main__":
    success = process_50_briefs()
    if success:
        print("\n[SUCCESS] 50 briefs processing completed!")
    else:
        print("\n[FAILED] 50 briefs processing failed!")
    
    sys.exit(0 if success else 1)
