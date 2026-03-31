# Go-live evidence

Use this folder for **non-secret** artifacts around a release:

- `REGRESSION_LOG.md` — automated regression gate output (append via `python scripts/record_go_live_evidence.py`).
- `MONITORING_LOG.md` — optional: notes from first 24–48h (create when monitoring).
- `RELEASE_ARTIFACTS.md` — optional: image digests, tag names.
- Redacted **sample JSON** responses and screenshots from manual QA (see `docs/GO_LIVE_MANUAL_VERIFICATION.md`).

Do **not** commit client confidential documents or API keys.
