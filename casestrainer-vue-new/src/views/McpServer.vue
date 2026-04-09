<template>
  <div class="container py-5">
    <div class="row justify-content-center">
      <div class="col-lg-10">

        <!-- Hero -->
        <h1 class="display-4 mb-3 text-center">
          <i class="bi bi-robot me-2" aria-hidden="true"></i> MCP Server
        </h1>
        <p class="lead mb-4 text-center">
          Use CaseStrainer as a tool inside AI assistants — Claude Desktop, Windsurf, Cursor,
          and any other <a href="https://modelcontextprotocol.io/" target="_blank" rel="noopener noreferrer">
            MCP-compatible<span class="visually-hidden"> (opens in new tab)</span></a> client.
        </p>

        <!-- What is MCP -->
        <div class="alert alert-info mb-4" role="note">
          <h4 class="mb-2"><i class="bi bi-info-circle me-2" aria-hidden="true"></i> What is MCP?</h4>
          <p class="mb-0">
            The <strong>Model Context Protocol</strong> is an open standard that lets AI assistants call
            external tools. Once configured, your AI can analyze a brief for citations without you leaving
            the conversation — just ask it and it calls CaseStrainer automatically.
          </p>
        </div>

        <!-- Available Tools -->
        <div class="card mb-4">
          <div class="card-header bg-primary text-white">
            <h2 class="mb-0 h5"><i class="bi bi-tools me-2" aria-hidden="true"></i> Available Tools</h2>
          </div>
          <div class="card-body p-0">
            <table class="table table-hover mb-0" aria-label="MCP tools">
              <thead class="table-light">
                <tr>
                  <th scope="col">Tool</th>
                  <th scope="col">Auth required</th>
                  <th scope="col">Description</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><code>analyze_text</code></td>
                  <td><span class="badge bg-warning text-dark">Yes</span></td>
                  <td>Submit legal text — returns extracted, clustered, and verified citations</td>
                </tr>
                <tr>
                  <td><code>analyze_url</code></td>
                  <td><span class="badge bg-warning text-dark">Yes</span></td>
                  <td>Fetch a PDF or web page URL and analyze it for citations</td>
                </tr>
                <tr>
                  <td><code>get_task_status</code></td>
                  <td><span class="badge bg-warning text-dark">Yes</span></td>
                  <td>Check or retrieve results for a long-running job by task ID</td>
                </tr>
                <tr>
                  <td><code>check_health</code></td>
                  <td><span class="badge bg-success">No</span></td>
                  <td>Verify the service is reachable — always accessible for monitoring</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="card-footer text-muted small">
            <code>analyze_text</code> and <code>analyze_url</code> poll automatically until the job finishes —
            you don't need to manage task IDs unless a job times out.
          </div>
        </div>

        <!-- Quick Start -->
        <div class="card mb-4">
          <div class="card-header bg-primary text-white">
            <h2 class="mb-0 h5"><i class="bi bi-lightning me-2" aria-hidden="true"></i> Quick Start</h2>
          </div>
          <div class="card-body">

            <h3 class="h6 fw-bold">1. Install dependencies</h3>
            <p>
              Create a lightweight virtual environment — this keeps MCP dependencies separate from the main backend stack.
            </p>
            <div class="mb-3">
              <span class="badge bg-secondary mb-1">Windows (PowerShell)</span>
              <pre class="bg-light p-3 rounded border"><code>python -m venv venv-mcp
.\venv-mcp\Scripts\Activate.ps1
pip install -r requirements-mcp.txt</code></pre>
            </div>
            <div class="mb-3">
              <span class="badge bg-secondary mb-1">macOS / Linux</span>
              <pre class="bg-light p-3 rounded border"><code>python3 -m venv venv-mcp
