#!/usr/bin/env python3
"""
CaseStrainer MCP Server
=======================
Exposes CaseStrainer citation analysis as MCP tools for AI assistants
(Claude Desktop, Windsurf, Cursor, etc.).

Usage
-----
  python casestrainer_mcp.py                    # stdio transport (default)
  python casestrainer_mcp.py --transport sse    # SSE transport on port 8000

Environment Variables
---------------------
  CASESTRAINER_URL          Base URL of the CaseStrainer service
                            (default: http://localhost:5000)
  CASESTRAINER_TIMEOUT      Max seconds to wait for a job to complete
                            (default: 600)
  CASESTRAINER_POLL_SEC     Polling interval in seconds (default: 3)

Access Control (optional)
--------------------------
  MCP_API_KEYS              Comma-separated list of allowed agent keys on the
                            SERVER side. Format: key:AgentName (name optional).
                            If unset, any caller may use the MCP server.
                            Example (in .env):
                              MCP_API_KEYS=abc123:ClaudeDesktop,def456:Windsurf

  CASESTRAINER_MCP_KEY      The key for THIS agent — set in the agent's MCP
                            config env block so the spawned server process
                            receives it. Must match one entry in MCP_API_KEYS.

  Generate keys with Python:
    python -c "import secrets; print(secrets.token_urlsafe(32))"

  check_health() is always accessible without a key so monitoring tools work.

Configuration in Claude Desktop / Windsurf / Cursor
----------------------------------------------------
  Add to your MCP config (e.g. claude_desktop_config.json):

    {
      "mcpServers": {
        "casestrainer": {
          "command": "python",
          "args": ["C:/path/to/casestrainer/casestrainer_mcp.py"],
          "env": {
            "CASESTRAINER_URL": "http://localhost:5000"
          }
        }
      }
    }

  For a remote/Docker deployment change CASESTRAINER_URL accordingly,
  e.g. "http://wolf.law.uw.edu".

  With access control enabled, add the agent's key to the env block:

    {
      "mcpServers": {
        "casestrainer": {
          "command": "python",
          "args": ["C:/path/to/casestrainer/casestrainer_mcp.py"],
          "env": {
            "CASESTRAINER_URL": "http://localhost:5000",
            "CASESTRAINER_MCP_KEY": "<this-agents-key>"
          }
        }
      }
    }

  Each agent gets its own unique key.  Revoke by removing it from MCP_API_KEYS
  in the server's .env and restarting the MCP server process.

Dependencies
------------
  pip install -r requirements-mcp.txt
"""

import asyncio
import hmac
import json
import os
import sys
from typing import Optional

import httpx
from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_BASE = os.getenv("CASESTRAINER_URL", "http://localhost:5000").rstrip("/")
_API = f"{_BASE}/casestrainer/api"
_TIMEOUT = float(os.getenv("CASESTRAINER_TIMEOUT", "600"))
_POLL = float(os.getenv("CASESTRAINER_POLL_SEC", "3"))

# ---------------------------------------------------------------------------
# Access control
# ---------------------------------------------------------------------------
# Server side: MCP_API_KEYS = "key1:AgentName1,key2:AgentName2"
# Client side: CASESTRAINER_MCP_KEY = "key1"  (set in the agent's env block)

def _parse_allowed_keys(raw: str) -> dict[str, str]:
    """Return {key: agent_name} from a comma-separated 'key:name' string."""
    result: dict[str, str] = {}
    for entry in raw.split(","):
        entry = entry.strip()
        if not entry:
            continue
        if ":" in entry:
            k, name = entry.split(":", 1)
            result[k.strip()] = name.strip()
        else:
            result[entry] = "unnamed-agent"
    return result


_ALLOWED_KEYS: dict[str, str] = _parse_allowed_keys(os.getenv("MCP_API_KEYS", ""))
_CLIENT_KEY: str = os.getenv("CASESTRAINER_MCP_KEY", "")


def _auth_error() -> Optional[str]:
    """
    Return None when the caller is authorised, or an error string when not.
    Uses hmac.compare_digest to prevent timing-based key enumeration.
    check_health() deliberately skips this check.
    """
    if not _ALLOWED_KEYS:
        return None  # Auth not configured — open access
    if not _CLIENT_KEY:
        return (
            "Access denied: CASESTRAINER_MCP_KEY is not set in this agent's "
            "MCP configuration. Contact the CaseStrainer administrator to "
            "obtain a key and add it to your MCP env block."
        )
    for allowed_key, agent_name in _ALLOWED_KEYS.items():
        if hmac.compare_digest(_CLIENT_KEY.encode(), allowed_key.encode()):
            return None  # Valid key — authorised
    return (
        "Access denied: the CASESTRAINER_MCP_KEY provided does not match any "
        "authorised agent key. Contact the CaseStrainer administrator."
    )

