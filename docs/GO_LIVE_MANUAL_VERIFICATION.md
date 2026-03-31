# Manual verification (operator)

Complete this document when preparing a public launch. It corresponds to functional items in `PRODUCTION_GO_LIVE_CHECKLIST.md`.

## 1) Gold / representative documents

- [ ] Run your **gold document set** (or NAAG / Trinko / internal corpus) through the production-equivalent pipeline.
- [ ] Record: document id, date, and **acceptable / not acceptable** for citations and clusters.

## 2) Strict gate and `possible_match`

- [ ] Pick at least one citation with **known name/year mismatch** vs CourtListener; confirm the UI/API does **not** show it as fully verified, or shows **`possible_match`** as designed.
- [ ] Confirm **strict-gate rejects** are visible in logs or response fields you rely on.

## 3) WL / LEXIS and parallels

- [ ] Submit a sample with **Westlaw/Lexis** style cites; confirm labeling and that **parallel** behavior matches policy (including “not in document” cases if applicable).

## 4) Clustering

- [ ] Confirm **deduplication** and **federal tier / split** behavior on at least one document where you have expected cluster boundaries.

## 5) Evidence to archive

After the above, save:

- [ ] One **JSON** response (or API payload) per critical scenario under `docs/go-live-evidence/` (redact client data if needed).
- [ ] Optional **screenshots** of the results UI for the same scenarios.

Record commands and timestamps in `docs/go-live-evidence/REGRESSION_LOG.md` (append after `scripts/record_go_live_evidence.py`).
