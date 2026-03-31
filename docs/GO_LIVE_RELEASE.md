# Release hygiene and publishing

## 1) Intended files only

Before tagging:

- [ ] `git status` — no accidental adds of `uploads/`, `data/*.db-wal`, local JSON dumps, or secrets.
- [ ] `.gitignore` covers env files (`config.env`, `.env` with secrets).

## 2) No local artifacts or secrets in commits

- [ ] No `COURTLISTENER_API_KEY`, `SECRET_KEY`, or `REDIS_PASSWORD` in tracked files.
- [ ] Use `.env.prod.example` / deployment secrets manager only.

## 3) Merge and tag

1. Merge approved changes to the release branch (e.g. `main`).
2. Create an annotated tag:

```bash
git tag -a vX.Y.Z -m "Release X.Y.Z: <short summary>"
git push origin vX.Y.Z
```

3. Build/push images if applicable; record digest in `docs/go-live-evidence/RELEASE_ARTIFACTS.md`.

## 4) Release notes

Copy `docs/RELEASE_NOTES_TEMPLATE.md` to `docs/RELEASE_NOTES_vX.Y.Z.md` (or project changelog) and fill:

- Behavior changes
- Known limitations
- Required config/env changes

## 5) Operator checklist

After deploy, run:

```bash
python scripts/verify_production_env.py
python scripts/ci_regression.py
python scripts/record_go_live_evidence.py
```
