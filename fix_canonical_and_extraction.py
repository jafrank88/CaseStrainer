#!/usr/bin/env python3
"""
Comprehensive fix for canonical case matching and case name extraction issues.
"""

import re
import logging
from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig
from src.case_name_extraction_core import extract_case_name_triple_comprehensive

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_canonical_matching():
    """Fix the canonical case matching logic to prioritize exact citation matches."""
    
    # Test the problematic citation
    test_citation = "200 Wn.2d 72"
    expected_case = "Convoyant, LLC v. DeepThink, LLC"
    
    print(f"=== FIXING CANONICAL MATCHING FOR: {test_citation} ===")
    
    # Create a test processor with debug mode
    config = ProcessingConfig(
        use_eyecite=False,
        use_regex=True,
        extract_case_names=True,
        extract_dates=True,
        enable_clustering=False,
        debug_mode=True
    )
    processor = UnifiedCitationProcessorV2(config)
    
    # Test the verification logic directly
    verify_result = processor._verify_with_courtlistener_search(
        citation=test_citation,
        extracted_case_name=expected_case,
        extracted_date="2022"
    )
    
    print(f"Verification result:")
    print(f"  Verified: {verify_result.get('verified')}")
    print(f"  Canonical name: {verify_result.get('canonical_name')}")
    print(f"  Expected: {expected_case}")
    
    if verify_result.get('canonical_name') != expected_case:
        print(f"  ✗ MISMATCH DETECTED!")
        
        # Let's examine the raw data to understand why
        raw_data = verify_result.get('raw')
        if raw_data:
            print(f"  Raw case name: {raw_data.get('caseName')}")
            print(f"  Raw citations: {raw_data.get('citation')}")
            print(f"  Raw court: {raw_data.get('court')}")
            print(f"  Raw date: {raw_data.get('dateFiled')}")
    
    return verify_result

def fix_case_name_extraction():
    """Fix the case name extraction logic to properly extract case names from text."""
    
    print(f"\n=== FIXING CASE NAME EXTRACTION ===")
    
    # Test text with known case names
    test_text = """
    A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)
    """
    
    test_cases = [
        ("200 Wn.2d 72", "Convoyant, LLC v. DeepThink, LLC"),
        ("171 Wn.2d 486", "Carlson v. Glob. Client Sols., LLC"),
        ("146 Wn.2d 1", "Dep't of Ecology v. Campbell & Gwinn, LLC")
    ]
    
    for citation, expected_case in test_cases:
        print(f"\n--- Testing extraction for: {citation} ---")
        print(f"Expected case: {expected_case}")
        
        # Test the comprehensive extraction function
        result = extract_case_name_triple_comprehensive(
            text=test_text,
            citation=citation,
            api_key=None,
            context_window=100
        )
        
        print(f"Extraction result:")
        print(f"  Extracted name: {result.get('extracted_name')}")
        print(f"  Case name: {result.get('case_name')}")
        print(f"  Method: {result.get('case_name_method')}")
        
        if result.get('extracted_name') == expected_case:
            print(f"  ✓ EXTRACTION SUCCESS!")
        else:
            print(f"  ✗ EXTRACTION FAILED!")
            print(f"    Expected: {expected_case}")
            print(f"    Got: {result.get('extracted_name')}")

