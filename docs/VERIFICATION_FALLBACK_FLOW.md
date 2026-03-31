# Verification Fallback Flow: When a Case Is Not Verified by Batch

This document describes what happens when a citation is **not** verified during the initial CourtListener batch lookup. There are two layers of fallbacks: **in-batch fallbacks** (inside the batch API loop) and **enhanced batch fallback** (after all batches complete).

---

## 1. Entry: Batch verification

- **Entry point:** `verify_citations_batch()` in `unified_verification_master.py`
- Citations are sent in batches to **CourtListener citation-lookup API** via `_verify_with_courtlistener_lookup_batch()`.
- For each citation in the batch response, the code branches on whether the citation was found and whether clusters pass validation.

---

## 2. In-batch fallbacks (inside `_verify_with_courtlistener_lookup_batch`)

These run **per citation** when the batch API does not yield a verified result for that citation.

### Branch A: Citation not in API response (`citation_result` is None)

CourtListener returned no matching result for this citation. Fallbacks run in order:

| Order | Condition | Fallback function |
|-------|-----------|-------------------|
| 1 | Slip opinion (e.g. `592 U.S. ___`) + has date | `_verify_slip_opinion_by_volume_year` |
| 2 | Has extracted name + date | `_verify_with_courtlistener_search` (case name + year search) |
| 3 | Federal citation (F.2d, F.3d, F.4th, F. Supp.) | `_verify_with_law_resource` |
| 4 | U.S. bound (e.g. `554 U.S. 269`) | `_verify_with_cornell_lii` → `_verify_with_findlaw` → `_verify_with_justia` |
| — | No match | `VerificationResult(error="No match found in batch lookup")` |

### Branch B: Citation in response but 404 or no clusters

CourtListener returned a result for this citation but `status_code == 404` or `clusters_for_citation` is empty. Fallbacks run in order:

| Order | Condition | Fallback function |
|-------|-----------|-------------------|
| 1 | Slip opinion + has date | `_verify_slip_opinion_by_volume_year` |
| 2 | U.S. Supreme (any) + name + date | `_verify_with_courtlistener_search` |
| 3 | U.S. bound (e.g. `523 U.S. 83`) | `_verify_with_cornell_lii` → `_verify_with_findlaw` → `_verify_with_justia` |
| — | No match | `VerificationResult(error=error_message or "Citation not found")` |

### Branch C: Has clusters but validation fails

- Clusters are validated with `_find_best_matching_cluster_sync()` (citation/year/name match).
- If **year mismatch** and date not “clearly wrong”: result is stored as **unverified** with `source="year_mismatch_rejected"` (canonical data kept for clustering).
- If **no matching cluster**: the citation is left unverified for this batch; it can still be retried in **enhanced batch fallback** (see below).

---

## 3. After all batches: Enhanced batch fallback

When **`enable_fallback`** is True and there are **unverified citations**:

- **Trigger:** `enable_fallback and unverified_count > 0` after `verify_citations_batch` finishes.
- **Function:** `enhanced_batch_fallback()` in `enhanced_batch_fallback.py`.
- **Input:** Full list of citations, current results, case names, dates; **max** `max_fallback_citations` unverified citations are processed (default 100).
- **Optional skip:** If env `SKIP_FALLBACK_VERIFICATION` is `true`/`1`/`yes`, this step is skipped.

Unverified citations are **prioritized** (e.g. those with case names first), then each is passed to an internal **per-citation** fallback that tries sources in this order:

| Priority | Citation type | Sources tried (in order) |
|----------|----------------|---------------------------|
| 1 | Slip opinion (`* U.S. ___`) + date | `_verify_slip_opinion_by_volume_year` |
| 2 | U.S. Supreme Court (bound, e.g. `554 U.S. 269`) | `_verify_with_cornell_lii`, `_verify_with_openjurist`, `_verify_with_findlaw`, `_verify_with_justia` |
| 3 | Federal (F.2d, F.3d, F.4th, F. Supp.) | `_verify_with_openjurist`, `_verify_with_leagle`, `_verify_with_law_resource`, `_verify_with_findlaw` |
| 4 | Any (if has extracted name) | `_verify_with_courtlistener_search` |
| 5 | Year &gt; 1850 | `_verify_with_casemine` |
| 6 | Final | **FastVerificationSystem** (`_fast_verify_wrapper` → CaseMine-style + other fast sources) |

**Not used in enhanced batch fallback:** VLex only (JavaScript-based). **Justia** is used for U.S. Supreme Court (direct URL `supreme.justia.com`; 403 applied to search, not direct GET).

