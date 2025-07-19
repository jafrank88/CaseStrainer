#!/usr/bin/env python3
"""
Test script for the Enhanced Unified Citation Processor
"""

import sys
import os
from pathlib import Path
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set up logging to file and console
log_dir = os.path.join(os.getcwd(), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'enhanced_processor_debug.log')

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
if not any(isinstance(h, logging.FileHandler) and h.baseFilename == log_file for h in logger.handlers):
    logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('[%(levelname)s] %(message)s')
console_handler.setFormatter(console_formatter)
if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
    logger.addHandler(console_handler)

from enhanced_unified_citation_processor import (
    EnhancedUnifiedCitationProcessor, 
    ProcessingConfig, 
    extract_citations_enhanced,
    extract_citations_simple
)

def test_enhanced_processor():
    logging.info("[DEBUG] Starting test_enhanced_processor()...")
    # Test text with various citation formats
    test_text = """
    A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlsen v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003).
    
    Additionally, the Supreme Court in Smith v. Jones, 123 F.3d 456 (1999) established important precedent.
    """
    logging.info("[DEBUG] Created test_text.")
    # Test with enhanced configuration (disable verification for debugging)
    config = ProcessingConfig(
        enable_verification=False,
        enable_bluebook_formatting=True,
        enable_confidence_breakdown=True,
        enable_validation=True,
        enable_clustering=True,
        debug_mode=True
    )
    logging.info("[DEBUG] Created ProcessingConfig with verification disabled.")
    logging.info(f"Processing text with enhanced configuration...")
    citations = extract_citations_enhanced(test_text, config)
    logging.info("[DEBUG] extract_citations_enhanced returned.")
    logging.info(f"Found {len(citations)} enhanced citations:")
    
    for i, citation in enumerate(citations, 1):
        logging.info(f"\n--- Citation {i} ---")
        logging.info(f"Raw Citation: {citation.citation}")
        logging.info(f"Case Name: {citation.extracted_case_name}")
        logging.info(f"Year: {citation.extracted_date}")
        logging.info(f"Bluebook Format: {citation.bluebook_format}")
        logging.info(f"Confidence: {citation.confidence:.2f}")
        logging.info(f"Precedent Strength: {citation.precedent_strength}")
        logging.info(f"Verified: {citation.verified}")
        logging.info(f"Method: {citation.method}")
        logging.info(f"Pattern: {citation.pattern}")
        
        if citation.confidence_breakdown:
            logging.info(f"Confidence Breakdown:")
            for factor, score in citation.confidence_breakdown.items():
                logging.info(f"  {factor}: {score:.2f}")
        
        if citation.validation_result:
            logging.info(f"Validation: {citation.validation_result.get('validation_score', 0):.2f}")
            if citation.validation_result.get('warnings'):
                logging.info(f"Warnings: {citation.validation_result['warnings']}")
        
        if citation.reporter_info:
            logging.info(f"Reporter: {citation.reporter_info.get('name', 'Unknown')}")
            logging.info(f"Jurisdiction: {citation.reporter_info.get('jurisdiction', 'Unknown')}")
            logging.info(f"Level: {citation.reporter_info.get('level', 'Unknown')}")
    logging.info("[DEBUG] Finished printing enhanced citations.")
    # Test simple extraction
    logging.info(f"\n--- Simple Extraction Test ---")
    simple_results = extract_citations_simple(test_text)
    logging.info(f"Simple results: {len(simple_results)} citations")
    
    for result in simple_results:
        logging.info(f"  {result['citation']} -> {result['case_name']} ({result['year']}) - {result['confidence']:.2f}")
    logging.info("[DEBUG] Finished simple extraction test.")

def test_comparison():
    logging.info("[DEBUG] Starting test_comparison()...")
    test_text = "Smith v. Jones, 123 F.3d 456 (1999)"
    # Test enhanced processor
    enhanced_citations = extract_citations_enhanced(test_text, ProcessingConfig(enable_verification=False))
    logging.info(f"Enhanced processor found: {len(enhanced_citations)} citations")
    
    if enhanced_citations:
        citation = enhanced_citations[0]
        logging.info(f"Enhanced result:")
        logging.info(f"  Citation: {citation.citation}")
        logging.info(f"  Bluebook: {citation.bluebook_format}")
        logging.info(f"  Confidence: {citation.confidence:.2f}")
        logging.info(f"  Precedent: {citation.precedent_strength}")
    logging.info("[DEBUG] Finished test_comparison().")

if __name__ == "__main__":
    try:
        logging.info("[DEBUG] Starting main test script...")
        test_enhanced_processor()
        test_comparison()
        logging.info(f"\n✅ All tests completed successfully!")
        
    except Exception as e:
        logging.error(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc() 