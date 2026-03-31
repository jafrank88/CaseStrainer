# Extraction Testing Process

This document describes how to test PDF citation extraction and compare results against expected (golden) fixtures.

## Overview

The testing workflow has two main steps:

1. **Extract** – Run the citation pipeline on a PDF and save output to JSON
2. **Compare** – Compare the extraction output to an expected fixture

Extraction runs in a subprocess to avoid OOM on large PDFs. Comparison is lightweight (JSON-only).

---

## Prerequisites

- Python environment with project dependencies installed
- PDF file(s) to test
- Expected fixture(s) in `tests/fixtures/` (see [Expected Fixture Format](#expected-fixture-format))

---

## Commands

### Extract only

Extracts citations from a PDF and saves to JSON. Use when you want to run extraction separately (e.g., to avoid OOM or to re-use output).

```bash
python scripts/run_extract_and_compare.py extract <pdf_path> <output.json>
```

**Examples:**
```bash
python scripts/run_extract_and_compare.py extract 1033397.pdf 1033397_actual.json
python scripts/run_extract_and_compare.py extract 75opn25-Decision.pdf 75opn25_actual.json
```

### Compare only

Compares actual extraction JSON to expected fixture. No PDF processing.

```bash
python scripts/run_extract_and_compare.py compare <expected.json> <actual.json>
```

**Examples:**
```bash
python scripts/run_extract_and_compare.py compare tests/fixtures/1033397_expected.json 1033397_actual.json
python scripts/run_extract_and_compare.py compare tests/fixtures/75opn25_expected.json 75opn25_actual.json
```

### Both (extract then compare)

Runs extraction in a subprocess, then compares the output to the expected fixture.

```bash
python scripts/run_extract_and_compare.py both <pdf_path> <expected.json> [output.json]
```

If `output.json` is omitted, it defaults to `{pdf_stem}_actual.json`.

**Examples:**
```bash
python scripts/run_extract_and_compare.py both 1033397.pdf tests/fixtures/1033397_expected.json
python scripts/run_extract_and_compare.py both 75opn25-Decision.pdf tests/fixtures/75opn25_expected.json 75opn25_actual.json
```

---

## Scripts Involved

| Script | Purpose |
|--------|---------|
| `scripts/run_extract_and_compare.py` | Entry point; orchestrates extract/compare |
| `scripts/_extract_pdf_to_json.py` | Subprocess: extracts text, runs pipeline, saves JSON |
| `scripts/compare_extraction_to_expected.py` | Compares actual vs expected clusters |

---

## Extraction Pipeline

1. **Text extraction** – `src.unified_text_extractor.extract_text_from_file_unified()`
2. **Citation processing** – `src.unified_processing_pipeline.process_citations_unified()` (async, with verification)
3. **Output** – JSON with `document_id`, `citations`, `clusters`

---

## Expected Fixture Format

Expected fixtures live in `tests/fixtures/` and use this structure:

```json
{
  "document_id": "short-id",
  "description": "Brief description of the document and key cases",
  "expected_clusters": [
    {
      "expected_case_name": "Case Name v. Defendant",
      "expected_citations": ["100 N.Y.2d 893", "100 NY2d 893"],
      "expected_year": "2003"
    }
  ]
}
```

- **document_id** – Short identifier (often PDF stem)
- **description** – Human-readable context
- **expected_clusters** – Array of clusters; each has:
  - `expected_case_name` – Canonical case name
  - `expected_citations` – Citation strings (include variants, e.g. `N.Y.2d` and `NY2d`)
  - `expected_year` – Year of decision

---

## Comparison Logic

The comparison script (`compare_extraction_to_expected.py`):

1. **Matches clusters** – By citation overlap (exact or containment)
2. **Normalizes** – Citations (whitespace, `N.Y.` → `NY`) and names (lowercase, trim)
3. **Reports** – Name match, year match, citation recall

### Metrics

- **Matched clusters** – Expected clusters that found a corresponding actual cluster
- **Name accuracy** – Clusters with matching case names
- **Year accuracy** – Clusters with matching years
- **Citation recall** – Expected citations found in actual / total expected

### Verdicts

- **PASS** – All clusters matched with correct name and year
- **PARTIAL** – All clusters matched but some name/year differences
- **FAIL** – One or more expected clusters not found

---

## Output Files

- **Actual JSON** – `{stem}_actual.json` (or path you specify)
- **Comparison JSON** – `{actual_stem}_comparison.json` (saved alongside actual)

---

## Current Fixtures

| Fixture | Document | Key Cases |
|---------|----------|-----------|
| `1033397_expected.json` | 1033397.pdf | State ex rel. Oriana House, Dow v. Caribou, Frederick v. City of Falls City |
| `75opn25_expected.json` | 75opn25-Decision.pdf | Levittown, Campaign for Fiscal Equity, Aristy-Farer, Leon, Paynter, NYCLU, IntegrateNYC |

---

## Troubleshooting

### Extraction takes a long time / times out

Large PDFs (e.g. 1033397) can take several minutes. Run `extract` separately and wait for completion before comparing.

### OOM during extraction

Extraction runs in a subprocess to limit memory. If OOM persists, try running `_extract_pdf_to_json.py` directly in a fresh process.

### Citation format mismatches

The comparison uses containment: `57 N.Y.2d 27` matches `57 NY2d 27`. Include both variants in `expected_citations` if extraction produces multiple formats.

### Name/year differences

Common causes:
- **Year** – Multiple citations with different years; clustering may pick the wrong one
- **Name** – Prior-citation bleed or wrong canonical name chosen
- **IntegrateNYC "Not Found"** – Cluster has no canonical name (e.g. Appellate Division below)

---

## Quick Reference

```bash
# Extract
python scripts/run_extract_and_compare.py extract <pdf> <out.json>

# Compare
python scripts/run_extract_and_compare.py compare <expected.json> <actual.json>

# Both
python scripts/run_extract_and_compare.py both <pdf> <expected.json> [out.json]
```
