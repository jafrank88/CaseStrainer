#!/usr/bin/env python3
"""
Test EnhancedMultiSourceVerifier with Washington citation variants
"""

import sys
import os
import logging
import json

# Ensure src is in the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

# from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier  # Module does not exist

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # verifier = EnhancedMultiSourceVerifier() # Module does not exist
    
    # Test citation and variants
    target_citation = "199 Wash. App. 280"
    citation_variants = [
        "199 Wash. App. 280",
        "199 Wn. App. 280",
        "199 Washington App. 280",
        "199 Wn App 280",
        "199 Wash App 280"
    ]
    
    print("=" * 80)
    print("TESTING ENHANCED MULTISOURCE VERIFIER FOR WASHINGTON CITATIONS")
    print("=" * 80)
    print(f"Target citation: {target_citation}")
    print()
    
    for variant in citation_variants:
        print(f"\nVerifying variant: {variant}")
        # result = verifier.verify_citation_unified_workflow(variant, use_cache=False, use_database=False, use_api=True, force_refresh=True) # Module does not exist
        print(json.dumps(result, indent=2, default=str)) # Module does not exist
        print("-" * 60)
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("If none of the variants are verified, check normalization and API logs.")

if __name__ == "__main__":
    main() 