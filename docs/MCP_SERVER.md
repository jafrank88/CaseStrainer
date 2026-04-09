# CaseStrainer MCP Server

CaseStrainer exposes its citation analysis engine as an **MCP (Model Context Protocol) server**, allowing AI assistants such as Claude Desktop, Windsurf, and Cursor to call CaseStrainer directly as a tool — no copy-pasting, no switching windows.

## Table of Contents

- [What is MCP?](#what-is-mcp)
- [Available Tools](#available-tools)
- [Quick Start](#quick-start)
- [Configuration by Assistant](#configuration-by-assistant)
- [Access Control](#access-control)
- [Environment Variables](#environment-variables)
- [Troubleshooting](#troubleshooting)

---

## What is MCP?

The [Model Context Protocol](https://modelcontextprotocol.io/) is an open standard that lets AI assistants call external tools. Once configured, your AI can say "analyze this brief for citations" and CaseStrainer will process it and return results — all without leaving the conversation.

---

## Available Tools

| Tool | Auth required | Description |
|---|---|---|
| `analyze_text` | Yes | Submit legal text; returns extracted, clustered, and verified citations |
| `analyze_url` | Yes | Fetch a PDF or web page URL and analyze it for citations |
| `get_task_status` | Yes | Check or retrieve results for a long-running job by task ID |
| `check_health` | **No** | Verify service is reachable; always accessible for monitoring |

`analyze_text` and `analyze_url` handle the async/sync duality automatically — they submit the job, poll until done (up to 10 minutes), and return a formatted result. You do not need to manage task IDs unless a job times out.

---

## Quick Start

### 1. Install dependencies

The MCP server has a deliberately minimal dependency footprint — install it in a separate lightweight venv to keep it independent of the main backend stack.

```powershell
# Windows
python -m venv venv-mcp
.\venv-mcp\Scripts\Activate.ps1
pip install -r requirements-mcp.txt
```

```bash
# macOS / Linux
python3 -m venv venv-mcp
source venv-mcp/bin/activate
pip install -r requirements-mcp.txt
```

`requirements-mcp.txt` contains only two packages:

```text
mcp>=1.6.0
httpx>=0.27.0
```

### 2. Test the server starts

```powershell
python casestrainer_mcp.py
```

You should see two startup lines on stderr:

```text
[CaseStrainer MCP] Auth: DISABLED (open access — set MCP_API_KEYS to restrict)
[CaseStrainer MCP] Backend: http://localhost:5000
```

Press **Ctrl+C** to stop — the server is meant to be launched by the AI assistant, not run manually.

### 3. Add to your AI assistant's config

See [Configuration by Assistant](#configuration-by-assistant) below.

---

## Configuration by Assistant

All assistants use the same format — a JSON block identifying the `command` to run and optional `env` variables. Full examples are in `.claude/mcp_config_example.json`.

### Claude Desktop

Config file: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "casestrainer": {
      "command": "C:/path/to/casestrainer/venv-mcp/Scripts/python.exe",
      "args": ["C:/path/to/casestrainer/casestrainer_mcp.py"],
      "env": {
        "CASESTRAINER_URL": "http://localhost:5000"
      }
    }
  }
}
```

### Windsurf

Config file: `~/.codeium/windsurf/mcp_config.json`

Same format as Claude Desktop — paste the `mcpServers` block above.

### Cursor

Config file: `~/.cursor/mcp.json` (or **Settings → MCP**)

Same format as Claude Desktop.

### Pointing at the production server

Replace `CASESTRAINER_URL` with the production URL to analyze documents against the live deployment instead of a local instance:

```json
"env": {
  "CASESTRAINER_URL": "https://wolf.law.uw.edu",
  "CASESTRAINER_MCP_KEY": "your-key-here"
}
```

> **Note:** Access control is strongly recommended when pointing at a remote server — see below.

---

## Access Control

By default the MCP server is open to any local process that can spawn it. Because `stdio` transport spawns a fresh server process per session, the OS-level protection (only the local user can start the process) is usually sufficient for local use.

For **remote deployments** or environments where you want explicit per-agent revocation, enable key-based access control.

### Server setup

Add to the server's `.env` file (same file used by the CaseStrainer backend):

```dotenv
# One entry per authorised agent — format: key:AgentName
# AgentName is optional but recommended for auditing
MCP_API_KEYS=key1:ClaudeDesktop,key2:Windsurf,key3:Cursor
```

Generate a key:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Agent setup

Add `CASESTRAINER_MCP_KEY` to that agent's MCP `env` block:

```json
{
  "mcpServers": {
    "casestrainer": {
      "command": "C:/path/to/venv-mcp/Scripts/python.exe",
      "args": ["C:/path/to/casestrainer/casestrainer_mcp.py"],
      "env": {
        "CASESTRAINER_URL": "http://localhost:5000",
        "CASESTRAINER_MCP_KEY": "key1"
      }
    }
  }
}
```

### How it works

- Each agent gets a **unique key** and a friendly name.
- Keys are validated with `hmac.compare_digest` — constant-time comparison to prevent timing attacks.
- **Revoke** an agent by removing its entry from `MCP_API_KEYS` and restarting the MCP server process (the assistant will restart it automatically on next use).
- `check_health()` is always accessible without a key so monitoring and health-check tools work regardless.

### Startup log

When the server starts, it prints the auth status to stderr — visible in the assistant's logs:

```text
# With auth enabled:
[CaseStrainer MCP] Auth: ENABLED (2 key(s): ClaudeDesktop (abc12345…), Windsurf (def67890…))

# Without auth:
[CaseStrainer MCP] Auth: DISABLED (open access — set MCP_API_KEYS to restrict)
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `CASESTRAINER_URL` | `http://localhost:5000` | Base URL of the CaseStrainer service |
| `CASESTRAINER_TIMEOUT` | `600` | Max seconds to poll for an async job to complete |
| `CASESTRAINER_POLL_SEC` | `3` | Polling interval in seconds for async jobs |
| `MCP_API_KEYS` | *(unset = open)* | **Server-side** allowed keys, format `key:Name,...` |
| `CASESTRAINER_MCP_KEY` | *(unset)* | **Agent-side** key — set in the agent's MCP `env` block |

---

## Troubleshooting

### "Cannot connect to CaseStrainer"

The MCP server cannot reach the backend. Check:

1. The CaseStrainer Docker stack is running: `docker ps`
2. `CASESTRAINER_URL` in your MCP config matches the actual service address.
3. For local deployments: backend typically listens on `http://localhost:5001` behind Docker's port mapping, but `http://localhost:5000` if running directly. Check `docker-compose.prod.yml`.

### "Access denied: CASESTRAINER_MCP_KEY is not set"

The server has `MCP_API_KEYS` configured but this agent's MCP `env` block does not include `CASESTRAINER_MCP_KEY`. Add the key to the agent's config file and restart the assistant.

### "Access denied: the CASESTRAINER_MCP_KEY provided does not match"

The key value in the agent's config doesn't match any entry in `MCP_API_KEYS`. Verify there are no extra spaces, and that the server's `.env` has been reloaded (restart the MCP server process).

### Job timed out

`analyze_text` and `analyze_url` poll for up to `CASESTRAINER_TIMEOUT` seconds (default 10 minutes). For very large documents, increase this value in the agent's `env` block:

```json
"CASESTRAINER_TIMEOUT": "1200"
```

If the job timed out but is still running, use `get_task_status` with the task ID that was returned in the timeout message.

### Health check

Ask the AI assistant to run `check_health()` — it always works without a key and will report whether the backend, Redis, and workers are reachable.

---

## Related

- [API Documentation](API_DOCUMENTATION.md) — REST endpoints the MCP server calls internally
- [Processing Pipeline](PIPELINE_ENTRY_POINTS.md) — How citation extraction and verification works
- [Data Retention](DATA_RETENTION.md) — How long async task results are kept in Redis
- [`.claude/mcp_config_example.json`](../.claude/mcp_config_example.json) — Ready-to-paste config examples
- [`casestrainer_mcp.py`](../casestrainer_mcp.py) — MCP server source
- [`requirements-mcp.txt`](../requirements-mcp.txt) — Minimal dependency list
