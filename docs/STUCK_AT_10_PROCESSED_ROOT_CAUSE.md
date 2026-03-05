# Root cause: Pipeline "stuck at 10 processed"

## What happened

The citation pipeline appeared to hang with progress stuck at "10 processed" (or "10%") for long periods (minutes to 15+ minutes) when processing larger PDFs (e.g. ~64k characters).

## Root cause

The job was **not** stuck in verification or in the batch API loop. It was blocked **before** any verification batches ran, in the **full-document citation normalization** step inside `_extract_citations_unified` (`UnifiedCitationProcessorV2`, `unified_citation_processor_v2.py`).

1. **Where:** Before extraction (regex + eyecite), the code runs `_normalize_citation_comprehensive()` on the **entire document text** to fix PDF artifacts (e.g. lost commas: `81 91233 P.3d` → `81 91, 233 P.3d`).

2. **Why it blocked:** That function is regex-heavy and CPU-bound. It was designed for normalizing **single citation strings**, not full documents. On a ~64k character document it could take **15+ minutes**, blocking the pipeline on a single thread.

3. **Why the UI said "10 processed":** The "10 processed" (or "10%") value came from an earlier progress update (or cached state), not from the verification batch loop. The job never reached the verification phase for most citations because it was still stuck in the normalization step.

## Why it got slow (O(n²) behavior)

Two things in `_normalize_citation_comprehensive` scaled poorly on long text:

1. **Step 0a – while-loop over full document:** The code repeatedly did `re.sub(…, normalized)` on the whole string until no change. Each run only fixed one "digit space digit" pair before a reporter, so for long runs (e.g. "81 91 233 P.3d") it could take O(run length) iterations, each scanning the whole document → **O(n²)**.
2. **Case C – unbounded `(.*)` prefix:** The regex used `(.*)` before the reporter series. That caused **catastrophic backtracking** on long strings: the engine tries many ways to split the string, so one `re.sub` could be O(n²) on a 64k document.

## How we fixed it

- **0a single-pass:** Step 0a now uses one regex that matches a full run of space-separated digits before a reporter, and a replacement that turns all internal spaces in that run into `", "` in one go → **O(n)**.
- **Case C bounded prefix:** The Case C pattern no longer uses `(.*)`; it uses a bounded prefix `.{0,2000}?` so backtracking is limited → **O(n)** per rule.
- After these changes, full-document normalization runs for all document lengths again (no 45k skip or timeout).

## How to avoid this in the future

1. **Avoid O(n²) when normalizing full document text:**
   - Do **not** use a `while True` loop that does one `re.sub` over the full string per iteration (e.g. fixing one digit-pair at a time). Use a single-pass pattern that matches the whole run and fix it in one replacement.
   - Do **not** use unbounded `(.*)` (or similar) at the start of a regex that runs over long text—it can cause catastrophic backtracking. Use a bounded prefix (e.g. `.{0,2000}?`) or a non-greedy, constrained pattern.

2. **Prefer per-citation normalization** when possible: applying normalization to each extracted citation string is O(citations × citation_length) instead of O(document_length × rules).

3. **When debugging "stuck" jobs:** Check worker logs for `[UNIFIED_EXTRACTION]` and `[BATCH]`. If you see "Text normalized" but never "Step 1: Enhanced regex extraction", the hang is in full-document normalization, not in verification.
