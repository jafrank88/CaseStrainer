# Pipeline: Citations Extracted but Case Names/Years Missing

## Summary

When the UI shows "13 Cases Found" but "0 matched" and all cards show "N/A, Not Found" for case name and year, the break is **before** the API response: citations are present but `extracted_case_name` and `extracted_date` are never set (or stay N/A) in the pipeline.

## Flow (extraction → name/date → response)

1. **Stage 1 extraction**  
   `run_extract_citations(processor, text, context)` → `processor.process_text(text)`.

2. **Inside `process_text()` (UnifiedCitationProcessorV2)**  
   - **Unified path:** `_extract_citations_unified(text)`  
     - Step 5 sets `extracted_case_name` via `_extract_case_name_from_context()` and `extracted_date`; returns "N/A" when nothing is found.  
   - **Regex fallback:** If unified extraction throws or returns 0 citations, `citations = _extract_with_regex_enhanced(text)`.  
     - These `CitationResult` objects do **not** go through Step 5 (or Step 4b), so they have no `extracted_case_name`/`extracted_date` and no `name_likely_in_left_context` / `is_proprietary_only`.

3. **Enhancement loop (same method)**  
   For each citation it tries: Method 0 (name in citation text), then left-context (when `name_likely_in_left_context` is True), then master extractor.  
   If nothing is found, it sets `extracted_case_name = "N/A"`.  
   **Bug:** For regex-fallback citations, `name_likely_in_left_context` was never set, so reporter-only cites (e.g. "725 F.3d 651") did not get the left-context path and often ended up N/A.

4. **Pipeline after `process_text()`**  
   - `citations = extraction_result.get("citations", [])` — same `CitationResult` objects.  
   - Law-review filter, optional Stage 2 verification (same objects, preserves `extracted_case_name`/`extracted_date` when N/A), Stage 3 parallel (same list).  
   - `_format_response(citations, context)` → `cit.to_dict()` and safeguard so null/empty name/date become "N/A".

5. **Worker**  
   Normalizes citations to dicts and uses `setdefault("extracted_case_name", "N/A")`; it does not overwrite real values.

## Root cause (regex fallback path)

- When **unified extraction fails** (exception or 0 citations), the pipeline uses **regex-only** citations.
- Those citations **never run Step 4b** in `_extract_citations_unified` (where `name_likely_in_left_context` and `is_proprietary_only` are set).
- So in the enhancement loop, reporter-only citations (e.g. "725 F.3d 651", "2025 WL 1734066") had `name_likely_in_left_context == False` and did not use the left-context extractor; the master extractor often failed in dense text, so names stayed N/A.

## Fix applied

- **Set flags on regex-fallback citations**  
  In `process_text()`, after the try/except that may assign `citations = _extract_with_regex_enhanced(text)`, we now set for each citation (when missing or when `method == "regex_enhanced"`):
  - `is_proprietary_only = is_proprietary_only_citation(citation.citation)`
  - `name_likely_in_left_context = name_likely_in_left_context(citation.citation)`  
  So the enhancement loop uses the left-context path for reporter-only cites even when coming from regex fallback.

- **Diagnostic logging**  
  - `[NAME-DIAG] After Step 5 (name/date extraction): X/Y citations have non-N/A extracted_case_name` (in `_extract_citations_unified`).  
  - `[NAME-DIAG] After enhancement loop: X/Y citations have non-N/A extracted_case_name` (in `process_text`).  
  - `[NAME-DIAG] _format_response: X/Y citations have non-N/A extracted_case_name on CitationResult` (in `_format_response`).  

  If Step 5 shows 0 and enhancement shows 0, names were never found (or unified threw and regex path wasn’t finding names before the flag fix). If Step 5 or enhancement shows names but _format_response shows 0, something between enhancement and formatting would be dropping them (none found in current code).

## Files touched

- `src/unified_citation_processor_v2.py`: set `name_likely_in_left_context` / `is_proprietary_only` after regex fallback; log after Step 5 and after enhancement loop.
- `src/unified_processing_pipeline.py`: log at start of `_format_response` for citation object name counts.