- **Concurrency:** Up to 5 citations in parallel (semaphore).
- **Timeouts:** Per-citation timeout (e.g. 5s) and a global fallback timeout (e.g. 300s).
- **Result:** Updated `results` list; any new verified/possible-match result replaces the previous unverified result for that index.

---

## 4. Single-citation path (for reference)

When verification is done **one citation at a time** (e.g. `verify_citation()`), the flow is different:

1. **CourtListener citation-lookup** → if verified, return.
2. If not rate limited: **CourtListener search** → if verified, return.
3. **Enhanced fallback** (`_verify_with_enhanced_fallback`) with a **different** source list:
   - Slip/reporter-first logic when name is missing/invalid.
   - Then **fallback_sources** (fast vs full mode), which **include Justia**, Cornell LII, FindLaw, Leagle, VLex, CaseMine, Bing, Google Scholar, etc., and optionally Law Resource, OpenJurist, state courts, FindLaw.

So for a **single** citation, Justia is tried in `_verify_with_enhanced_fallback`; for **batch**, Justia is tried both in **in-batch** U.S. bound fallbacks (Branch A/B) and in `enhanced_batch_fallback` (Cornell LII → OpenJurist → FindLaw → Justia for U.S. Supreme Court).

---

## 5. Summary diagram

```
verify_citations_batch()
  │
  ├─ For each batch: _verify_with_courtlistener_lookup_batch()
  │    │
  │    ├─ Citation not in API response (Branch A)
  │    │    → Slip → CourtListener search → Law Resource (federal) → Cornell → FindLaw → Justia (U.S.) → else unverified
  │    │
  │    ├─ 404 or no clusters (Branch B)
  │    │    → Slip → CourtListener search → Cornell → FindLaw → Justia (U.S.) → else unverified
  │    │
  │    └─ Has clusters → validate; year mismatch → unverified with canonical data; no match → unverified
  │
  ├─ After all batches: if enable_fallback and unverified_count > 0
  │    → enhanced_batch_fallback()
  │         For each unverified citation (up to max_fallback_citations):
  │           Slip → Cornell LII / OpenJurist / FindLaw / Justia (U.S.) → OpenJurist / Leagle / Law_Resource / FindLaw (federal)
  │           → CourtListener search → CaseMine → FastVerification
  │
  └─ Return results
```

---

## 6. Implications for U.S. Reports (e.g. 554 U.S. 269)

- **In-batch:** If CourtListener returns no match or 404, U.S. bound citations try Cornell LII → FindLaw → **Justia** in Branch A and B. With the “verify by URL alone” logic in `_verify_with_justia`, a 200 from `supreme.justia.com/.../us/...` can mark the citation verified there.
- **Enhanced batch fallback:** U.S. Supreme Court citations also try Cornell LII → OpenJurist → **FindLaw** → **Justia**, so a second chance to verify via Justia direct URL or FindLaw if in-batch failed.

---

## 7. How to maximize verification (single, batch, sync, async)

**Unified behavior:**

- **Single citation (sync):** `verify_citation_sync()` runs `verify_citation()` in a new event loop; same logic as async single citation. Fallback is `_verify_with_enhanced_fallback` (Justia, Cornell LII, FindLaw, Leagle, VLex, CaseMine, Bing, etc.).
- **Single citation (async):** `verify_citation()` → CourtListener lookup → CourtListener search → `_verify_with_enhanced_fallback` with full source list.
- **Batch (sync):** Callers use `asyncio.run(verifier.verify_citations_batch(...))` or a thread with `run_until_complete(verify_citations_batch(...))`; same async batch flow.
- **Batch (async):** `verify_citations_batch()` → in-batch fallbacks (Branch A/B) → then `enhanced_batch_fallback()` for unverified (with FindLaw + Justia for U.S., FindLaw for federal).

**Recommendations:**

1. **Keep `enable_fallback=True`** for both single and batch so fallback sources run (default is True).
2. **Use `max_fallback_citations=100`** (or higher) for batch so more unverified citations get a second pass via enhanced_batch_fallback (default 100; citation_extraction_endpoint and unified_citation_processor_v2 pass this explicitly).
3. **Do not set `SKIP_FALLBACK_VERIFICATION=true`** unless you intentionally want to skip enhanced batch fallback (e.g. for speed).
4. **Single vs batch:** For maximum coverage, prefer batch when you have many citations (CourtListener batch + in-batch fallbacks + enhanced_batch_fallback). For one citation, single `verify_citation` is equivalent and uses the same fallback list plus VLex/Bing/Google Scholar.
5. **Sync vs async:** Use the same entry point (`verify_citation_sync` / `verify_citation` for single; `verify_citations_batch` for batch). Sync paths wrap the async implementation so behavior is identical.