def create_enhanced_extraction_fix():
    """Create an enhanced extraction function that properly handles case name extraction."""
    
    def enhanced_extract_case_name_from_text(text: str, citation: str) -> str:
        """
        Enhanced case name extraction that works with the current citation processing.
        """
        import re
        
        # Find the citation in the text
        citation_pos = text.find(citation)
        if citation_pos == -1:
            return ""
        
        # Get context before the citation (up to 200 characters)
        context_before = text[max(0, citation_pos - 200):citation_pos]
        
        # Enhanced case name patterns
        case_name_patterns = [
            # Standard case format: Name v. Name
            r'([A-Z][A-Za-z0-9&.,\'\\-]+(?:\s+[A-Za-z0-9&.,\'\\-]+)*\s+(?:v\.|vs\.|versus)\s+[A-Z][A-Za-z0-9&.,\'\\-]+(?:\s+[A-Za-z0-9&.,\'\\-]+)*)',
            # Department cases
            r'(Dep\'t\s+of\s+[A-Za-z\s,&\.]+\s+(?:v\.|vs\.|versus)\s+[A-Za-z\s,&\.]+)',
            # In re cases
            r'(In\s+re\s+[A-Za-z\s,&\.]+)',
            # Estate cases
            r'(Estate\s+of\s+[A-Za-z\s,&\.]+)',
        ]
        
        for pattern in case_name_patterns:
            matches = list(re.finditer(pattern, context_before, re.IGNORECASE))
            if matches:
                # Take the last (most recent) match
                match = matches[-1]
                case_name = match.group(1).strip()
                
                # Clean up the case name
                case_name = re.sub(r',\s*\d+\s+[A-Za-z.]+.*$', '', case_name)
                case_name = re.sub(r'\(\d{4}\)$', '', case_name)
                case_name = case_name.strip(' ,;')
                
                # Basic validation
                if len(case_name) > 5 and ' v. ' in case_name:
                    return case_name
        
        return ""
    
    return enhanced_extract_case_name_from_text

def test_enhanced_extraction():
    """Test the enhanced extraction function."""
    
    print(f"\n=== TESTING ENHANCED EXTRACTION ===")
    
    enhanced_extract = create_enhanced_extraction_fix()
    
    test_text = """
    A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)
    """
    
    test_cases = [
        ("200 Wn.2d 72", "Convoyant, LLC v. DeepThink, LLC"),
        ("171 Wn.2d 486", "Carlson v. Glob. Client Sols., LLC"),
        ("146 Wn.2d 1", "Dep't of Ecology v. Campbell & Gwinn, LLC")
    ]
    
    for citation, expected_case in test_cases:
        print(f"\n--- Testing enhanced extraction for: {citation} ---")
        
        extracted_case = enhanced_extract(test_text, citation)
        print(f"Extracted: {extracted_case}")
        print(f"Expected: {expected_case}")
        
        if extracted_case == expected_case:
            print(f"  ✓ SUCCESS!")
        else:
            print(f"  ✗ FAILED!")

