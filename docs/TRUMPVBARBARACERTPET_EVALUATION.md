# Evaluation: trumpvbarbaracertpet.pdf vs CaseStrainer Results

Evaluation of extraction and clustering issues **without** verification logic. Document: cert petition (Trump v. Barbara), 107 case cards, 231 citation mentions.

---

## 1. Summary of issues observed

| Category | Examples | Likely cause |
|----------|----------|--------------|
| **Wrong / contaminated case names** | "Hunt Page Cochise Consultancy..."; "Dukes Wal-Mart..."; "Windsor Amchem..."; "States v. Wong Kim Ark" for The Venus | Extraction: context bleed, antecedent guess, or order swap |
| **Mixed clusters (different cases in one card)** | Cochise Consultancy card has 2004 WL 166722 (Hawkins) + 587 U.S. 262 (Students for Fair Admissions) | Clustering: transitive merge or bare-citation reassignment |
| **Plaintiff/defendant reversed** | CASA, Inc. v. Trump vs Trump v. CASA; State of Washington v. Trump vs Trump v. Washington | Extraction or display: doc order vs canonical order |
| **Wrong year in extracted name** | United States v. Manzi 1928 vs 2005; Ludlam 1860 vs 1891; Amchem 1997 vs 2019 | Extraction: year from wrong context or nested citation |
| **Truncated names** | "Winter v. Nat"; "Crowley v. Local No"; "Moreno" (Toll v. Moreno) | Extraction: fragment or abbreviation not expanded |
| **Noise / invalid citations** | "States 1" (2022); "764 F. Supp. 3d 1050" with N/A name | Extraction: non-citation text or failed name resolution |
| **Duplicate case cards** | Amchem 1997 and Amchem 2019 (same 521 U.S. 591) | Clustering: same citation split by year or name variant |
| **Date/name differences (verified)** | Hawkins vs State ex rel. Hawkins; Rodriguez 2009 vs 2010; Ludlam 1860 vs 1891 | Expected when doc and DB differ; UI correctly flags |

---

## 2. Root-cause analysis (no verification)

### 2.1 Extraction (case name / date)

- **Context bleed**: Text before a citation (e.g. “Hunt, 2019” or “see Cochise”) gets merged into the next citation’s `extracted_case_name`, producing “Hunt Page Cochise Consultancy...” or wrong party order.
- **Antecedent / Id.**: Resolving “Id.” or short cites can pull the wrong antecedent (e.g. “States v. Wong Kim Ark” for The Venus, 8 Cranch 253) when multiple candidates exist.
- **Year from nested cite**: Parentheticals like “(citing X, 587 U.S. 262)” can attach the inner citation’s year or name to the main cite (or vice versa), causing wrong year (e.g. Amchem 1997 vs 2019) or wrong name.
- **Truncation**: Line wraps or abbreviation (e.g. “Nat.” for Natural Resources, “Local No” for Local No. 82) are not always expanded; fragment recovery only handles corporate suffixes (LLC, Inc., etc.).

### 2.2 Clustering

- **Transitive merge**: If the same citation string (e.g. “587 U.S. 262”) appears in two groups—one with correct name (Students for Fair Admissions), one with a wrong/contaminated name that later gets Cochise’s canonical name—transitive merge can merge those groups and produce one card with mixed cases.
- **Bare-citation reassignment**: `_reassign_bare_citations_by_containment` moves a short citation (e.g. “587 U.S. 262”) into any group that has a citation string **containing** that text. If “587 U.S. 262” appears inside a parenthetical in a different case (e.g. “Cochise… (citing SFA, 587 U.S. 262)”), the standalone 587 U.S. 262 citation can be reassigned into the Cochise cluster and wrongly merged.
- **names_are_same_case**: Plaintiff last-word match and fuzzy overlap can merge names that are similar but different (e.g. same defendant, different plaintiff). Less likely for Hawkins vs Cochise, but can contribute when extracted names are already contaminated.

