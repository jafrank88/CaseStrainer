"""
Diagnostic script to analyze case name extraction failures.

This script will:
1. Extract PDF text
2. Find citation positions
3. Show what context is available
4. Explain why extraction is failing
"""

import json
import re
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF."""
    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"
            return text
    except Exception as e:
        logger.error(f"Failed to extract PDF text: {e}")
        return None

def analyze_extraction_failure(text, citation_text, citation_start, citation_end, extracted_name, canonical_name):
    """Analyze why extraction failed for a specific citation."""
    logger.info(f"\n{'='*80}")
    logger.info(f"CITATION: {citation_text}")
    logger.info(f"Position: {citation_start}-{citation_end}")
    logger.info(f"Extracted: {extracted_name}")
    logger.info(f"Canonical: {canonical_name}")
    logger.info(f"{'='*80}")
    
    if extracted_name and extracted_name != "N/A":
        logger.info(f"✅ Extraction succeeded: '{extracted_name}'")
        if canonical_name and extracted_name.lower() != canonical_name.lower():
            logger.info(f"⚠️  But doesn't match canonical: '{canonical_name}'")
        return
    
    # Show context at different sizes
    for lookback in [50, 100, 180, 300, 500]:
        context_start = max(0, citation_start - lookback)
        context = text[context_start:citation_start]
        
        # Check if context contains " v. " pattern
        has_v = ' v. ' in context
        has_in_re = 'In re' in context or 'in re' in context
        
        logger.info(f"\nContext window: {lookback} chars")
        logger.info(f"Has ' v. ': {has_v}")
        logger.info(f"Has 'In re': {has_in_re}")
        logger.info(f"Context: ...{context[-150:]}")
        
        if has_v or has_in_re:
            # Try to extract manually
            v_match = re.search(r'([A-Z][a-zA-Z\.\&\s\-,]+)\s+v\.\s+([A-Z][a-zA-Z\.\&\s\-,]+)', context)
            in_re_match = re.search(r'In\s+re\s+([A-Z][a-zA-Z\.\&\s\-,]+)', context, re.IGNORECASE)
            
            if v_match:
                plaintiff = v_match.group(1).strip()
                defendant = v_match.group(2).strip()
                manual_extract = f"{plaintiff} v. {defendant}"
                logger.info(f"✅ Manual extraction possible: '{manual_extract}'")
                
                # Check why it might be rejected
                if 'ET AL' in manual_extract.upper():
                    logger.info(f"⚠️  Contains 'ET AL' - might be filtered as header")
                if re.search(r'Petitioner|Respondent|Appellant', manual_extract, re.IGNORECASE):
                    logger.info(f"⚠️  Contains role words - might be filtered as header")
                if re.search(r'\bNo\.\s*\d+', manual_extract):
                    logger.info(f"⚠️  Contains docket number - might be filtered as header")
                    
            elif in_re_match:
                manual_extract = f"In re {in_re_match.group(1).strip()}"
                logger.info(f"✅ Manual extraction possible: '{manual_extract}'")
            else:
                logger.info(f"❌ No clear case name pattern found")
        
        logger.info(f"-" * 80)
    
    # Check if text around citation contains the canonical name
    if canonical_name:
        window_start = max(0, citation_start - 500)
        window_end = min(len(text), citation_end + 500)
        window = text[window_start:window_end]
        
        if canonical_name in window:
            logger.info(f"\n✅ Canonical name '{canonical_name}' found in 500-char window!")
            # Find exact position
            pos = window.find(canonical_name)
            rel_pos = pos - (citation_start - window_start)
            logger.info(f"   Position relative to citation: {rel_pos} chars")
        else:
            # Try partial match
            canonical_parts = canonical_name.split(' v. ')
            if len(canonical_parts) == 2:
                plaintiff = canonical_parts[0]
                defendant = canonical_parts[1]
                
                if plaintiff in window:
                    logger.info(f"\n⚠️  Plaintiff '{plaintiff}' found in window")
                if defendant in window:
                    logger.info(f"\n⚠️  Defendant '{defendant}' found in window")
                if plaintiff not in window and defendant not in window:
                    logger.info(f"\n❌ Neither plaintiff nor defendant found in 500-char window")

def main():
    pdf_path = Path(r"D:\dev\casestrainer\1031351.pdf")
    json_path = Path(r"D:\dev\casestrainer\1031351_results.json")
    
    logger.info("Extracting text from PDF...")
    text = extract_text_from_pdf(pdf_path)
    
    if not text:
        logger.error("Failed to extract PDF text")
        return
    
    logger.info(f"PDF text length: {len(text)} chars")
    
    # Save text for inspection
    text_path = Path(r"D:\dev\casestrainer\1031351_text.txt")
    with open(text_path, 'w', encoding='utf-8') as f:
        f.write(text)
    logger.info(f"Saved text to: {text_path}")
    
    # Analyze specific failures from user's JSON
    failures = [
        {"citation": "161 Wn.2d 676", "extracted": "N/A", "canonical": "Erwin v. Cotter Health Centers, Inc."},
        {"citation": "167 P.3d 1112", "extracted": "N/A", "canonical": "Erwin v. Cotter Health Centers"},
        {"citation": "11 Wn.2d 288", "extracted": "N/A", "canonical": "Richardson v. Pacific Power & Light Co."},
        {"citation": "118 P.2d 985", "extracted": "N/A", "canonical": "Richardson v. Pacific Power & Light Co."},
        {"citation": "70 Wn.2d 893", "extracted": "N/A", "canonical": "Baffin Land Corp. v. MONTICELLO MOT. INN., INC."},
        {"citation": "425 P.2d 623", "extracted": "N/A", "canonical": "Baffin Land Corp. v. MONTICELLO MOT. INN., INC."},
        {"citation": "548 P.3d 226", "extracted": "N/A", "canonical": "Erickson v. Pharmacia LLC"},
        {"citation": "124 Wn.2d 205", "extracted": "N/A", "canonical": "Rice v. Dow Chemical Co."},
        {"citation": "124 F. Supp. 2d 46", "extracted": "N/A", "canonical": "Simon v. Philip Morris Inc."},
    ]
    
    for failure in failures:
        citation_text = failure["citation"]
        
        # Find citation in text
        pattern = re.escape(citation_text)
        matches = list(re.finditer(pattern, text))
        
        if not matches:
            logger.info(f"\n{'='*80}")
            logger.info(f"❌ Citation '{citation_text}' not found in PDF text")
            logger.info(f"{'='*80}")
            continue
        
        # Analyze first occurrence
        match = matches[0]
        citation_start = match.start()
        citation_end = match.end()
        
        analyze_extraction_failure(
            text,
            citation_text,
            citation_start,
            citation_end,
            failure["extracted"],
            failure["canonical"]
        )

if __name__ == "__main__":
    main()
