/* global CaseStrainerApi, Office, Word */
'use strict';

const DEFAULT_ANALYZE =
  'https://wolf.law.uw.edu/casestrainer/api/analyze';

const state = {
  settings: {
    autoValidate: false,
    highlightCitations: true,
    apiEndpoint: DEFAULT_ANALYZE,
  },
  citations: [],
  isProcessing: false,
};

Office.onReady((info) => {
  if (info.host === Office.HostType.Word) {
    loadSettings();
    initializeUI();
    setupEventListeners();
  }
});

function loadSettings() {
  try {
    const s = Office.context.roamingSettings.get('casestrainer_settings');
    if (s) {
      const parsed = JSON.parse(s);
      state.settings = { ...state.settings, ...parsed };
    }
  } catch (e) {
    console.error('loadSettings', e);
  }
}

function saveSettings() {
  try {
    Office.context.roamingSettings.set('casestrainer_settings', JSON.stringify(state.settings));
    Office.context.roamingSettings.saveAsync((r) => {
      if (r.status === Office.AsyncResultStatus.Failed) console.error(r.errorMessage);
    });
  } catch (e) {
    console.error('saveSettings', e);
  }
}

function initializeUI() {
  document.getElementById('auto-validate').checked = state.settings.autoValidate;
  document.getElementById('highlight-citations').checked = state.settings.highlightCitations;
  document.getElementById('api-endpoint').value = state.settings.apiEndpoint;
  updateResultsUI();
  updateStatus('Ready. Click Validate to analyze the document (or a selection).');
}

function setupEventListeners() {
  document.getElementById('validate-button').addEventListener('click', () => validateDocument());
  document.getElementById('clear-button').addEventListener('click', () => clearHighlights());

  document.getElementById('auto-validate').addEventListener('change', (e) => {
    state.settings.autoValidate = e.target.checked;
    saveSettings();
    updateStatus(
      state.settings.autoValidate
        ? 'Auto-validate on selection change is experimental; prefer Validate button for large documents.'
        : 'Auto-validate off.'
    );
  });

  document.getElementById('highlight-citations').addEventListener('change', (e) => {
    state.settings.highlightCitations = e.target.checked;
    saveSettings();
    if (!state.settings.highlightCitations) clearHighlights();
  });

  document.getElementById('api-endpoint').addEventListener('change', (e) => {
    state.settings.apiEndpoint = e.target.value.trim() || DEFAULT_ANALYZE;
    saveSettings();
  });
}

async function getContentForValidation() {
  if (typeof Word === 'undefined') {
    return getSelectionLegacy().then((sel) => sel || getBodyTextLegacy());
  }
  return Word.run(async (context) => {
    const range = context.document.getSelection();
    range.load('text');
    await context.sync();
    const sel = (range.text || '').trim();
    if (sel.length >= 40) return sel;
    const body = context.document.body;
    body.load('text');
    await context.sync();
    return (body.text || '').trim();
  });
}

function getSelectionLegacy() {
  return new Promise((resolve) => {
    Office.context.document.getSelectedDataAsync(Office.CoercionType.Text, { valueFormat: 'unformatted' }, (r) => {
      if (r.status === Office.AsyncResultStatus.Succeeded) resolve((r.value || '').trim());
      else resolve('');
    });
  });
}

function getBodyTextLegacy() {
  return new Promise((resolve, reject) => {
    if (!Office.context.document.body.getTextAsync) {
      reject(new Error('Word API not available'));
      return;
    }
    Office.context.document.body.getTextAsync({ valueFormat: 'unformatted' }, (r) => {
      if (r.status === Office.AsyncResultStatus.Succeeded) resolve((r.value || '').trim());
      else reject(new Error('Could not read document'));
    });
  });
}

