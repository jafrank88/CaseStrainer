# Fallback Verification Flow When Citation-Lookup Fails

This chart shows the verification checks applied when CourtListener citation-lookup returns no match or fails.

---

## Single-Citation Flow (`verify_citation`)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 1. CACHE                                                                        │
│    Check verification cache → HIT → return cached result                         │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │ MISS
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 2. KNOWN FEDERAL TABLE                                                           │
│    Exact match in KNOWN_FEDERAL_CITATIONS → return known_federal                 │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │ NOT FOUND
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 3. KNOWN SLIP TABLE                                                              │
│    Volume+year + name match in KNOWN_SLIP_CITATIONS → return known_slip         │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │ NOT FOUND
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 4. VALIDATION                                                                   │
│    is_citation_likely_valid() → FAIL → return "Invalid citation format"         │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │ PASS
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 5. COURTLISTENER LOOKUP (primary)                                               │
│    CourtListener citation-lookup API → verified → validate year → return         │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │ NOT VERIFIED
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 6. COURTLISTENER SEARCH FALLBACK                                                 │
│    cl_search_fallback() – see CL Search Strategies below                         │
│    → verified → _passes_two_point_gate() → return                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │ NOT VERIFIED
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 7. WEB FALLBACK (FallbackVerifier)                                               │
│    Sources (by citation type):                                                   │
│    • Google Scholar (always first)                                                │
│    • Supreme Court: FindLaw, Cornell LII, Justia, OpenJurist                      │
│    • Federal: FindLaw, Justia, Cornell LII, OpenJurist                           │
│    • WL-only + weak name: Google Scholar only                                     │
│    → verified → _passes_two_point_gate() → return                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │ NOT VERIFIED
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 8. NAME+DATE-ONLY (last resort)                                                  │
│    Requires: case name (with "v" or 1–4 word party) + year                        │
│    Sources: Google Scholar, FindLaw                                               │
│    Query: "{name} {year}"                                                         │
│    → verified → return as possible_match                                          │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │ NOT VERIFIED
                                        ▼
                              "All verification methods failed"
```

---

## CourtListener Search Fallback Strategies (`cl_search_fallback`)

When citation-lookup returns 0 clusters, these strategies run in order:

| # | Strategy | When | Description |
|---|----------|------|-------------|
| **-1** | PACER Dockets API | Citation has docket number | Direct lookup by `docket_number` (+ optional court filter) |
| **0** | Exact citation search | WL/LEXIS/docket or reporter cite | Free-text search: U.S. reporter cite, cleaned citation, or citation+name |
| **0r** | Docket type search | Same as 0, type=o failed | Search `type=r` (dockets) with citation text |
| **0.5** | Name + date | Case name + year, name not weak | Fielded: `caseName:"..." AND dateFiled:[YYYY-2 TO YYYY+2]` |
| **1** | Opinion search | Case name present | `caseName:"..." AND dateFiled:[year±1]` |
| **1.5** | Keyword search | Strategy 1 failed | Content words from name + date filter |
| **2** | Freetext search | Strategy 1.5 failed | `{case_name} {citation}` |
| **3** | Docket search | Strategy 2 failed | First-party + second-party quoted, `type=r` |

### CourtListener Search API – `status` field

Valid entries for the `status` filter (opinion clusters):

| Value | Description |
|-------|--------------|
| `published` | Published opinions (default when `type=o`) |
| `unpublished` | Unpublished opinions |
| `errata` | Errata |
| `separate` | Separate opinions (concurrences, dissents) |
| `in-chambers` | In-chambers opinions |
| `relating-to` | Relating-to orders |
| `unknown` | Unknown status |

By default, case law search (`type=o`) returns only published results. To include unpublished and other statuses, explicitly request them via the `status` parameter.

---

## Batch Flow (`verify_citations_batch`)

Used in Phase 4.75 before clustering. CourtListener batch API first; then per-citation fallback for unverified:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ BATCH: CourtListener citation-lookup (text-based batch API)                      │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                    For each unverified (or verified but no URL):
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ KNOWN FEDERAL (deterministic rescue)                                             │
│ Same as single-citation flow                                                     │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │ NOT FOUND
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ WL/Lexis + name+date: Early name+date-only path (proprietary citations)          │
│ FallbackVerifier.verify_name_and_date_only() → possible_match                     │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │ (or skip if not proprietary)
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ Step A: CL Search Fallback                                                       │
│ cl_search_fallback() – same strategies as single-citation                       │
│ → _passes_two_point_gate()                                                       │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │ NOT VERIFIED
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ Step B: Web Fallback (FallbackVerifier.verify)                                   │
│ Skipped if: weak/no case name (except WL/Lexis citation-first Scholar lane)      │
│ Same sources as single-citation flow                                            │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Batch limits:**
- `max_fallback_citations` (default 100) – cap on fallback attempts
- `fallback_time_budget_seconds` (default 300) – total wall-clock budget
- Noisy citations (e.g. "TABLE OF AUTHORITIES", "Cases-Continued") are skipped

---

## Two-Point Gate (`_passes_two_point_gate`)

Applied to CL search and web fallback results before accepting:

- **Citation core match** – submitted citation core equals candidate citation core, OR
- **Strong name + year match** – case name has "v", ≥3 tokens, overlap ≥0.75 (CL) or ≥0.5 (CourtListener sources), and year within tolerance, OR
- **First-party surname + year** – first party’s surname in canonical name and year matches

If extraction metadata is weak (no strong name, no year), gate does not block.

---

## Sources Summary

| Source | Used In | Notes |
|--------|---------|-------|
| Cache | Single, Batch | In-memory / persistent cache |
| Known Federal | Single, Batch | Static table for misresolved federal cites |
| Known Slip | Single | Volume+year + name match |
| CourtListener Lookup | Single, Batch | Primary API |
| CourtListener Search | Single, Batch | Multiple strategies (see table above) |
| Google Scholar | Fallback | First in web fallback |
| FindLaw | Fallback | Supreme/federal |
| Cornell LII | Fallback | Supreme/federal |
| Justia | Fallback | Supreme/federal |
| OpenJurist | Fallback | Federal |

---

## File References

- `src/verification/master.py` – `UnifiedVerificationMaster`, `verify_citation`, `verify_citations_batch`
- `src/verification/fallback.py` – `FallbackVerifier`, `_select_sources`, `verify_name_and_date_only`
- `src/verification/cl_search_fallback.py` – `cl_search_fallback`, PACER, exact/name-date/opinion/docket strategies
- `src/verification/known_citations.py` – `KNOWN_FEDERAL_CITATIONS`, `KNOWN_SLIP_CITATIONS`
- `src/verification/batch.py` – `BatchVerifier` (CourtListener batch API)