# ---------------------------------------------------------------------------
# MCP server instance
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "CaseStrainer",
    instructions=(
        "CaseStrainer extracts, clusters, and verifies case-law citations "
        "from text or URLs. "
        "Use analyze_text for pasted document content and analyze_url for "
        "PDF links or web pages. Processing takes 1-10 minutes depending on "
        "document size and citation count."
    ),
)

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _poll_until_done(client: httpx.AsyncClient, task_id: str) -> dict:
    """Poll /task_status/<task_id> until the job finishes or timeout expires."""
    elapsed = 0.0
    while elapsed < _TIMEOUT:
        await asyncio.sleep(_POLL)
        elapsed += _POLL
        try:
            r = await client.get(f"{_API}/task_status/{task_id}", timeout=30)
            r.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise RuntimeError(f"Task {task_id!r} not found (404)") from exc
            raise
        data = r.json()
        status = data.get("status", "")
        if status in ("completed", "success", "failed", "error") or data.get("is_finished"):
            return data
    raise TimeoutError(
        f"Task {task_id!r} did not complete within {int(_TIMEOUT)}s. "
        "The document may still be processing — poll manually with get_task_status()."
    )


def _fmt_results(data: dict) -> str:
    """
    Convert an API result dict into concise, human-readable text.
    Designed for AI consumption: one cluster per paragraph.
    """
    citations = data.get("citations") or []
    clusters = data.get("clusters") or []
    status = data.get("status", "")
    error = data.get("error")

    if status in ("failed", "error") or error:
        return f"Analysis failed: {error or 'unknown error'}"

    if not citations and not clusters:
        return "No legal citations found in the document."

    stats = data.get("result", {}).get("statistics", {})
    verified_count = sum(1 for c in citations if c.get("verified"))

    lines: list[str] = [
        f"Found {len(citations)} citation(s) in {len(clusters)} cluster(s) "
        f"({verified_count} verified).\n"
    ]

    for i, cl in enumerate(clusters, 1):
        verified = cl.get("verified", False)
        tag = "VERIFIED" if verified else "UNVERIFIED"

        case_name = (
            cl.get("cluster_case_name")
            or cl.get("canonical_name")
            or cl.get("submitted_display_name")
            or "Unknown Case"
        )
        case_name = case_name.strip() or "Unknown Case"

        cit_list = cl.get("display_citations") or cl.get("citations") or []
        cit_texts = [
            c.get("citation") or c.get("text", "")
            for c in cit_list
            if isinstance(c, dict)
        ]
        cit_texts = [t for t in cit_texts if t]

        year = cl.get("canonical_date") or cl.get("submitted_display_date") or ""
        canon_url = cl.get("canonical_url") or cl.get("verification_url") or ""

        lines.append(f"{i}. [{tag}] {case_name}")
        if cit_texts:
            lines.append(f"   Citations : {', '.join(cit_texts)}")
        if year:
            lines.append(f"   Year      : {year}")
        if canon_url:
            lines.append(f"   Source    : {canon_url}")

        mismatch = cl.get("name_mismatch") or cl.get("date_mismatch")
        if mismatch:
            lines.append("   ⚠ Name or date mismatch detected — review manually")

        lines.append("")

    if stats:
        lines.append(
            f"Statistics: {stats.get('total_citations', len(citations))} citations, "
            f"{stats.get('total_clusters', len(clusters))} clusters."
        )

    return "\n".join(lines)


async def _submit_and_wait(payload: dict) -> str:
    """POST to /analyze, handle both sync (immediate) and async (polled) responses."""
    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(f"{_API}/analyze", json=payload, timeout=60)
            r.raise_for_status()
        except httpx.ConnectError:
            return (
                f"Cannot connect to CaseStrainer at {_BASE}. "
                "Ensure the service is running and CASESTRAINER_URL is correct."
            )
        except httpx.HTTPStatusError as exc:
            return f"HTTP {exc.response.status_code} from CaseStrainer: {exc.response.text[:300]}"

        data = r.json()

        # Synchronous / already-complete response
        if (
            data.get("status") in ("completed", "success")
            or data.get("citations")
            or data.get("clusters")
        ):
            return _fmt_results(data)

        # Asynchronous: server queued the job
        task_id = data.get("task_id")
        if not task_id:
            return f"Unexpected response from CaseStrainer:\n{json.dumps(data, indent=2)[:800]}"

        try:
            result = await _poll_until_done(client, task_id)
        except TimeoutError as exc:
            return str(exc)
        except RuntimeError as exc:
            return str(exc)

        return _fmt_results(result)