async function validateDocument() {
  if (state.isProcessing) return;
  state.isProcessing = true;
  showLoading(true);
  updateProgress(10);
  updateStatus('Reading document…');

  try {
    const text = await getContentForValidation();
    if (!text || text.length < 8) {
      throw new Error('No text to analyze. Select a passage or ensure the document has body text.');
    }
    updateProgress(35);
    updateStatus('Calling CaseStrainer API…');

    const analyzeUrl = CaseStrainerApi.normalizeAnalyzeUrl(state.settings.apiEndpoint);
    const data = await CaseStrainerApi.analyzeText(analyzeUrl, text);
    state.citations = CaseStrainerApi.citationsFromResponse(data);

    updateProgress(85);
    updateResultsUI();

    if (state.settings.highlightCitations && state.citations.length) {
      updateStatus('Highlighting citations…');
      await highlightCitationsWord();
    }

    updateProgress(100);
    const v = state.citations.filter((c) => c.verified).length;
    updateStatus(`Done — ${state.citations.length} citation(s), ${v} verified.`);
  } catch (e) {
    console.error(e);
    updateStatus(e.message || String(e), 'error');
  } finally {
    state.isProcessing = false;
    showLoading(false);
    setTimeout(() => updateProgress(0), 800);
  }
}

async function highlightCitationsWord() {
  if (typeof Word === 'undefined') {
    updateStatus('Highlighting requires Word API 1.1+ (Word.run).', 'error');
    return;
  }
  await Word.run(async (context) => {
    for (const c of state.citations) {
      if (!c.text) continue;
      const search = context.document.body.search(c.text, { matchCase: false, matchWholeWord: false });
      search.load('items');
      await context.sync();
      for (let i = 0; i < search.items.length; i++) {
        search.items[i].font.highlightColor = c.verified ? '#C6EFCE' : '#FFC7CE';
      }
    }
    await context.sync();
  });
}

async function clearHighlights() {
  if (typeof Word === 'undefined') {
    updateStatus('Clear highlights requires Word.run API.', 'error');
    return;
  }
  const texts = state.citations.map((c) => c.text).filter(Boolean);
  if (!texts.length) {
    updateStatus('No citations in memory to clear. Run Validate first.');
    return;
  }
  try {
    await Word.run(async (context) => {
      for (const fragment of texts) {
        const search = context.document.body.search(fragment, { matchCase: false, matchWholeWord: false });
        search.load('items');
        await context.sync();
        for (let i = 0; i < search.items.length; i++) {
          search.items[i].font.highlightColor = 'White';
        }
      }
      await context.sync();
    });
    updateStatus('Removed highlights for the last validated citation strings.');
  } catch (e) {
    console.error(e);
    updateStatus('Could not clear highlights: ' + e.message, 'error');
  }
}

function updateResultsUI() {
  const total = state.citations.length;
  const verified = state.citations.filter((c) => c.verified).length;
  document.getElementById('total-citations').textContent = String(total);
  document.getElementById('verified-citations').textContent = String(verified);
  document.getElementById('unverified-citations').textContent = String(total - verified);

  const list = document.getElementById('citations-list');
  list.innerHTML = '';
  state.citations.forEach((c) => {
    const row = document.createElement('div');
    row.className = 'citation-item';
    const t = document.createElement('div');
    t.className = 'citation-text';
    t.textContent = c.text;
    const st = document.createElement('div');
    st.className = 'citation-status ' + (c.verified ? 'verified' : 'unverified');
    st.textContent = c.verified ? 'Verified' : 'Unverified';
    row.appendChild(t);
    row.appendChild(st);
    if (c.canonical_name) {
      const cn = document.createElement('div');
      cn.className = 'citation-meta';
      cn.textContent = c.canonical_name;
      row.appendChild(cn);
    }
    list.appendChild(row);
  });
}

function updateStatus(message, type) {
  const el = document.getElementById('status-message');
  el.textContent = message;
  el.className = 'status-message' + (type === 'error' ? ' error' : '');
}

function updateProgress(pct) {
  const bar = document.getElementById('progress-bar');
  const txt = document.getElementById('progress-text');
  const wrap = document.getElementById('progress-container');
  wrap.style.display = pct > 0 ? 'block' : 'none';
  bar.style.width = `${pct}%`;
  txt.textContent = `${pct}%`;
}

function showLoading(on) {
  document.getElementById('loading-spinner').style.display = on ? 'flex' : 'none';
}