### 2.3 Display / API

- **Canonical vs extracted**: Cards show canonical name (from verification) with “Extracted from Document: …”. Reversals (Trump v. CASA vs CASA v. Trump) can come from extraction storing doc order while canonical uses standard order, or from one being wrong.

---

## 3. Recommendations (extraction and clustering only)

### 3.1 Extraction

1. **Tighten context for case name**: When taking “context before” for case name, stop at sentence boundary or “citation-like” boundary (e.g. prior “v.” or reporter pattern) to avoid pulling in “Hunt, 2019” or “see Cochise” into the next citation’s name.
2. **Id. / short-cite resolution**: Prefer antecedent that matches reporter+volume+page of the short cite; reject antecedents whose citation text is clearly different (e.g. different reporter).
3. **Year from citation string**: Prefer year from the **main** citation (before “(quoting…” or “(citing…”); treat parenthetical year as secondary and avoid letting it overwrite the main cite’s year when they conflict.
4. **Expand truncations**: Extend fragment/abbreviation handling for “Nat.” → “Natural Resources”, “Local No” → “Local No. 82”, and similar patterns when they appear immediately before a reporter (e.g. “Winter v. Nat. Res. Def. Council”).
5. **Reject obvious noise**: Filter or mark as N/A citations that are not valid reporter patterns (e.g. “States 1”) or that have no plausible case name after cleaning.

### 3.2 Clustering

1. **Conflict check before transitive merge**: When merging two groups because they “share a citation”, require that the **citation text** is exactly the same (not just substring). If one is “587 U.S. 262” and the other is “Cochise..., 587 U.S. 262 (citing...)”, do not treat as “same citation” for merge.
2. **Safeguard bare-citation reassignment**: Before moving a bare citation into another group, require that the **target group’s citation that contains the bare string** has the same (or same-case) `extracted_case_name` or `canonical_name` as the bare citation. If the bare citation has name “Students for Fair Admissions” and the only containing citation is in a Cochise-named group, do not reassign.
3. **Stricter same-case for N/A**: When one citation has `extracted_case_name` N/A and the other has a name, do not merge solely by “shared citation” if the named citation’s string is long (e.g. contains “(citing”) so that the “shared” part might be a nested cite.

### 3.3 Display / UX

1. **Show both names when they differ**: When canonical and extracted differ (e.g. plaintiff/defendant order), show both explicitly, e.g. “Canonical: Trump v. CASA | In document: CASA, Inc. v. Trump.”
2. **Flag mixed clusters**: If a cluster’s citations have inconsistent canonical names (e.g. two different verified canonical_name values), show a warning and consider splitting the cluster in a post-pass.

---

## 4. Document-specific notes

- **trumpvbarbaracertpet.pdf** is a cert petition with many block quotes, parentheticals, and “Id.” cites. That increases the risk of context bleed, wrong antecedent, and nested-citation confusion.
- **107 cases, 231 citations** is a high ratio; many citations are parallel or short, which stresses grouping and reassignment logic.
- **Verified vs unverified**: The 40 “need review” and the “Unverified” / “Name Differences” / “Date Differences” cards are expected. The issues above are about **wrong grouping and wrong extracted names** even when verification is not involved.

---

## 5. Next steps

1. Implement extraction improvements (context boundary, Id. resolution, year preference, truncation expansion, noise filter).
2. Implement clustering safeguards (merge only on exact citation key when merging by “shared citation”; same-case or same-name check for bare-citation reassignment).
3. Re-run pipeline on trumpvbarbaracertpet.pdf (with and without verification) and compare to this evaluation.
4. Optionally add a post-cluster check: if a cluster has more than one distinct `canonical_name`, split or flag it.

---

*Evaluation based on user-provided CaseStrainer result summary and codebase review of extraction and clustering (unified_citation_processor_v2, unified_clustering_master_optimized, same_case, cluster_filter).*