source venv-mcp/bin/activate
pip install -r requirements-mcp.txt</code></pre>
            </div>
            <p class="text-muted small mb-3">
              <code>requirements-mcp.txt</code> contains only <code>mcp&gt;=1.6.0</code> and <code>httpx&gt;=0.27.0</code>.
            </p>

            <h3 class="h6 fw-bold mt-4">2. Add to your AI assistant's config</h3>
            <p>Find your assistant's MCP config file and add the <code>casestrainer</code> block:</p>

            <ul class="nav nav-tabs mb-0" id="assistantTabs" role="tablist">
              <li class="nav-item" role="presentation">
                <button class="nav-link active" id="claude-tab" data-bs-toggle="tab" data-bs-target="#claude" type="button" role="tab" aria-controls="claude" aria-selected="true">Claude Desktop</button>
              </li>
              <li class="nav-item" role="presentation">
                <button class="nav-link" id="windsurf-tab" data-bs-toggle="tab" data-bs-target="#windsurf" type="button" role="tab" aria-controls="windsurf" aria-selected="false">Windsurf</button>
              </li>
              <li class="nav-item" role="presentation">
                <button class="nav-link" id="cursor-tab" data-bs-toggle="tab" data-bs-target="#cursor" type="button" role="tab" aria-controls="cursor" aria-selected="false">Cursor</button>
              </li>
            </ul>
            <div class="tab-content border border-top-0 rounded-bottom mb-3" id="assistantTabsContent">
              <div class="tab-pane fade show active p-3" id="claude" role="tabpanel" aria-labelledby="claude-tab">
                <p class="text-muted small mb-2">Config file: <code>%APPDATA%\Claude\claude_desktop_config.json</code></p>
                <pre class="bg-light p-3 rounded border mb-0"><code>{{ claudeConfig }}</code></pre>
              </div>
              <div class="tab-pane fade p-3" id="windsurf" role="tabpanel" aria-labelledby="windsurf-tab">
                <p class="text-muted small mb-2">Config file: <code>~/.codeium/windsurf/mcp_config.json</code></p>
                <pre class="bg-light p-3 rounded border mb-0"><code>{{ claudeConfig }}</code></pre>
              </div>
              <div class="tab-pane fade p-3" id="cursor" role="tabpanel" aria-labelledby="cursor-tab">
                <p class="text-muted small mb-2">Config file: <code>~/.cursor/mcp.json</code> (or <strong>Settings → MCP</strong>)</p>
                <pre class="bg-light p-3 rounded border mb-0"><code>{{ claudeConfig }}</code></pre>
              </div>
            </div>
            <p class="text-muted small">
              Replace <code>C:/path/to/casestrainer</code> with your actual checkout path.
              Use the <code>venv-mcp</code> Python executable for isolation.
            </p>
          </div>
        </div>

        <!-- Access Control -->
        <div class="card mb-4">
          <div class="card-header bg-warning text-dark">
            <h2 class="mb-0 h5"><i class="bi bi-shield-lock me-2" aria-hidden="true"></i> Access Control</h2>
          </div>
          <div class="card-body">
            <p>
              By default the MCP server is open to any local process that can spawn it.
              To restrict which agents can use it, enable key-based access control.
            </p>

            <h3 class="h6 fw-bold">Server setup — <code>.env</code></h3>
            <p>Add one entry per authorised agent. Use <code>key:AgentName</code> format (name is optional but useful for auditing):</p>
            <pre class="bg-light p-3 rounded border mb-2"><code>MCP_API_KEYS=key1:ClaudeDesktop,key2:Windsurf,key3:Cursor</code></pre>
            <p class="text-muted small mb-3">
              Generate a key:
              <code>python -c "import secrets; print(secrets.token_urlsafe(32))"</code>
            </p>

            <h3 class="h6 fw-bold">Agent setup — MCP config <code>env</code> block</h3>
            <p>Each agent gets its own unique key in its MCP config:</p>
            <pre class="bg-light p-3 rounded border mb-3"><code>{{ authConfig }}</code></pre>

            <div class="row g-3">
              <div class="col-md-4">
                <div class="d-flex align-items-start p-2 bg-light rounded border">
                  <i class="bi bi-person-check fs-5 text-success me-2 flex-shrink-0 mt-1" aria-hidden="true"></i>
                  <div>
                    <strong class="d-block small">Per-agent keys</strong>
                    <span class="text-muted small">Each assistant gets its own unique key</span>
                  </div>
                </div>
              </div>
              <div class="col-md-4">
                <div class="d-flex align-items-start p-2 bg-light rounded border">
                  <i class="bi bi-x-circle fs-5 text-danger me-2 flex-shrink-0 mt-1" aria-hidden="true"></i>
                  <div>
                    <strong class="d-block small">Easy revocation</strong>
                    <span class="text-muted small">Remove entry from <code>MCP_API_KEYS</code>, restart</span>
                  </div>
                </div>
              </div>
              <div class="col-md-4">
                <div class="d-flex align-items-start p-2 bg-light rounded border">
                  <i class="bi bi-heart-pulse fs-5 text-primary me-2 flex-shrink-0 mt-1" aria-hidden="true"></i>
                  <div>
                    <strong class="d-block small">Health always open</strong>
                    <span class="text-muted small"><code>check_health()</code> never requires a key</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Environment Variables -->
        <div class="card mb-4">
          <div class="card-header bg-secondary text-white">
            <h2 class="mb-0 h5"><i class="bi bi-sliders me-2" aria-hidden="true"></i> Environment Variables</h2>
          </div>
          <div class="card-body p-0">
            <table class="table table-hover mb-0" aria-label="Environment variables">
              <thead class="table-light">
                <tr>
                  <th scope="col">Variable</th>
                  <th scope="col">Default</th>
                  <th scope="col">Description</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><code>CASESTRAINER_URL</code></td>
                  <td><code>http://localhost:5000</code></td>
                  <td>Base URL of the CaseStrainer service</td>
                </tr>
                <tr>
                  <td><code>CASESTRAINER_TIMEOUT</code></td>
                  <td><code>600</code></td>
                  <td>Max seconds to poll for an async job to complete</td>
                </tr>
                <tr>
                  <td><code>CASESTRAINER_POLL_SEC</code></td>
                  <td><code>3</code></td>
                  <td>Polling interval in seconds for async jobs</td>
                </tr>
                <tr>
                  <td><code>MCP_API_KEYS</code></td>
                  <td><em>unset (open)</em></td>
                  <td>Server-side allowed keys, format <code>key:Name,…</code></td>
                </tr>
                <tr>
                  <td><code>CASESTRAINER_MCP_KEY</code></td>
                  <td><em>unset</em></td>
                  <td>Agent-side key — set in the agent's MCP <code>env</code> block</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Troubleshooting -->
        <div class="card mb-4">
          <div class="card-header bg-secondary text-white">
            <h2 class="mb-0 h5"><i class="bi bi-bug me-2" aria-hidden="true"></i> Troubleshooting</h2>
          </div>
          <div class="card-body">
            <div class="accordion" id="troubleshootingAccordion">

              <div class="accordion-item">
                <h3 class="accordion-header" id="h-connect">
                  <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#c-connect" aria-expanded="false" aria-controls="c-connect">
                    "Cannot connect to CaseStrainer"
                  </button>
                </h3>
                <div id="c-connect" class="accordion-collapse collapse" aria-labelledby="h-connect" data-bs-parent="#troubleshootingAccordion">
                  <div class="accordion-body">
                    <ol class="mb-0">
                      <li>Check the Docker stack is running: <code>docker ps</code></li>
                      <li>Verify <code>CASESTRAINER_URL</code> in your MCP config matches the actual service address.</li>
                      <li>For local deployments the backend typically listens on <code>http://localhost:5001</code> behind Docker's port mapping, or <code>http://localhost:5000</code> if running directly.</li>
                    </ol>
                  </div>
                </div>
              </div>

              <div class="accordion-item">
                <h3 class="accordion-header" id="h-nokey">
                  <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#c-nokey" aria-expanded="false" aria-controls="c-nokey">
                    "Access denied: CASESTRAINER_MCP_KEY is not set"
                  </button>
                </h3>
                <div id="c-nokey" class="accordion-collapse collapse" aria-labelledby="h-nokey" data-bs-parent="#troubleshootingAccordion">
                  <div class="accordion-body">
                    The server has <code>MCP_API_KEYS</code> configured but this agent's MCP <code>env</code> block does not include <code>CASESTRAINER_MCP_KEY</code>.
                    Add the key to the agent's config file and restart the assistant.
                  </div>
                </div>
              </div>

              <div class="accordion-item">
                <h3 class="accordion-header" id="h-badkey">
                  <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#c-badkey" aria-expanded="false" aria-controls="c-badkey">
                    "Access denied: the key provided does not match"
                  </button>
                </h3>
                <div id="c-badkey" class="accordion-collapse collapse" aria-labelledby="h-badkey" data-bs-parent="#troubleshootingAccordion">
                  <div class="accordion-body">
                    The key value in the agent's config doesn't match any entry in <code>MCP_API_KEYS</code>.
                    Check for extra spaces and ensure the server's <code>.env</code> has been reloaded
                    (restart the MCP server process — the assistant will do this automatically on next use).
                  </div>
                </div>
              </div>

              <div class="accordion-item">
                <h3 class="accordion-header" id="h-timeout">
                  <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#c-timeout" aria-expanded="false" aria-controls="c-timeout">
                    Job timed out
                  </button>
                </h3>
                <div id="c-timeout" class="accordion-collapse collapse" aria-labelledby="h-timeout" data-bs-parent="#troubleshootingAccordion">
                  <div class="accordion-body">
                    <p>
                      <code>analyze_text</code> and <code>analyze_url</code> poll for up to
                      <code>CASESTRAINER_TIMEOUT</code> seconds (default 10 minutes).
                      For very large documents, increase this in the agent's <code>env</code> block:
                    </p>
                    <pre class="bg-light p-2 rounded border mb-2"><code>"CASESTRAINER_TIMEOUT": "1200"</code></pre>
                    <p class="mb-0">
                      If the job timed out but is still running, use <code>get_task_status</code>
                      with the task ID that was returned in the timeout message.
                    </p>
                  </div>
                </div>
              </div>

            </div>
          </div>
        </div>

        <!-- Links -->
        <div class="card mb-4">
          <div class="card-header bg-secondary text-white">
            <h2 class="mb-0 h5"><i class="bi bi-book me-2" aria-hidden="true"></i> More Information</h2>
          </div>
          <div class="card-body">
            <div class="list-group">
              <a href="https://github.com/jafrank88/casestrainer/blob/main/docs/MCP_SERVER.md"
                 target="_blank" rel="noopener noreferrer"
                 class="list-group-item list-group-item-action">
                <i class="bi bi-github me-2" aria-hidden="true"></i>
                Full MCP server documentation on GitHub
                <span class="visually-hidden">(opens in new tab)</span>
              </a>
              <a href="https://github.com/jafrank88/casestrainer/blob/main/casestrainer_mcp.py"
                 target="_blank" rel="noopener noreferrer"
                 class="list-group-item list-group-item-action">
                <i class="bi bi-code-slash me-2" aria-hidden="true"></i>
                MCP server source code (<code>casestrainer_mcp.py</code>)
                <span class="visually-hidden">(opens in new tab)</span>
              </a>
              <a href="https://github.com/jafrank88/casestrainer/blob/main/.claude/mcp_config_example.json"
                 target="_blank" rel="noopener noreferrer"
                 class="list-group-item list-group-item-action">
                <i class="bi bi-file-code me-2" aria-hidden="true"></i>
                Ready-to-paste config examples (<code>.claude/mcp_config_example.json</code>)
                <span class="visually-hidden">(opens in new tab)</span>
              </a>
              <router-link to="/docs/api" class="list-group-item list-group-item-action">
                <i class="bi bi-code-square me-2" aria-hidden="true"></i>
                REST API documentation (the endpoints the MCP server calls)
              </router-link>
              <a href="https://modelcontextprotocol.io/"
                 target="_blank" rel="noopener noreferrer"
                 class="list-group-item list-group-item-action">
                <i class="bi bi-box-arrow-up-right me-2" aria-hidden="true"></i>
                Model Context Protocol specification
                <span class="visually-hidden">(opens in new tab)</span>
              </a>
            </div>
          </div>
        </div>

        <div class="text-center mt-4">
          <router-link to="/docs" class="btn btn-outline-primary me-2">
            <i class="bi bi-arrow-left me-1" aria-hidden="true"></i> Back to Docs
          </router-link>
          <router-link to="/" class="btn btn-outline-secondary">
            <i class="bi bi-house me-1" aria-hidden="true"></i> Home
          </router-link>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
const claudeConfig = `{
  "mcpServers": {
    "casestrainer": {
      "command": "C:/path/to/casestrainer/venv-mcp/Scripts/python.exe",
      "args": ["C:/path/to/casestrainer/casestrainer_mcp.py"],
      "env": {
        "CASESTRAINER_URL": "http://localhost:5000"
      }
    }
  }
}`;

const authConfig = `{
  "mcpServers": {
    "casestrainer": {
      "command": "C:/path/to/casestrainer/venv-mcp/Scripts/python.exe",
      "args": ["C:/path/to/casestrainer/casestrainer_mcp.py"],
      "env": {
        "CASESTRAINER_URL": "http://localhost:5000",
        "CASESTRAINER_MCP_KEY": "your-agent-key-here"
      }
    }
  }
}`;
</script>
