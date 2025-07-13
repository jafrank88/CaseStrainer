// State management
let state = {
  isProcessing: false,
  citations: [],
  settings: {
    autoValidate: false,
    highlightCitations: true,
    apiEndpoint: 'http://localhost:5000/api/analyze'
  }
};

// DOM Elements
const elements = {
  validateButton: document.getElementById('validatePage'),
  statusDot: document.querySelector('.status-dot'),
  statusText: document.querySelector('.status-text'),
  resultsContainer: document.getElementById('citationResults'),
  autoValidateCheckbox: document.getElementById('autoValidate'),
  highlightCitationsCheckbox: document.getElementById('highlightCitations'),
  apiEndpointInput: document.getElementById('apiEndpoint'),
  openOptionsButton: document.getElementById('openOptions')
};

// Initialize popup
async function initialize() {
  // Load saved settings
  const savedSettings = await chrome.storage.sync.get('settings');
  if (savedSettings.settings) {
    state.settings = { ...state.settings, ...savedSettings.settings };
    updateSettingsUI();
  }

  // Add event listeners
  elements.validateButton.addEventListener('click', validateCurrentPage);
  elements.autoValidateCheckbox.addEventListener('change', updateSettings);
  elements.highlightCitationsCheckbox.addEventListener('change', updateSettings);
  elements.apiEndpointInput.addEventListener('change', updateSettings);
  elements.openOptionsButton.addEventListener('click', openOptionsPage);

  // Check if auto-validate is enabled
  if (state.settings.autoValidate) {
    validateCurrentPage();
  }
}

// Update settings UI to match state
function updateSettingsUI() {
  elements.autoValidateCheckbox.checked = state.settings.autoValidate;
  elements.highlightCitationsCheckbox.checked = state.settings.highlightCitations;
  elements.apiEndpointInput.value = state.settings.apiEndpoint;
}

// Update settings from UI
async function updateSettings() {
  state.settings = {
    autoValidate: elements.autoValidateCheckbox.checked,
    highlightCitations: elements.highlightCitationsCheckbox.checked,
    apiEndpoint: elements.apiEndpointInput.value
  };

  // Save settings
  await chrome.storage.sync.set({ settings: state.settings });

  // Notify content script of settings change
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tab) {
    chrome.tabs.sendMessage(tab.id, { type: 'SETTINGS_UPDATED', settings: state.settings });
  }
}

// Validate current page
async function validateCurrentPage() {
  if (state.isProcessing) return;

  try {
    setProcessingState(true);
    
    // Get current tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab) throw new Error('No active tab found');

    // Get page content
    const [{result}] = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      function: () => document.body.innerText
    });

    // Send to API
    const response = await fetch(state.settings.apiEndpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: result })
    });

    if (!response.ok) throw new Error('API request failed');

    const data = await response.json();
    state.citations = data.citations || [];

    // Update UI
    updateResultsUI();
    
    // Highlight citations if enabled
    if (state.settings.highlightCitations) {
      chrome.tabs.sendMessage(tab.id, {
        type: 'HIGHLIGHT_CITATIONS',
        citations: state.citations
      });
    }

  } catch (error) {
    console.error('Validation error:', error);
    showError(error.message);
  } finally {
    setProcessingState(false);
  }
}

// Update results UI
function updateResultsUI() {
  const container = elements.resultsContainer;
  
  if (!state.citations.length) {
    container.innerHTML = `
      <div class="empty-state">
        <p>No citations found</p>
        <p class="hint">Try a different page or document</p>
      </div>
    `;
    return;
  }

  container.innerHTML = state.citations.map(citation => `
    <div class="citation-item ${citation.verified ? 'verified' : 'unverified'}">
      <div class="citation-text">${citation.text}</div>
      <div class="citation-status">
        ${citation.verified ? '✓ Verified' : '⚠ Unverified'}
        ${citation.canonical_name ? ` - ${citation.canonical_name}` : ''}
      </div>
    </div>
  `).join('');
}

// Set processing state
function setProcessingState(isProcessing) {
  state.isProcessing = isProcessing;
  elements.validateButton.disabled = isProcessing;
  elements.statusDot.style.background = isProcessing ? 'var(--warning-color)' : 'var(--success-color)';
  elements.statusText.textContent = isProcessing ? 'Processing...' : 'Ready';
}

// Show error
function showError(message) {
  elements.statusDot.style.background = 'var(--error-color)';
  elements.statusText.textContent = 'Error';
  elements.resultsContainer.innerHTML = `
    <div class="citation-item error">
      <div class="citation-text">Error</div>
      <div class="citation-status">${message}</div>
    </div>
  `;
}

// Open options page
function openOptionsPage() {
  chrome.runtime.openOptionsPage();
}

// Initialize popup when DOM is loaded
document.addEventListener('DOMContentLoaded', initialize); 