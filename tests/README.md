# CaseStrainer automated tests

## CI regression gate (`scripts/ci_regression.py`)

GitHub Actions and pull-request checks run:

```bash
python scripts/ci_regression.py
```

This uses **`pytest-ci-regression.ini`**, which includes the same wolf-style modules plus **`tests/test_mismatch_party_line.py`**. By default the runner passes **`-m "not local_briefs and not local_pdf and not production"`** so optional corpora (gitignored `downloaded_briefs/`, one-off PDFs, production suite) do not run in CI.

| Goal | Command |
|------|---------|
| Same as CI (recommended before push) | `python scripts/ci_regression.py` |
| Windows + Redis env like other scripts | `pwsh scripts/run_ci_regression.ps1` |
| Include `local_pdf` tests (skip if PDF missing) | `python scripts/ci_regression.py --with-local-pdf` |
| Include `production` tests | `python scripts/ci_regression.py --with-production` |
| After the gate, run `downloaded_briefs/` smoke tests | `python scripts/ci_regression.py --with-downloaded-briefs` |
| Legacy wolf file list only | `python scripts/ci_regression.py --wolf` |
| No marker filter (everything in the chosen ini) | `python scripts/ci_regression.py --no-marker-filter` |
| Extra pytest args | `python scripts/ci_regression.py -v` or `python scripts/ci_regression.py -- -k Foo` |

Set **`CASSTRAINER_USE_TEST_REDIS=1`** and run Redis locally when async/analyze tests need a broker (the PowerShell wrapper sets this and `REDIS_URL` for you).

## Reviewing saved briefs → golden expectations (extraction + clustering)

Goal: you manually decide what is correct for each PDF, then lock it in so future runs of the **same** pipeline must match.

1. **Dump actual output** (citations + clusters, no goldens committed yet):

   ```bash
   python scripts/brief_goldens.py dump --pdf downloaded_briefs/your_brief.pdf --out data/brief_goldens/runs/your_brief.json
   ```

   Or batch: `dump --dir downloaded_briefs --out-dir data/brief_goldens/runs --max-files 10`

2. **Author expectations** — copy `scripts/brief_goldens.manifest.example.json` to `data/brief_goldens/manifest.json` (that tree is **gitignored**), set `file`, `id`, and `expect` (counts, required citation substrings, `cluster_rules`). Use `"skip": true` for templates you have not wired to a real file yet.

3. **Verify**:

   ```bash
   python scripts/brief_goldens.py verify --manifest data/brief_goldens/manifest.json
   ```

Schema and field meanings: `src/utils/brief_golden_expectations.py`. Default manifest uses **`enable_verification: false`** for fast, deterministic local runs; set per-document **`enable_verification": true`** when you want CourtListener-backed checks.

## Keeping heavy tests or PDFs out of GitHub

**Facts only (recommended):** The **application code** stays in the public repo; **large PDFs** stay local. The directory **`downloaded_briefs/`** is already in `.gitignore`. Put briefs under `D:\dev\casestrainer\downloaded_briefs` (or anywhere and set **`CASSTRAINER_DOWNLOADED_BRIEFS_DIR`**). To run extraction smoke tests over those files:

1. Set **`CASSTRAINER_DOWNLOADED_BRIEF_TESTS=1`** (required so `tests/conftest.py` will collect `tests/test_downloaded_briefs_optional.py`).
2. Run **`python -m pytest tests/test_downloaded_briefs_optional.py -q --no-cov -o addopts=`** or **`python scripts/ci_regression.py --with-downloaded-briefs`**.

Without that env var, the optional module is ignored during collection, so **`pytest`** and GitHub Actions behave as before.

**Entire test suite in a second repo (advanced):** You can keep *all* test modules private: clone `casestrainer` and a private `casestrainer-tests` side by side, set **`PYTHONPATH`** to the main repo root, and run **`pytest`** from the private tree (with `conftest.py` there inserting the main repo on `sys.path`). GitHub would need access to the private repo (submodule, org secret checkout, or self-hosted runner with both workspaces). Most teams still keep **small, fast tests** in the main repo for PR safety and put only **corpus + slow jobs** outside.

