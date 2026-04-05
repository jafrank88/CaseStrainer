# CaseStrainer Corpus Bug Report
**Corpus:** 25 NAAG Amicus briefs (`downloaded_briefs/naag_amicus/`)  
**Run date:** 2026-04-03  
**Total citations extracted:** ~1,725 (avg 69/doc)  
**Total clusters:** ~728 (avg 29/doc)  
**Total flagged issues:** 144

---

## Issue Summary

| Type | Count | % | Severity |
|---|---|---|---|
| `short_ecn_on_long_citation` | 82 | 57% | HIGH |
| `year_mismatch` | 41 | 28% | MEDIUM |
| `name_mismatch_verified` | 12 | 8% | HIGH |
| `oversized_cluster` | 4 | 3% | MEDIUM |
| `multi_canonical_cluster` | 3 | 2% | MEDIUM |
| `duplicate_cluster_id` | 2 | 1% | LOW |

---

## Bug A — `short_ecn_on_long_citation` (82 instances) — HIGHEST PRIORITY

### What it means
A citation has a case-name prefix in `citation.citation` (eyecite extracted it), but
`extracted_case_name` is `N/A` or a 2–3 word fragment.  
The submitted display ends up blank or shows only a fragment.

### Sub-patterns

**A1 · "In re / Antitrust Litig." names (most frequent)**  
Eyecite correctly extracts the full citation text including the case name prefix, but the
prefix has no `" v. "` and no `"In re"` (eyecite strips it), so `_is_bad_submitted_name`
marks it as lacking "case structure" and downstream logic may reject it.

Examples across multiple docs:
```
'Brand Name Prescription Drugs Antitrust Litig., 123 F.3d 599'          ecn='N/A'
'Railway Industry Employee No-Poach Antitrust Litigation, 395 ...'       ecn='N/A'
'Ciprofloxacin Hydrochloride Antitrust Litig., 544 F.3d 1323'           ecn='N/A'
'New Motor Vehicles Canadian Exp. Antitrust Litig., 522 F.3d ...'       ecn='N/A'
'Intel Corp. Microprocessor Antitrust Litig., 496 F. Supp. 2d'          ecn='N/A'
'Lamictal Direct Purchaser Antitrust Litig., 18 F. Supp. 3d'            ecn='N/A'
'Minolta Camera Products Antitrust Litigation, 668 F. Supp.'            ecn='N/A'
'Cipro I & II No. 198616, 2015 WL 2125291'                              ecn='Cipro I & II'
```

**Root cause:** `_is_bad_submitted_name` requires `_has_case_structure = True` (contains
`v.` or `In re`) before accepting a name. Antitrust Litig. names stripped of "In re" fail
this check and then fall through to `is_citation_fragment_not_case_name`, which may
further reject them.

**Proposed fix (cluster_display_utils.py line 92):**
```python
_has_case_structure = bool(
    re.search(r"\bv\.\s", s)
    or re.search(r"\b(?:In\s+re|Ex\s+parte|In\s+the\s+Matter\s+of|Estate\s+of)\b", s, re.IGNORECASE)
    or re.search(r"\bAntitrust\s+Litig(?:ation)?\b|\bLitig\.\s*$", s, re.IGNORECASE)
)
```

---

**A2 · "Amici Curiae" prefix contamination**

Eyecite citation text starts with the brief title line:
```
'Amici Curiae Supporting Petitioners, La. Wholesale Drug Co. ...'       ecn='N/A'
'Amici Curiae, Ark. Carpenters Health Welfare Fund v. Bayer A.'         ecn='N/A'
```
The "Amici Curiae" is not stripped, so `_extract_inline_case_name` returns `None`
(prefix has `>8 words` after "Amici Curiae" is treated as part of the name).

**Proposed fix (`_extract_inline_case_name` signal phrases, ucp_v2.py ~line 4381):**
```python
r'|Amici\s+Curiae\s+(?:of\s+)?(?:[\w\s]+,\s+)?'
r'|Brief\s+(?:of\s+)?(?:Amici?\s+Curiae\s+)?(?:[\w\s]+,\s+)?'
```