# ---------------------------------------------------------------------------
# MCP tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def analyze_text(text: str) -> str:
    """
    Analyze legal text for citations.

    Submits the provided text to CaseStrainer, which extracts all legal
    case-law citations, groups them into clusters
    of related/parallel citations, and verifies each against external legal
    databases (CourtListener, CaseMine, Justia, Leagle).

    Returns a plain-text summary with verification status, case names,
    reporter strings, and source URLs for each citation cluster.

    Note: processing typically takes 1–5 minutes depending on citation count.

    Args:
        text: Full text of the legal document to analyze (brief, opinion,
              memo, etc.). There is no hard length limit, but very large
              documents (>200 KB) will be processed asynchronously.
    """
    err = _auth_error()
    if err:
        return err
    return await _submit_and_wait({"text": text, "type": "text"})


@mcp.tool()
async def analyze_url(url: str) -> str:
    """
    Fetch a URL and analyze it for legal citations.

    Submits the URL to CaseStrainer, which downloads the document (PDF or
    HTML), extracts all legal citations, clusters them, and verifies each
    against external legal databases.

    Returns a plain-text summary with verification status, case names,
    reporter strings, and source URLs for each citation cluster.

    Note: processing typically takes 2–10 minutes depending on document size.

    Args:
        url: URL to a PDF (e.g. a court opinion or brief) or web page
             containing legal citations.
             Example: https://www.justice.gov/d9/2025-08/24-923_brief.pdf
    """
    err = _auth_error()
    if err:
        return err
    return await _submit_and_wait({"url": url, "type": "url"})


@mcp.tool()
async def get_task_status(task_id: str) -> str:
    """
    Check the status of a previously submitted analysis job.

    Use this if analyze_text or analyze_url reported a timeout but you
    still want the result, or to check a long-running job you submitted
    earlier.

    Returns formatted citation results if the job is complete, or a
    status message if it is still running.

    Args:
        task_id: The task ID returned in a prior API response.
    """
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(f"{_API}/task_status/{task_id}", timeout=30)
            r.raise_for_status()
        except httpx.ConnectError:
            return f"Cannot connect to CaseStrainer at {_BASE}."
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return f"Task {task_id!r} not found. It may have expired."
            return f"HTTP {exc.response.status_code}: {exc.response.text[:300]}"

        data = r.json()
        status = data.get("status", "unknown")

        if status in ("processing", "queued", "started"):
            progress = data.get("progress") or data.get("progress_percent", 0)
            msg = data.get("message") or data.get("current_message", "")
            return (
                f"Job {task_id!r} is still running "
                f"({status}, {int(progress)}% — {msg}). "
                "Call get_task_status() again in a minute."
            )

        err = _auth_error()
        if err:
            return err
        return _fmt_results(data)


@mcp.tool()
async def check_health() -> str:
    # NOTE: check_health() is intentionally exempt from key auth so that
    # monitoring and health-check tools always work regardless of key config.
    """
    Check whether the CaseStrainer service is reachable and healthy.

    Returns a brief status summary including Redis and worker availability.
    """
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(f"{_API}/health", timeout=10)
            r.raise_for_status()
            data = r.json()
        except httpx.ConnectError:
            return f"CaseStrainer at {_BASE} is NOT reachable. Check that the service is running."
        except httpx.HTTPStatusError as exc:
            return f"CaseStrainer returned HTTP {exc.response.status_code} (unhealthy)."

    service_status = data.get("status", "unknown")
    redis_ok = data.get("redis", {}).get("status") == "healthy" if isinstance(data.get("redis"), dict) else None
    workers = data.get("workers")

    out = [f"CaseStrainer status: {service_status.upper()}"]
    if redis_ok is not None:
        out.append(f"Redis: {'healthy' if redis_ok else 'UNHEALTHY'}")
    if workers is not None:
        out.append(f"Workers: {workers}")
    out.append(f"Endpoint: {_BASE}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    transport = "stdio"
    if "--transport" in sys.argv:
        idx = sys.argv.index("--transport")
        if idx + 1 < len(sys.argv):
            transport = sys.argv[idx + 1]

    if _ALLOWED_KEYS:
        agents = ", ".join(f"{n} ({k[:8]}…)" for k, n in _ALLOWED_KEYS.items())
        key_status = f"ENABLED ({len(_ALLOWED_KEYS)} key(s): {agents})"
        if not _CLIENT_KEY:
            print(
                "[CaseStrainer MCP] WARNING: MCP_API_KEYS is set but "
                "CASESTRAINER_MCP_KEY is missing from this agent's env. "
                "All restricted tools will be blocked.",
                file=sys.stderr,
            )
    else:
        key_status = "DISABLED (open access — set MCP_API_KEYS to restrict)"
    print(f"[CaseStrainer MCP] Auth: {key_status}", file=sys.stderr)
    print(f"[CaseStrainer MCP] Backend: {_BASE}", file=sys.stderr)

    mcp.run(transport=transport)
