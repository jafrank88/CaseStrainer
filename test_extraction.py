import re
import sys
import logging

# Set up logging to show debug output
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def extract_case_name(text, citation_text, start, end):
    """Extract case name from text around a citation."""
    logger.info(f"\n{'='*80}")
    logger.info(f"Extracting case name for: {citation_text}")
    
    # Show context around the citation
    context_window = 100
    context_start = max(0, start - context_window)
    context_end = min(len(text), end + context_window)
    
    before = text[context_start:start]
    after = text[end:context_end]
    
    logger.debug(f"Context before: ...{before}")
    logger.debug(f"Citation: {citation_text}")
    logger.debug(f"Context after: {after}...")
    
    # Try different patterns to extract case name
    patterns = [
        # Pattern 1: Case name followed by comma, then citation
        r'([A-Z][^.!?]*?)\s*\b(?:v\.|vs\.|v\s|in\s+re\b|ex\s+rel\.|ex\s+parte\b)[^.!?]*?' + re.escape(citation_text),
        # Pattern 2: In re/Ex parte at start of sentence
        r'(?:In\s+re|Ex\s+parte|Ex\s+rel\.)\s+([A-Z][^.!?]*?)(?=\s*\d|\s*v\.|\s*vs\.|\s*\n|\s*$)',
        # Pattern 3: Look for v. or v in the previous sentence
        r'([A-Z][^.!?]*?\b(?:v\.?|vs\.?|in\s+re|ex\s+rel\.|ex\s+parte)\b[^.!?]*?)[.!?](?:\s+[A-Z]|\s*\n|\s*$)',
    ]
    
    for i, pattern in enumerate(patterns, 1):
        logger.debug(f"\nTrying pattern {i}: {pattern}")
        match = re.search(pattern, f"{before} {citation_text} {after}", re.IGNORECASE | re.DOTALL)
        if match:
            case_name = match.group(1).strip()
            logger.info(f"✅ Found match with pattern {i}: '{case_name}'")
            return case_name
    
    logger.warning("❌ No case name found")
    return None

def main():
    test_text = """We review statutory interpretation de novo. DeSean v. Sanger, 2 Wn. 3d 329, 334-35, 536 P.3d 191 (2023). 
    "The goal of statutory interpretation is to give effect to the legislature's intentions." DeSean, 2 Wn.3d at 335. 
    In determining the plain meaning of a statute, we look to the text of the statute, as well as its No. 87675-9-I/14 14 
    broader context and the statutory scheme as a whole. State v. Ervin, 169 Wn.2d 815, 820, 239 P.3d 354 (2010). 
    Only if the plain text is susceptible to more than one interpretation do we turn to statutory construction, 
    legislative history, and relevant case law to determine legislative intent. Ervin, 169 Wn.2d at 820."""
    
    # Test cases with their positions in the text
    test_cases = [
        {"text": "2 Wn. 3d 329, 334-35, 536 P.3d 191 (2023)", "start": 50, "end": 85},
        {"text": "DeSean, 2 Wn.3d at 335", "start": 180, "end": 202},
        {"text": "169 Wn.2d 815, 820, 239 P.3d 354 (2010)", "start": 320, "end": 357},
        {"text": "Ervin, 169 Wn.2d at 820", "start": 512, "end": 535}
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"TEST CASE {i}: {case['text']}")
        print("-" * 80)
        
        case_name = extract_case_name(
            test_text,
            case['text'],
            case['start'],
            case['end']
        )
        
        print(f"\nRESULT: {case_name}")
        print("=" * 80)

if __name__ == "__main__":
    main()