---

**A3 · "Cited Authorities Page" prefix**

```
'Cited Authorities Page Laurel Sand v. CSX, 924 F.2d 539 (ca4)'        ecn='N/A'
```
The existing `Cases-Continued: Page` strip doesn't cover `Cited Authorities Page`.

**Proposed fix:** Extend the TOA header regex to also match `Cited Authorities Page`.

---

**A4 · Truncated plaintiff on abbreviated names**

Eyecite extracts from "Nw., Inc. v. EEOC" → the full name is "Northwest Airlines, Inc.";
from "Nemours & Co., 351 U.S. 377" → full name is "E.I. du Pont de Nemours & Co."

```
'Nw., Inc. v. EEOC, 446 U.S. 318 (scotus 1980)'            ecn='N/A'   (16_Mississippi)
'Nemours & Co., 351 U.S. 377 (scotus 1956)'                 ecn='Nemours & Co'
'Assocs. v. Garlock, Inc., 721 F.2d 1540 (cafc 1983)'       ecn='N/A'   (22_K-Dur)
'E. Scientific Co. v. Wild Heerbrugg Instruments, Inc.'      ecn='N/A'   (09, 10)
```

These are cases where the TOA entry or body-text citation starts at a mid-name
abbreviation. Eyecite parses only from the abbreviation forward. The inline extractor
faithfully returns the truncated plaintiff.

**Long-term fix:** Extend `_recover_truncated_name_from_context` to handle single-token
abbreviation plaintiffs (e.g., `Nw.`, `Assocs.`, `E.`) by looking back further in
context and accepting non-entity-suffix starting words.

---

**A5 · Administrative reporters (FCC, FTC, F.T.C., C.P.U.C.) not in `_INLINE_REPORTER_RE`**

```
'21 F.C.C.2d 190 (1970)'                                    ecn='N/A'   (25_Verizon)
'Specialized Common Carriers, 29 F.C.C.2d 870 (1977)'       ecn='N/A'   (25_Verizon)
'Local Exchange Carriers, 33 C.P.U.C.2d 43'                 ecn='N/A'   (25_Verizon)
'Polygram Holding, Inc., 136 F.T.C. 310 (2015)'             ecn='N/A'   (06_Impax)
```

The `_INLINE_REPORTER_RE` used in `_extract_inline_case_name` doesn't include
`F.C.C.`, `F.T.C.`, `C.P.U.C.`, `N.L.R.B.`, etc., so these citations aren't scanned
for an inline prefix at all.

**Proposed fix:** Add administrative reporters to `_INLINE_REPORTER_RE`.

---

## Bug B — `year_mismatch` (41 instances)

### Sub-patterns

**B1 · Wrong CourtListener verification → extreme year gap (10+ cases)**

The name similarity matcher selected a wrong CourtListener result, and the canonical
year is wildly off:

| Doc | Cluster | Extracted | Canonical | Gap |
|---|---|---|---|---|
| 01_Tri-City | cluster_15 | 2008 | 1890 | 118 yr |
| 01_Tri-City | cluster_19 | 1905 | 2023 | 118 yr |
| 13_NC-Dental | cluster_7 | 1976 | 1890 | 86 yr |
| 15_NC-Dental-Cert | cluster_15 | 1999 | 1845 | 154 yr |
| 15_NC-Dental-Cert | c0_yr_1 | 1960 | 2025 | **future!** |
| 22_K-Dur | cluster_13 | 1983 | 1892 | 91 yr |
| 21_OK-v-BP | cluster_15 | 1983 | 1887 | 96 yr |

Note `canonical_year=2025` is a future date — invalid CourtListener data.

**Proposed fix:** In post-verification, hard-reject any `canonical_date` that is
`> current_year` or `< 1780` (pre-U.S. legal system). Also reject verifications where
`abs(canonical_year - extracted_year) > 30` UNLESS `names_are_same_case()` returns True
(the name similarity check should have prevented this, suggesting the threshold is too low).

