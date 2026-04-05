// CaseStrainer — MV3 service worker: POST /analyze + optional task polling
'use strict';

const DEFAULT_API_BASE = 'https://wolf.law.uw.edu/casestrainer/api';

const DEFAULT_SETTINGS = {
  autoVerify: true,
  apiUrl: DEFAULT_API_BASE,
  highlightVerified: true,
  highlightUnverified: true,
  verifiedColor: '#28a745',
  unverifiedColor: '#dc3545',
  showConfidence: true,
};

function normalizeApiBase(url) {
  return String(url || DEFAULT_API_BASE).replace(/\/$/, '');
}

function analyzeUrlFromBase(base) {
  return `${normalizeApiBase(base)}/analyze`;
}

async function postAnalyze(analyzeUrl, text) {
  const res = await fetch(analyzeUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ type: 'text', text, force_mode: 'sync' }),
  });
  const raw = await res.text();
  let data;
  try {
    data = raw ? JSON.parse(raw) : {};
  } catch {
    throw new Error(`Invalid JSON (${res.status})`);
  }
  if (!res.ok) throw new Error(data.error || data.details || `HTTP ${res.status}`);
  return data;
}

async function pollTask(apiBase, taskId) {
  for (let i = 0; i < 90; i++) {
    const r = await fetch(`${apiBase}/task_status/${encodeURIComponent(taskId)}`);
    const raw = await r.text();
    let d = {};
    try {
      d = raw ? JSON.parse(raw) : {};
    } catch {
      throw new Error('task_status: invalid JSON');
    }
    if (!r.ok) throw new Error(d.error || `task_status ${r.status}`);
    if (d.status === 'completed' || d.status === 'failed' || d.status === 'error') return d;
    await new Promise((x) => setTimeout(x, 2000));
  }
  throw new Error('Analysis timed out');
}

async function analyzeText(apiBase, text) {
  const aurl = analyzeUrlFromBase(apiBase);
  const data = await postAnalyze(aurl, text);
  if (
    data.task_id &&
    (data.status === 'processing' || data.status === 'queued') &&
    (!Array.isArray(data.citations) || data.citations.length === 0)
  ) {
    return pollTask(normalizeApiBase(apiBase), data.task_id);
  }
  return data;
}

function rowsFromResponse(data) {
  const raw = data.citations || [];
  return raw.map((c) => ({
    citation: String(c.citation || c.text || '').trim(),
    verified: !!(c.verified === true || c.found === true || c.true_by_parallel === true),
    confidence:
      typeof c.confidence === 'number' ? (c.confidence > 1 ? c.confidence / 100 : c.confidence) : 0,
    canonical_name: c.canonical_name || c.extracted_case_name,
  }));
}

function mapRequestedCitations(data, requested) {
  const rows = rowsFromResponse(data).filter((r) => r.citation);
  const norm = (s) => s.replace(/\s+/g, ' ').trim().toLowerCase();
  const by = new Map();
  for (const r of rows) {
    by.set(norm(r.citation), r);
  }
  const out = {};
  for (const req of requested) {
    const n = norm(req);
    let m = by.get(n);
    if (!m) {
      for (const [k, v] of by) {
        if (k.includes(n) || n.includes(k)) {
          m = v;
          break;
        }
      }
    }
    const verified = !!(m && m.verified);
    let conf = m && typeof m.confidence === 'number' ? m.confidence : verified ? 0.82 : 0;
    if (conf > 1) conf /= 100;
    out[req] = {
      citation: req,
      verified,
      confidence: conf,
      caseName: m ? m.canonical_name : undefined,
    };
  }
  return out;
}

chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.sync.get('settings', (result) => {
    if (!result.settings) {
      chrome.storage.sync.set({ settings: DEFAULT_SETTINGS });
    }
  });
});

function updateBadge(tabId, count) {
  if (count > 0) {
    chrome.action.setBadgeText({ text: String(Math.min(count, 99)), tabId });
    chrome.action.setBadgeBackgroundColor({ color: '#0d6efd', tabId });
  } else {
    chrome.action.setBadgeText({ text: '', tabId });
  }
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'updateBadge') {
    if (sender.tab && sender.tab.id != null) {
      updateBadge(sender.tab.id, request.count);
    }
    sendResponse({ success: true });
    return true;
  }

  if (request.action === 'getSettings') {
    chrome.storage.sync.get('settings', (result) => {
      sendResponse({ success: true, data: result.settings || DEFAULT_SETTINGS });
    });
    return true;
  }

  if (request.action === 'verifyCitation') {
    const cite = request.citation;
    getSettings()
      .then((s) => analyzeText(s.apiUrl || DEFAULT_API_BASE, cite))
      .then((data) => {
        const mapped = mapRequestedCitations(data, [cite]);
        sendResponse({ success: true, data: mapped[cite] });
      })
      .catch((err) => sendResponse({ success: false, error: err.message }));
    return true;
  }

  if (request.action === 'batchVerify') {
    const citations = request.citations || [];
    const text = citations.join('\n\n');
    getSettings()
      .then((s) => analyzeText(s.apiUrl || DEFAULT_API_BASE, text))
      .then((data) => sendResponse({ success: true, data: mapRequestedCitations(data, citations) }))
      .catch((err) => sendResponse({ success: false, error: err.message }));
    return true;
  }

  return false;
});

function getSettings() {
  return new Promise((resolve) => {
    chrome.storage.sync.get('settings', (result) => {
      resolve(result.settings || DEFAULT_SETTINGS);
    });
  });
}

chrome.tabs.onUpdated.addListener((tabId, changeInfo) => {
  if (changeInfo.status === 'complete') {
    updateBadge(tabId, 0);
  }
});
