// CaseStrainer Browser Extension - Background Service Worker
// Handles API requests and manages extension state

const API_BASE_URL = 'https://wolf.law.uw.edu/casestrainer/api';

// Default settings
const DEFAULT_SETTINGS = {
  autoVerify: true,
  apiUrl: API_BASE_URL,
  highlightVerified: true,
  highlightUnverified: true,
  verifiedColor: '#28a745',
  unverifiedColor: '#dc3545',
  showConfidence: true
};

// Initialize extension
chrome.runtime.onInstalled.addListener(() => {
  console.log('CaseStrainer extension installed');
  
  // Set default settings
  chrome.storage.sync.get('settings', (result) => {
    if (!result.settings) {
      chrome.storage.sync.set({ settings: DEFAULT_SETTINGS });
    }
  });
});

// Handle messages from content scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'verifyCitation') {
    verifyCitation(request.citation)
      .then(result => sendResponse({ success: true, data: result }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true; // Keep channel open for async response
  }
  
  if (request.action === 'batchVerify') {
    batchVerifyCitations(request.citations)
      .then(results => sendResponse({ success: true, data: results }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true;
  }
  
  if (request.action === 'getSettings') {
    chrome.storage.sync.get('settings', (result) => {
      sendResponse({ success: true, data: result.settings || DEFAULT_SETTINGS });
    });
    return true;
  }
});

// Verify a single citation using CaseStrainer API
async function verifyCitation(citation) {
  try {
    const settings = await getSettings();
    const apiUrl = settings.apiUrl || API_BASE_URL;
    
    const response = await fetch(`${apiUrl}/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        text: citation,
        source_type: 'text'
      })
    });
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    
    const data = await response.json();
    return parseCitationResult(data, citation);
  } catch (error) {
    console.error('Citation verification error:', error);
    throw error;
  }
}

// Batch verify multiple citations
async function batchVerifyCitations(citations) {
  try {
    const settings = await getSettings();
    const apiUrl = settings.apiUrl || API_BASE_URL;
    
    // Combine citations into single text
    const text = citations.join(' ');
    
    const response = await fetch(`${apiUrl}/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        text: text,
        source_type: 'text'
      })
    });
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    
    const data = await response.json();
    return parseBatchResults(data, citations);
  } catch (error) {
    console.error('Batch verification error:', error);
    throw error;
  }
}

// Parse API result for single citation
function parseCitationResult(data, citation) {
  if (!data.results || data.results.length === 0) {
    return {
      citation: citation,
      verified: false,
      confidence: 0,
      message: 'No results found'
    };
  }
  
  const result = data.results[0];
  return {
    citation: result.citation || citation,
    verified: result.exists || !result.is_hallucinated,
    confidence: result.confidence || 0,
    caseName: result.case_name,
    method: result.method,
    similarityScore: result.similarity_score
  };
}

// Parse batch API results
function parseBatchResults(data, citations) {
  const results = {};
  
  if (!data.results || data.results.length === 0) {
    citations.forEach(cit => {
      results[cit] = {
        citation: cit,
        verified: false,
        confidence: 0,
        message: 'No results found'
      };
    });
    return results;
  }
  
  data.results.forEach(result => {
    const citation = result.citation;
    results[citation] = {
      citation: citation,
      verified: result.exists || !result.is_hallucinated,
      confidence: result.confidence || 0,
      caseName: result.case_name,
      method: result.method,
      similarityScore: result.similarity_score
    };
  });
  
  // Fill in missing citations
  citations.forEach(cit => {
    if (!results[cit]) {
      results[cit] = {
        citation: cit,
        verified: false,
        confidence: 0,
        message: 'Not verified'
      };
    }
  });
  
  return results;
}

// Get settings from storage
async function getSettings() {
  return new Promise((resolve) => {
    chrome.storage.sync.get('settings', (result) => {
      resolve(result.settings || DEFAULT_SETTINGS);
    });
  });
}

// Badge to show number of citations found
function updateBadge(tabId, count) {
  if (count > 0) {
    chrome.action.setBadgeText({ text: count.toString(), tabId: tabId });
    chrome.action.setBadgeBackgroundColor({ color: '#0d6efd', tabId: tabId });
  } else {
    chrome.action.setBadgeText({ text: '', tabId: tabId });
  }
}

// Listen for tab updates to reset badge
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete') {
    updateBadge(tabId, 0);
  }
});