## DOJ OSG Supreme Court briefs (corpus index)

The [Office of the Solicitor General Supreme Court Briefs](https://www.justice.gov/osg/supreme-court-briefs) listing is a practical source of real federal brief PDFs. This repo does **not** commit bulk PDFs or the full ~11k-row index.

- **Committed test corpus:** `tests/fixtures/justice_osg_supreme_court_briefs_sample.json` (small JSON snapshot: captions, docket numbers, `brief_url` / `pdf_url`). Schema is checked in `tests/test_justice_osg_brief_corpus.py`.
- **Refresh or grow the index locally:** from repo root with `PYTHONPATH` set:

  ```bash
  python scripts/fetch_osg_supreme_court_brief_index.py --pages 1 --out data/justice_osg/index.json
  ```

  Output under `data/justice_osg/` is **gitignored**. Use `--sleep` (default 1.5s) and keep `--pages` small. Optional: `--download-pdfs DIR` to save PDFs for local CaseStrainer runs (still do not commit large binaries without an explicit team policy).

- **Live regression against the site (optional):** `CASSTRAINER_JUSTICE_GOV_LIVE=1 python -m pytest tests/test_justice_osg_brief_corpus.py -k live -v`

Parsing helpers live in `src/utils/justice_osg_brief_listing.py`.

## Wolf / production UX regression

What users see on [wolf.law.uw.edu](https://wolf.law.uw.edu) comes from the same Flask app and clustering/display code exercised here. These tests do **not** hit the live Wolf server; they run the **same Python code** locally or in CI (with Redis on `localhost`, like Docker Compose and GitHub Actions).

**Recommended command** (quiet, no coverage gate, skips `tests/unit` scripts):

```powershell
# From repo root — Redis on 127.0.0.1:6379 recommended
pwsh scripts/run_wolf_regression_tests.ps1
```

Or:

```powershell
python -m pytest -c pytest-wolf.ini
```

`pytest-wolf.ini` runs **only** these modules: `test_mismatch_party_line`, `test_generalized_regressions`, `test_imports`, `test_analyze_async_contract` (cluster/display/API paths Wolf uses).

Default `pytest` uses `pytest.ini` (coverage, verbose). It still skips `tests/unit`, `tests/debug`, and other non-gated subtrees via `norecursedirs` / `collect_ignore`; add new **gated** tests as `tests/test_*.py` at the top level or extend `pytest-wolf.ini` deliberately.

**Environment**

- `tests/conftest.py` sets `REDIS_URL` / `CACHE_REDIS_URL` to `127.0.0.1` during pytest unless `CASSTRAINER_USE_TEST_REDIS=0`.
- Start Redis locally if async/analyze tests should talk to a real broker: e.g. `docker compose up -d redis`.

## PDF smoke (`1031351.pdf`)

Optional integration test (slow, no live server):

```powershell
$env:CASSTRAINER_TEST_PDF = 'file:///D:/dev/casestrainer/1031351.pdf'
python -m pytest tests/test_1031351_pdf_smoke.py -q --no-cov -o addopts=
```

If `1031351.pdf` sits at the repo root, you can omit the env var.

With the wolf script, **do not pass a bare `--`** (pytest will error). Append the test path directly:

```powershell
$env:CASSTRAINER_TEST_PDF = 'file:///D:/dev/casestrainer/1031351.pdf'
pwsh scripts/run_wolf_regression_tests.ps1 tests/test_1031351_pdf_smoke.py
```

The script strips a literal `--` so `.\scripts\run_wolf_regression_tests.ps1 -- tests/test_1031351_pdf_smoke.py` works when `--` is passed into the script. If you still see pytest complain about `--`, run without it: `.\scripts\run_wolf_regression_tests.ps1 tests/test_1031351_pdf_smoke.py`.

## `tests/unit/`

Manual smoke scripts (e.g. posting to Wolf with `requests`). They are **not** pytest tests and are ignored by `pytest-wolf.ini` / `collect_ignore`.

## Legacy note

Older docs referred to `test_case_strainer_api.py` and a server on port 5000. The current regression suite lives in `test_*.py` at the top level of `tests/` as listed in `pytest-wolf.ini`.
