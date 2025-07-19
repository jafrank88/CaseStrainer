#!/usr/bin/env python3
"""
Simple import diagnostic script
"""

logger.info("=== Import Diagnostic ===")

# Test core module
try:
    from case_name_extraction_core import extract_case_name_and_date
    logger.info("✅ Core module works")
except Exception as e:
    logger.error(f"❌ Core module error: {e}")

# Test integrated module
try:
    from legal_case_extractor_integrated import extract_cases_from_text
    logger.info("✅ Integration module works")
except Exception as e:
    logger.error(f"❌ Integration module error: {e}")

# Test enhanced module
try:
    from legal_case_extractor_enhanced import LegalCaseExtractorEnhanced
    logger.info("✅ Enhanced module works")
except Exception as e:
    logger.error(f"❌ Enhanced module error: {e}")

logger.info("=== Quick Test ===")

# Test actual extraction
try:
    test_text = "Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022)."
    test_citation = "200 Wn.2d 72"
    
    result = extract_case_name_and_date(test_text, test_citation)
    logger.info(f"✅ Extraction works: {result['case_name']} ({result['year']})")
except Exception as e:
    logger.error(f"❌ Extraction error: {e}")

logger.info("=== Done ===") 