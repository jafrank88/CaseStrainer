---
description: Citation extraction testing process and commands
globs: scripts/run_extract_and_compare.py, scripts/compare_extraction_to_expected.py, scripts/_extract_pdf_to_json.py, tests/fixtures/*_expected.json
alwaysApply: false
---

# Extraction Testing Process

When working with citation extraction or comparison scripts, use this process.

## Commands

```bash
# Extract only (saves to JSON; subprocess to avoid OOM)
python scripts/run_extract_and_compare.py extract <pdf_path> <output.json>

# Compare only (lightweight, no extraction)
python scripts/run_extract_and_compare.py compare <expected.json> <actual.json>

# Both: extract then compare
python scripts/run_extract_and_compare.py both <pdf_path> <expected.json> [output.json]
```

## Key Paths

- **Entry point:** `scripts/run_extract_and_compare.py`
- **Extraction subprocess:** `scripts/_extract_pdf_to_json.py`
- **Comparison logic:** `scripts/compare_extraction_to_expected.py`
- **Expected fixtures:** `tests/fixtures/*_expected.json`

## Expected Fixture Format

```json
{
  "document_id": "short-id",
  "expected_clusters": [
    {
      "expected_case_name": "Case Name v. Defendant",
      "expected_citations": ["100 N.Y.2d 893", "100 NY2d 893"],
      "expected_year": "2003"
    }
  ]
}
```

## Full Documentation

See `docs/EXTRACTION_TESTING_PROCESS.md` for detailed steps, troubleshooting, and fixture format.
