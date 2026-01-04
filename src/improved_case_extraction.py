#!/usr/bin/env python3
"""
Improved case name extraction with reduced context noise
"""

import re
from typing import Dict, Optional, Any


def extract_case_name_clean(
    text: str,
    citation: Optional[str] = None,
    citation_start: Optional[int] = None,
    citation_end: Optional[int] = None,
    debug: bool = False,
) -> Dict[str, Any]:
    """
    Clean case name extraction that minimizes context noise.

    This function uses focused patterns to extract only the essential case name
    without capturing surrounding context text.
    """

    if not text or not citation:
        return {
            "case_name": "",
            "year": "",
            "confidence": 0.0,
            "method": "no_input",
            "debug_info": {"error": "No text or citation provided"},
        }

    # Get a focused context window around the citation
    if citation_start is not None and citation_end is not None:
        # Use position-based context window (smaller to reduce noise)
        context_start = max(0, citation_start - 200)  # Reduced from 800
        context_end = min(len(text), citation_end + 100)  # Reduced from 400
        context = text[context_start:context_end]
    else:
        # Find citation in text and get context
        citation_pos = text.find(citation)
        if citation_pos == -1:
            return {
                "case_name": "",
                "year": "",
                "confidence": 0.0,
                "method": "citation_not_found",
                "debug_info": {"error": "Citation not found in text"},
            }

        context_start = max(0, citation_pos - 200)
        context_end = min(len(text), citation_pos + len(citation) + 100)
        context = text[context_start:context_end]

    if debug:
        print(f"Context window: {context}")

    # Clean, focused patterns for case name extraction
    # Pattern 1: Standard "Party v. Party" (most common) - MORE RESTRICTIVE
    # Only match proper nouns and common legal words, avoid long descriptive text
    simple_pattern = r"([A-Z][a-z]*(?:\s+[A-Z][a-z]*){0,3}(?:\s+(?:[A-Z]{2,}|&|and))*)\s+v\.?\s+([A-Z][a-z]*(?:\s+[A-Z][a-z]*){0,3}(?:\s+(?:[A-Z]{2,}|&|and))*)"

    # Pattern 2: "In re" cases
    in_re_pattern = r"In\s+re\s+([A-Z][A-Z\s\'&\-,]{1,40})"

    # Pattern 3: "In the Matter of" cases
    matter_pattern = r"In\s+the\s+Matter\s+of\s+([A-Z][A-Z\s\'&\-,]{1,40})"

    # Pattern 4: Ex parte cases
    ex_parte_pattern = r"Ex\s+parte\s+([A-Z][a-zA-Z\s\'&\-,]{1,40})"

    # Try patterns in order of specificity
    case_name = ""
    method_used = ""

    # Try to find case name BEFORE the citation (most common scenario)
    citation_in_context = context.find(citation)
    if citation_in_context == -1:
        citation_in_context = len(context) // 2  # Fallback to middle

    # Look for patterns before the citation
    before_citation = context[:citation_in_context]

    # Pattern 1: Standard v. cases
    matches = re.findall(simple_pattern, before_citation)
    if matches:
        # Use the closest match to the citation
        closest_match = matches[-1]  # Last match is closest to citation
        case_name = f"{closest_match[0].strip()} v. {closest_match[1].strip()}"
        method_used = "standard_v_pattern"

    # Pattern 2: In re cases
    if not case_name:
        matches = re.findall(in_re_pattern, before_citation)
        if matches:
            case_name = f"In re {matches[-1].strip()}"
            method_used = "in_re_pattern"

    # Pattern 3: Matter cases
    if not case_name:
        matches = re.findall(matter_pattern, before_citation)
        if matches:
            case_name = f"In the Matter of {matches[-1].strip()}"
            method_used = "matter_pattern"

    # Pattern 4: Ex parte cases
    if not case_name:
        matches = re.findall(ex_parte_pattern, before_citation)
        if matches:
            case_name = f"Ex parte {matches[-1].strip()}"
            method_used = "ex_parte_pattern"

    # Extract year from citation or context
    year_pattern = r"\((19|20)\d{2}\)"
    year_matches = re.findall(year_pattern, citation or context)
    year = year_matches[0] if year_matches else ""

    # Clean up the case name
    if case_name:
        # Remove trailing punctuation and extra spaces
        case_name = re.sub(r"[,;\s]+$", "", case_name).strip()
        case_name = re.sub(r"\s+", " ", case_name)

        # Ensure it contains "v." or is a special case type
        if not any(indicator in case_name.lower() for indicator in ["v.", "in re", "in the matter of", "ex parte"]):
            case_name = ""  # Reject if it doesn't look like a case name

    confidence = 0.8 if case_name else 0.0

    if debug:
        print(f"Extracted case name: '{case_name}'")
        print(f"Method used: {method_used}")
        print(f"Year: {year}")

    return {
        "case_name": case_name,
        "year": year,
        "confidence": confidence,
        "method": method_used or "no_match",
        "debug_info": {
            "context_length": len(context),
            "citation_in_context": citation_in_context,
            "before_citation_length": len(before_citation),
        },
    }


# Test the function with the problematic text
if __name__ == "__main__":
    test_text = """
    IN THE COURT OF APPEALS OF THE STATE OF WASHINGTON
    DIVISION II
    
    STATE OF WASHINGTON,
        Respondent,
    v.
    JOHN DOE,
        Appellant.
    
    No. 59366-1-II
    UNPUBLISHED OPINION
    
    The court considers the precedent set in Smith v. Jones, 123 Wn.2d 456 (1998), where 
    the appellate court held that statutory interpretation requires careful analysis of 
    legislative intent. Similarly, in Johnson v. Washington State Dept., 456 P.3d 789 (2020),
    the court addressed administrative law principles.
    
    Furthermore, the case of Brown v. City of Seattle, 789 Wn. App. 234 (2015), established
    important guidelines for municipal liability. The court also referenced the earlier 
    decision in Anderson v. Clark, 312 P.2d 123 (1957), which remains good law.
    
    The appellant relies on the reasoning from Martinez v. County of Pierce, 567 P.3d 890 (2022),
    while the respondent cites Wilson v. State, 234 Wn.2d 567 (2010) and Taylor v. Federal Way, 
    890 P.3d 345 (2019) as controlling authority.
    """

    citations = [
        "123 Wn.2d 456 (1998)",
        "456 P.3d 789 (2020)",
        "789 Wn. App. 234 (2015)",
        "312 P.2d 123 (1957)",
        "567 P.3d 890 (2022)",
        "234 Wn.2d 567 (2010)",
        "890 P.3d 345 (2019)",
    ]

    print("🧪 Testing improved case name extraction:")
    print("=" * 80)

    for citation in citations:
        print(f"\n📋 Citation: {citation}")
        result = extract_case_name_clean(test_text, citation, debug=True)
        print(f"✅ Result: '{result['case_name']}' ({result['year']}) - {result['method']}")
        print(f"📊 Confidence: {result['confidence']}")
