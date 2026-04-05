/**
 * Shared helpers for CaseStrainer Word task pane — POST /analyze + task polling.
 * Exposes CaseStrainerApi on globalThis for plain script tags (no bundler).
 */
(function (g) {
  'use strict';

  function normalizeAnalyzeUrl(endpoint) {
    const u = String(endpoint || '').trim().replace(/\/$/, '');
    if (!u) return '';
    return u.endsWith('/analyze') ? u : `${u}/analyze`;
  }

  function apiBaseFromAnalyze(analyzeUrl) {
    return analyzeUrl.replace(/\/analyze\/?$/i, '').replace(/\/$/, '');
  }

  async function postAnalyze(analyzeUrl, text) {
    const res = await fetch(analyzeUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        type: 'text',
        text,
        force_mode: 'sync',
      }),
    });
    const raw = await res.text();
    let data;
    try {
      data = raw ? JSON.parse(raw) : {};
    } catch {
      throw new Error(`API ${res.status}: invalid JSON`);
    }
    if (!res.ok) {
      throw new Error(data.error || data.details || `API ${res.status}: ${raw.slice(0, 200)}`);
    }
    return data;
  }

  async function pollUntilComplete(analyzeUrl, taskId) {
    const base = apiBaseFromAnalyze(analyzeUrl);
    for (let i = 0; i < 90; i++) {
      const r = await fetch(`${base}/task_status/${encodeURIComponent(taskId)}`);
      const raw = await r.text();
      let d;
      try {
        d = raw ? JSON.parse(raw) : {};
      } catch {
        throw new Error('task_status: invalid JSON');
      }
      if (!r.ok) throw new Error(d.error || `task_status ${r.status}`);
      if (d.status === 'completed' || d.status === 'failed' || d.status === 'error') return d;
      await new Promise((x) => setTimeout(x, 2000));
    }
    throw new Error('Timed out waiting for analysis');
  }

  async function analyzeText(analyzeUrl, text) {
    const url = normalizeAnalyzeUrl(analyzeUrl);
    const data = await postAnalyze(url, text);
    if (
      data.task_id &&
      (data.status === 'processing' || data.status === 'queued') &&
      (!Array.isArray(data.citations) || data.citations.length === 0)
    ) {
      return pollUntilComplete(url, data.task_id);
    }
    return data;
  }

  function citationsFromResponse(data) {
    const raw = data.citations || [];
    return raw
      .map((c) => {
        const text = String(c.citation || c.text || '').trim();
        if (!text) return null;
        const verified = !!(c.verified === true || c.found === true || c.true_by_parallel === true);
        let conf = typeof c.confidence === 'number' ? c.confidence : 0;
        if (conf > 1) conf = conf / 100;
        return {
          text,
          verified,
          confidence: conf,
          canonical_name: c.canonical_name || c.extracted_case_name || '',
        };
      })
      .filter(Boolean);
  }

  g.CaseStrainerApi = {
    normalizeAnalyzeUrl,
    apiBaseFromAnalyze,
    analyzeText,
    citationsFromResponse,
  };
})(typeof globalThis !== 'undefined' ? globalThis : window);