**B2 · Minor off-by-one (1–3 year gaps, 25 cases)**

These are almost all legitimate: a case decided in year X was reported in year X+1, or
a brief cites a district decision (earlier year) that was later affirmed by the circuit
(later year). Not bugs per se — but the `year_mismatch` flag is correct to surface them
for user review.

---

## Bug C — `name_mismatch_verified` (12 instances)

### Sub-patterns

**C1 · Wrong CourtListener verification (4 clear cases)**

These are verifications where name similarity matching selected the completely wrong case:

| Doc | Extracted | Canonical (from CL) |
|---|---|---|
| 09_FTC-v-PennState | `F. & M. Schaefer Corporation v. C. Schmidt & Sons, Inc` | `Harnischfeger Corp. v. Paccar, Inc.` |
| 21_OK-v-BP | `Control v. Fcc` | `Kavanau v. Santa Monica Rent Control Board` |
| 25_Verizon | `At T Co. Mci Communications Corporation v. At&t Co` | `Southern Pacific Communications Co. v. American Telephone and...` |
| 16_Mississippi | `Texas v. Scott & Fetzer Co` | `Railroad Comm'n of Tex. v. Pullman Co.` |

The extracted name fragments (`"Control"`, `"At T Co."`, `"Texas"`) match CourtListener
results with superficial word overlap but are completely wrong cases.

**Proposed fix:** Add a hard-fail check: if the similarity score is < 0.4 AND neither
party name token from the extracted name appears in the canonical name, reject the
verification as a mismatch and keep the citation as unverified.

**C2 · Abbreviation normalization mismatch (4 cases)**

Minor mismatches where the names are actually the same case but abbreviation differences
trick `names_are_same_case()`:

- `Ftc v. Shkreli` vs `Fed. Trade Comm'N v. Shkreli` — "FTC" vs "Fed. Trade Comm'n"
- `Carbonell v. I. N. S` vs `Carbonell v. I.N.S.` — period spacing
- `Prof' v. United States` vs `National Society of Professional Engineers v. United States` — truncation
- `Co., Inc. v. Ftc` vs `Charles Pfizer & Co., Inc. v. Federal Trade Commission` — truncated plaintiff

These are extraction-quality issues (wrong truncation), not verification bugs. The
canonical name is correct; the extracted name is the problem.

**C3 · Legitimate name difference (4 cases)**

- `Taylor v. Carryl` vs `James L. v. Carryl` — same case, different abbreviation in document
- `Textile Employees, Afl-cio, Clc v. Ins` vs `Union of Needletrades...` — union name changed
- `Assocs. v. Garlock` vs `W.L. Gore & Associates v. Ga...` — truncated plaintiff (Bug A4)
- `Becerra v. U.S. Dep't of the Interior` vs `California by and through Becerra v. U.S. Dep't...`

The display mismatch here is expected and intentional (shows what was in the doc vs.
canonical). These are not bugs.

---

## Bug D — `oversized_cluster` (4 instances)

| Doc | Cluster | Size | Name |
|---|---|---|---|
| 18_AmEx-v-Italian-Colors | cluster_1 | 8 | Green Tree Financial Corp.-Alabama v. Randolph |
| 19_FTC-v-Phoebe-Putney | cluster_24 | 8 | **Unknown Case** |
| 23_Leegin-v-PSKS | cluster_6 | 6 | Business Electronics Corp. v. Sharp Electronics |
| 25_Verizon | cluster_19 | 6 | Spectrum Sports, Inc. v. McQuillan |

The `cluster_24 (Unknown Case, size=8)` in `19_FTC-v-Phoebe-Putney_2012.pdf` is
suspicious — 8 citations in a cluster with no extractable name suggests a bad transitive
merge of unrelated bare citations (the N/A merge bug, which should be mostly fixed by
the `_same_case_check` change but may still affect pre-verification clusters).

