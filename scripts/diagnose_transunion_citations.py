#!/usr/bin/env python3
"""
Diagnostic script for TransUnion v. Ramirez (20-297) citation extraction.
Step 1: Extract raw text from PDF and inspect
Step 2: Trace where citations are filtered/deduplicated
Step 3: Check eyecite patterns
"""
import os
import re
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PDF_PATH = r"D:\dev\casestrainer\20-297_4g25.pdf"


def step1_extract_and_inspect():
    """Extract text from PDF and inspect raw content for citation patterns."""
    print("=" * 60)
    print("STEP 1: PDF extraction and raw text inspection")
    print("=" * 60)
    
    if not os.path.exists(PDF_PATH):
        print(f"PDF not found: {PDF_PATH}")
        return None
    
    from src.unified_text_extractor import extract_text_from_file_unified
    from src.input_fetchers import preprocess_extracted_text
    
    text, method = extract_text_from_file_unified(PDF_PATH, verbose=True)
    print(f"\nExtracted {len(text)} chars using {method}")
    
    # Count citation-like patterns in raw text (before preprocessing)
    us_cite_raw = len(re.findall(r"\d+\s+U\.?\s*S\.?\s+\d+", text))
    us_cite_with_paren = len(re.findall(r"\d+\s+U\.?\s*S\.?\s+\d+[^.]*?\(\d{4}\)", text))
    print(f"Raw text: ~{us_cite_raw} matches for 'N U.S. N' pattern")
    print(f"Raw text: ~{us_cite_with_paren} matches for 'N U.S. N ... (YYYY)' pattern")
    
    # Show first 2000 chars (syllabus area)
    print("\n--- First 2500 chars (syllabus/header) ---")
    print(repr(text[:2500]))
    
    # Preprocess and re-count
    preprocessed = preprocess_extracted_text(text)
    print(f"\nAfter preprocessing: {len(preprocessed)} chars")
    us_cite_pre = len(re.findall(r"\d+\s+U\.?\s*S\.?\s+\d+", preprocessed))
    print(f"After preprocessing: ~{us_cite_pre} matches for 'N U.S. N' pattern")
    
    return preprocessed


def step2_trace_filtering(text):
    """Trace citation extraction and filtering pipeline."""
    print("\n" + "=" * 60)
    print("STEP 2: Trace citation filtering/deduplication")
    print("=" * 60)
    
    # Run eyecite directly (before any pipeline filtering)
    try:
        from eyecite import get_citations
        raw_citations = get_citations(text)
        print(f"\nEyecite raw extraction: {len(raw_citations)} citations")
        for i, c in enumerate(raw_citations[:15]):
            print(f"  {i+1}. {c}")
        if len(raw_citations) > 15:
            print(f"  ... and {len(raw_citations) - 15} more")
    except Exception as e:
        print(f"Eyecite error: {e}")
    
    # Run full pipeline and compare
    from src.unified_processing_pipeline import UnifiedProcessingPipeline
    import asyncio
    pipeline = UnifiedProcessingPipeline()
    result = asyncio.run(pipeline.process_citations(
        text=text,
        processing_mode="sync",
        enable_verification=False,  # Skip verification for speed
    ))
    
    citations = result.get("citations", [])
    clusters = result.get("clusters", [])
    print(f"\nPipeline output: {len(citations)} citations, {len(clusters)} clusters")
    print(f"Metadata: {result.get('metadata', {})}")
    
    # Check for filtering steps in pipeline
    print("\n--- Pipeline filtering check ---")
    print("If eyecite finds N citations but pipeline returns 5, filtering occurs in:")
    print("  - unified_citation_processor_v2 (extraction, grouping)")
    print("  - cluster_filter / contamination rejection")
    print("  - placeholder resolution (unresolved removed)")
    
    return result


def step3_eyecite_patterns(text):
    """Check if eyecite patterns match this document's citation style."""
    print("\n" + "=" * 60)
    print("STEP 3: Eyecite pattern coverage")
    print("=" * 60)
    
    # Sample citation formats from TransUnion (SCOTUS syllabus/opinion style)
    samples = [
        "200 U. S. 321, 337",
        "521 U. S. 811, 819-820",
        "504 U. S. 555, 560-561",
        "578 U. S. 330, 340",
        "497 U. S. 1, 13",
    ]
    
    from eyecite import get_citations
    for sample in samples:
        cites = get_citations(sample)
        status = "OK" if cites else "MISSED"
        print(f"  '{sample}' -> {len(cites)} citations [{status}]")
    
    # Check for patterns that might NOT be matched
    print("\n--- Scanning text for potential missed patterns ---")
    # SCOTUS often uses "Vol U. S. Page, Pinpoint" without parenthetical year
    pattern = r"(\d+)\s+U\.?\s*S\.?\s+(\d+)(?:\s*,\s*(\d+(?:-\d+)?))?"
    matches = list(re.finditer(pattern, text))
    print(f"Regex 'N U.S. N' or 'N U.S. N, N' found {len(matches)} matches")
    
    # Sample some that might be citations
    for m in matches[:10]:
        start = max(0, m.start() - 50)
        end = min(len(text), m.end() + 50)
        snippet = text[start:end]
        print(f"  ...{snippet}...")


if __name__ == "__main__":
    text = step1_extract_and_inspect()
    if text:
        step2_trace_filtering(text)
        step3_eyecite_patterns(text)
    print("\n" + "=" * 60)
    print("Diagnostic complete")
    print("=" * 60)
