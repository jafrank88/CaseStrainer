#!/usr/bin/env python3
"""
Debug script to test complex citation processing.
"""

import sys
import os
import logging
from typing import Any

# Set up logging
logger = logging.getLogger(__name__)

# Add the parent directory to the path so we can import from src
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Try to import the modules, with fallbacks if they don't exist
try:
    from .enhanced_multi_source_verifier import EnhancedMultiSourceVerifier as ImportedVerifier
    EnhancedMultiSourceVerifier = ImportedVerifier  # type: ignore
except ImportError:
    logger.warning("enhanced_multi_source_verifier module not found - using fallback")
    class EnhancedMultiSourceVerifier:
        def __init__(self):
            pass

# Fallback for complex citation processing since the module doesn't exist
def process_text_with_complex_citations(text: str, verifier: Any) -> list:
    """Fallback function for complex citation processing."""
    logger.warning("complex_citation_integration module not available - using fallback")
    return [{"error": "complex_citation_integration module not available"}]

ComplexCitationIntegrator = None

def test_complex_citation():
    """Test the complex citation processing."""
    
    # Initialize the verifier
    verifier = EnhancedMultiSourceVerifier()
    
    # Use the provided sample text
    test_text = (
        "Zink filed her first appeal after the trial court granted summary judgment to "
        "the Does. While the appeal was pending, this court decided John Doe A v. "
        "Washington State Patrol, which rejected a PRA exemption claim for sex offender "
        "registration records that was materially identical to one of the Does' claims in this "
        "case. 185 Wn.2d 363, 374 P.3d 63 (2016). Thus, following John Doe A, the Court "
        "of Appeals here reversed in part and held 'that the registration records must be "
        "released.' John Doe P v. Thurston County, 199 Wn. App. 280, 283, 399 P.3d 1195 "
        "(2017) (Doe I), modified on other grounds on remand, No. 48000-0-II (Wash. Ct. "
        "App. Oct. 2, 2018) (Doe II) (unpublished), "
    )
    
    logger.info(f"Testing complex citation in sample text:")
    logger.info("=" * 60)
    logger.info(test_text)
    logger.info("=" * 60)
    
    # Process with the full pipeline
    logger.info("\nProcessing with full pipeline:")
    logger.info("-" * 40)
    
    results = process_text_with_complex_citations(test_text, verifier)
    
    for i, result in enumerate(results):
        logger.info(f"\nResult {i+1}:")
        logger.info(f"  Citation: {result.get('citation')}")
        logger.info(f"  Verified: {result.get('verified')}")
        logger.info(f"  Case name: {result.get('case_name')}")
        logger.info(f"  Canonical date: {result.get('canonical_date')}")
        logger.info(f"  Is parallel: {result.get('is_parallel_citation')}")
        logger.info(f"  Primary citation: {result.get('primary_citation')}")
        logger.error(f"  Error: {result.get('error')}")
        logger.info(f"  Context: {result.get('context')}")
        logger.info(f"  Complex metadata: {result.get('complex_metadata')}")

if __name__ == "__main__":
    test_complex_citation() 