The others (Green Tree 8, Business Electronics 6, Spectrum Sports 6) may be legitimate
if the same case genuinely appears many times.

---

## Bug E — `multi_canonical_cluster` (3 instances)

| Doc | Cluster | URLs |
|---|---|---|
| 16_Mississippi | cluster_37 | New York v. 11 Cornwell Co. × 2 (different editions) |
| 17_FTC-v-Watson | cluster_3 | Arkansas Carpenters v. Bayer AG × 2 (district + circuit) |
| 25_Verizon | cluster_11 | **MCI v. AT&T + Southern Pacific v. AT&T — two distinct cases!** |

The Verizon case is a genuine bad merge: two different antitrust cases about AT&T
(MCI Communications Corp. v. AT&T Co., and Southern Pacific Communications Co. v.
American Telephone and Telegraph Co.) ended up in the same cluster because both are
"[party] v. AT&T" and similarity-match at high enough score.

**Proposed fix:** When two verified citations in the same cluster have different
CourtListener URLs AND their canonical names don't match, force a cluster split.

---

## Bug F — `duplicate_cluster_id` (2 instances)

Both in `01_Tri-City-Valleycats-v-Commissioner_2023.pdf`:
- `c0_ecn_0_yr_0` appears 2×
- `c0_ecn_0_yr_1` appears 2×

The `c0_` prefix suggests this is from the "orphan cluster" path in `split_clusters_by_canonical_name`. When two different clusters are split at the same `ecn_0_yr_0` sub-key, they collide.

**Proposed fix:** Append a UUID suffix or a per-cluster sequential counter to the split
cluster ID to prevent collisions.

---

## Recurring Frequently-Cited Cases with Extraction Issues

These cases appear in multiple documents and consistently have bad ECN:

| Case | Appears in | Issue |
|---|---|---|
| Aspen Skiing Co. v. Aspen Highlands Skiing Corp. | 11, 25 | `ecn='N/A'` (Aspen) |
| Broadcast Music, Inc. v. Columbia Broadcasting System | 10, 23 | `ecn='N/A'` |
| Zenith Radio Corp. v. Hazeltine Research, Inc. | 09, 20 | `ecn='N/A'` |
| Hanover Shoe, Inc. v. United Shoe Mach. Corp. | 20, 24 | `ecn='N/A'` |
| Ciprofloxacin Hydrochloride Antitrust Litig. | 22, 24 | `ecn='N/A'` |
| Covad Communications v. Bell Atlantic/BellSouth | 25 | `ecn='N/A'` (3 citations) |
| Gulfstream III Assocs. v. Gulfstream Aerospace Corp. | 09 | `ecn='N/A'` |
| E. Scientific Co. v. Wild Heerbrugg Instruments | 09, 10 | `ecn='N/A'` |

These are strong candidates for the **known-citation lookup table** (pre-seed with ECN
from CourtListener canonical names to avoid repeat extraction failures).

---

## Priority Fix List

| Priority | Bug | File(s) to Edit | Estimated Impact |
|---|---|---|---|
| 1 | A1: Recognize "Antitrust Litig." as case structure | `cluster_display_utils.py:92` | ~35 issues fixed |
| 2 | A2: Strip "Amici Curiae" prefix | `ucp_v2.py ~4381` | ~4 issues |
| 3 | A3: Strip "Cited Authorities Page" | `ucp_v2.py ~4408` | ~2 issues |
| 4 | B1: Hard-reject canonical dates > current year | `unified_processing_pipeline.py` | ~5 issues |
| 5 | C1: Stricter wrong-verification guard | `courtlistener_verification.py` | ~4 issues |
| 6 | E: Force cluster split on multi-canonical | `post_verify_split.py` or clustering | ~1 issue |
| 7 | F: Deduplicate cluster IDs | cluster ID generation | ~2 issues |
| 8 | A5: Admin reporters in `_INLINE_REPORTER_RE` | `ucp_v2.py ~190` | ~5 issues |
