# CaseStrainer Word add-in (static task pane)

These files are copied verbatim into the Vue production build (`public/` → site root). After deploy they are available at:

- `https://wolf.law.uw.edu/casestrainer/word-addin/index.html`
- `https://wolf.law.uw.edu/casestrainer/word-addin/manifest.xml`

For local sideloading with Vite (`npm run dev`), use `manifest.local.xml` (points at `http://localhost:5173/casestrainer/word-addin/`).

The task pane uses the same `POST /casestrainer/api/analyze` contract as the web app (`type: "text"`, optional `force_mode: "sync"`, poll `task_status` when needed).
