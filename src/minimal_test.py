#!/usr/bin/env python3

logger.info("=== Minimal Test ===")
logger.info("Python is working!")

# Test basic imports
import re
import json
import time
logger.info("Basic imports work!")

# Test dataclasses
from dataclasses import dataclass
logger.info("Dataclasses work!")

# Test typing
from typing import Dict, List, Optional
logger.info("Typing works!")

logger.info("=== Testing Core Module ===")

try:
    # Test the core module
    from case_name_extraction_core import extract_case_name_and_date
    logger.info("✅ Core module imported successfully!")
    
    # Test a simple extraction
    test_text = "Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022)."
    test_citation = "200 Wn.2d 72"
    
    result = extract_case_name_and_date(test_text, test_citation)
    logger.info(f"✅ Extraction successful: {result['case_name']} ({result['year']})")
    
except Exception as e:
    logger.error(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

logger.info("=== Testing Integration Module ===")

try:
    # Test the integration module
    from legal_case_extractor_integrated import extract_cases_from_text
    logger.info("✅ Integration module imported successfully!")
    
    # Test integrated extraction
    test_text = "Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022)."
    extractions = extract_cases_from_text(test_text)
    logger.info(f"✅ Integrated extraction successful: {len(extractions)} cases found")
    
except Exception as e:
    logger.error(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

logger.info("=== Test Complete ===")