def create_canonical_matching_fix():
    """Create a fix for the canonical matching logic."""
    
    def enhanced_verify_with_courtlistener_search(processor, citation: str, extracted_case_name: str = None, extracted_date: str = None, apply_state_filter: bool = True) -> dict:
        """
        Enhanced verification that prioritizes exact citation matches.
        """
        import requests
        from difflib import SequenceMatcher
        
        result = {
            "canonical_name": None,
            "canonical_date": None,
            "url": None,
            "verified": False,
            "raw": None,
            "source": None
        }
        
        if not processor.courtlistener_api_key:
            return result
            
        headers = {"Authorization": f"Token {processor.courtlistener_api_key}"}
        
        try:
            base_citation = processor._get_base_citation(citation)
            search_url = f"https://www.courtlistener.com/api/rest/v4/search/?q={base_citation}&format=json"
            resp = requests.get(search_url, headers=headers, timeout=10)
            
            if resp.status_code == 200:
                search_data = resp.json()
                results = search_data.get("results", [])
                
                # Apply state filtering
                if apply_state_filter:
                    expected_state = processor._infer_state_from_citation(citation)
                    if expected_state:
                        state_lower = expected_state.lower()
                        filtered = [
                            r for r in results
                            if state_lower in (r.get('court', '').lower() + r.get('jurisdiction', '').lower())
                        ]
                        if filtered:
                            results = filtered
                
                best = None
                best_score = 0
                
                for entry in results:
                    entry_citations = entry.get("citation", [])
                    entry_name = entry.get("caseName", "")
                    entry_date = entry.get("dateFiled", "")
                    
                    score = 0
                    match_details = []
                    
                    # PRIORITY 1: Exact citation match (highest priority)
                    for c in entry_citations:
                        normalized_citation = c.replace(",", "").replace(" ", "").lower()
                        normalized_base = base_citation.replace(",", "").replace(" ", "").lower()
                        
                        if normalized_base == normalized_citation:
                            score += 20  # Exact match gets highest score
                            match_details.append(f"exact_citation_match: {c}")
                            break
                        elif normalized_base in normalized_citation:
                            score += 15  # Contains the base citation
                            match_details.append(f"contains_citation: {c}")
                            break
                        elif processor._is_similar_citation(base_citation, c):
                            score += 10  # Similar citation
                            match_details.append(f"similar_citation: {c}")
                            break
                    
                    # PRIORITY 2: Case name similarity
                    if extracted_case_name and entry_name:
                        if extracted_case_name.lower() == entry_name.lower():
                            score += 10
                            match_details.append(f"exact_case_name_match")
                        elif extracted_case_name.lower() in entry_name.lower():
                            score += 8
                            match_details.append(f"case_name_contains")
                        elif any(word in entry_name.lower() for word in extracted_case_name.lower().split()):
                            score += 5
                            match_details.append(f"partial_case_name_match")
                        else:
                            similarity = SequenceMatcher(None, extracted_case_name.lower(), entry_name.lower()).ratio()
                            if similarity > 0.7:
                                score += int(similarity * 6)
                                match_details.append(f"fuzzy_match: {similarity:.2f}")
                    
                    # PRIORITY 3: Date matching
                    if extracted_date and entry_date:
                        if extracted_date in entry_date:
                            score += 3
                            match_details.append(f"date_match")
                        elif processor._is_similar_date(extracted_date, entry_date):
                            score += 2
                            match_details.append(f"similar_date")
                    
                    # PRIORITY 4: Court preference
                    if "washington" in entry.get('court', '').lower():
                        score += 2
                        match_details.append("washington_court")
                    
                    # Update best match
                    if score > best_score:
                        best_score = score
                        best = (entry, match_details)
                
                # Use a higher threshold for better accuracy
                if best and best_score >= 15:  # Increased threshold
                    entry, match_details = best
                    result["canonical_name"] = entry.get("caseName")
                    result["canonical_date"] = entry.get("dateFiled")
                    abs_url = entry.get("absolute_url")
                    if abs_url and abs_url.startswith("/"):
                        abs_url = "https://www.courtlistener.com" + abs_url
                    result["url"] = abs_url
                    result["verified"] = True
                    result["source"] = f"CourtListener (Enhanced) - {citation}"
                    result["raw"] = entry
                    
                    logger.info(f"Enhanced verification found: {citation} -> {result['canonical_name']} (score: {best_score})")
                    return result
                else:
                    logger.info(f"Enhanced verification: {citation} score {best_score} below threshold (15)")
                    
        except Exception as e:
            logger.warning(f"Enhanced verification failed for {citation}: {e}")
        
        return result
    
    return enhanced_verify_with_courtlistener_search

def test_enhanced_canonical_matching():
    """Test the enhanced canonical matching."""
    
    print(f"\n=== TESTING ENHANCED CANONICAL MATCHING ===")
    
    config = ProcessingConfig(debug_mode=True)
    processor = UnifiedCitationProcessorV2(config)
    enhanced_verify = create_canonical_matching_fix()
    
    test_cases = [
        ("200 Wn.2d 72", "Convoyant, LLC v. DeepThink, LLC", "2022"),
        ("171 Wn.2d 486", "Carlson v. Glob. Client Sols., LLC", "2011"),
        ("146 Wn.2d 1", "Dep't of Ecology v. Campbell & Gwinn, LLC", "2003")
    ]
    
    for citation, expected_case, expected_date in test_cases:
        print(f"\n--- Testing enhanced verification for: {citation} ---")
        
        result = enhanced_verify(processor, citation, expected_case, expected_date)
        
        print(f"Result:")
        print(f"  Verified: {result.get('verified')}")
        print(f"  Canonical name: {result.get('canonical_name')}")
        print(f"  Expected: {expected_case}")
        print(f"  Canonical date: {result.get('canonical_date')}")
        print(f"  Expected date: {expected_date}")
        
        if result.get('canonical_name') == expected_case:
            print(f"  ✓ CANONICAL MATCH SUCCESS!")
        else:
            print(f"  ✗ CANONICAL MATCH FAILED!")

if __name__ == "__main__":
    # Test the current issues
    fix_canonical_matching()
    fix_case_name_extraction()
    
    # Test the enhanced fixes
    test_enhanced_extraction()
    test_enhanced_canonical_matching() 