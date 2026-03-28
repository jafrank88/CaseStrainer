# CaseStrainer automated tests

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
