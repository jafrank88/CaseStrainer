// CaseStrainer Popup - Display verified citations

document.addEventListener('DOMContentLoaded', () => {
  loadCitations();
  
  // Re-analyze button
  document.getElementById('reanalyze').addEventListener('click', () => {
    reanalyzePage();
  });
  
  // Settings button
  document.getElementById('openOptions').addEventListener('click', () => {
    chrome.runtime.openOptionsPage();
  });
});

// Load citations from active tab
function loadCitations() {
  showLoading(true);
  hideError();
  
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (tabs.length === 0) {
      showError('No active tab found');
      showLoading(false);
      return;
    }
    
    chrome.tabs.sendMessage(tabs[0].id, { action: 'getCitations' }, (response) => {
      showLoading(false);
      
      if (chrome.runtime.lastError) {
        showError('Content script not loaded. Try refreshing the page.');
        return;
      }
      
      if (response && response.success) {
        displayCitations(response.data);
      } else {
        showError('Failed to load citations');
      }
    });
  });
}

// Display citations in the popup
function displayCitations(data) {
  const { detected, verified } = data;
  const totalCount = detected.length;
  let verifiedCount = 0;
  let unverifiedCount = 0;
  
  // Update stats
  document.getElementById('totalCitations').textContent = totalCount;
  
  // Build citations list
  const listElement = document.getElementById('citationsList');
  listElement.innerHTML = '';
  
  if (totalCount === 0) {
    listElement.innerHTML = '<p style="text-align: center; color: #6c757d; padding: 20px;">No citations found on this page.</p>';
    return;
  }
  
  detected.forEach(citation => {
    const result = verified[citation];
    const isVerified = result ? result.verified : false;
    const confidence = result ? result.confidence : 0;
    
    if (isVerified) {
      verifiedCount++;
    } else {
      unverifiedCount++;
    }
    
    const item = createCitationElement(citation, isVerified, confidence, result);
    listElement.appendChild(item);
  });
  
  // Update counts
  document.getElementById('verifiedCount').textContent = verifiedCount;
  document.getElementById('unverifiedCount').textContent = unverifiedCount;
}

// Create citation list item element
function createCitationElement(citation, isVerified, confidence, result) {
  const div = document.createElement('div');
  div.className = `citation-item ${isVerified ? 'verified' : 'unverified'}`;
  
  const citationText = document.createElement('div');
  citationText.className = 'citation-text';
  citationText.textContent = citation;
  
  const status = document.createElement('div');
  status.className = 'citation-status';
  
  const badge = document.createElement('span');
  badge.className = `status-badge ${isVerified ? 'verified' : 'unverified'}`;
  badge.textContent = isVerified ? '✓ Verified' : '✗ Unverified';
  
  const confidenceSpan = document.createElement('span');
  confidenceSpan.className = 'confidence';
  confidenceSpan.textContent = `${Math.round(confidence * 100)}% confidence`;
  
  status.appendChild(badge);
  if (result) {
    status.appendChild(confidenceSpan);
  }
  
  div.appendChild(citationText);
  div.appendChild(status);
  
  // Add case name if available
  if (result && result.caseName) {
    const caseName = document.createElement('div');
    caseName.style.fontSize = '12px';
    caseName.style.color = '#6c757d';
    caseName.style.marginTop = '4px';
    caseName.textContent = result.caseName;
    div.appendChild(caseName);
  }
  
  return div;
}

// Re-analyze current page
function reanalyzePage() {
  showLoading(true);
  hideError();
  
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (tabs.length === 0) {
      showError('No active tab found');
      showLoading(false);
      return;
    }
    
    chrome.tabs.sendMessage(tabs[0].id, { action: 'reanalyze' }, (response) => {
      if (chrome.runtime.lastError) {
        showLoading(false);
        showError('Content script not loaded. Try refreshing the page.');
        return;
      }
      
      // Wait a bit for processing
      setTimeout(() => {
        loadCitations();
      }, 2000);
    });
  });
}

// Show/hide loading indicator
function showLoading(show) {
  document.getElementById('loading').style.display = show ? 'block' : 'none';
  document.getElementById('citationsList').style.display = show ? 'none' : 'block';
}

// Show error message
function showError(message) {
  const errorElement = document.getElementById('error');
  errorElement.textContent = message;
  errorElement.style.display = 'block';
}

// Hide error message
function hideError() {
  document.getElementById('error').style.display = 'none';
}
