// CaseStrainer Options Page

const DEFAULT_SETTINGS = {
  autoVerify: true,
  apiUrl: 'https://wolf.law.uw.edu/casestrainer/api',
  highlightVerified: true,
  highlightUnverified: true,
  verifiedColor: '#28a745',
  unverifiedColor: '#dc3545',
  showConfidence: true
};

// Load saved settings
document.addEventListener('DOMContentLoaded', () => {
  loadSettings();
  
  // Save button
  document.getElementById('settingsForm').addEventListener('submit', (e) => {
    e.preventDefault();
    saveSettings();
  });
  
  // Reset button
  document.getElementById('resetButton').addEventListener('click', () => {
    if (confirm('Reset all settings to defaults?')) {
      resetSettings();
    }
  });
});

// Load settings from storage
function loadSettings() {
  chrome.storage.sync.get('settings', (result) => {
    const settings = result.settings || DEFAULT_SETTINGS;
    
    document.getElementById('autoVerify').checked = settings.autoVerify;
    document.getElementById('showConfidence').checked = settings.showConfidence;
    document.getElementById('apiUrl').value = settings.apiUrl;
    document.getElementById('highlightVerified').checked = settings.highlightVerified;
    document.getElementById('highlightUnverified').checked = settings.highlightUnverified;
    document.getElementById('verifiedColor').value = settings.verifiedColor;
    document.getElementById('unverifiedColor').value = settings.unverifiedColor;
  });
}

// Save settings to storage
function saveSettings() {
  const settings = {
    autoVerify: document.getElementById('autoVerify').checked,
    showConfidence: document.getElementById('showConfidence').checked,
    apiUrl: document.getElementById('apiUrl').value,
    highlightVerified: document.getElementById('highlightVerified').checked,
    highlightUnverified: document.getElementById('highlightUnverified').checked,
    verifiedColor: document.getElementById('verifiedColor').value,
    unverifiedColor: document.getElementById('unverifiedColor').value
  };
  
  chrome.storage.sync.set({ settings: settings }, () => {
    showSuccessMessage();
  });
}

// Reset to default settings
function resetSettings() {
  chrome.storage.sync.set({ settings: DEFAULT_SETTINGS }, () => {
    loadSettings();
    showSuccessMessage();
  });
}

// Show success message
function showSuccessMessage() {
  const message = document.getElementById('successMessage');
  message.classList.add('show');
  
  setTimeout(() => {
    message.classList.remove('show');
  }, 3000);
}
