# Ad-hoc scripts

One-off check, debug, and read scripts moved from the project root. Not part of the main application or test suite.

- **check_*.py** – connectivity, API, Redis, task status, and feature checks
- **debug_*.py** – debugging extraction, clustering, verification, and pipelines
- **read_*.py** – reading/exploring external data (Justia, Cornell, scholar, etc.)
- **test_*.py** – one-off test/demo scripts moved from repo root (not pytest; for sync/async comparison use `scripts/test_sync_async_pdf.py`)

CI runs `scripts/adhoc/check_health.py` for the backend health check.
