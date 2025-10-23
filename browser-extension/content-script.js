// CaseStrainer Content Script - Citation Detection and Highlighting
// Runs on legal websites to detect and verify citations

(function() {
  'use strict';
  
  // Citation detection patterns
  const CITATION_PATTERNS = [
    // US Reports: 123 U.S. 456
    /\b\d{1,3}\s+U\.?S\.?\s+\d{1,4}\b/gi,
    // Federal Reporter: 123 F.2d 456 or 123 F.3d 456
    /\b\d{1,3}\s+F\.\s?(?:2d|3d|4th|App\'?x\.?)\s+\d{1,4}\b/gi,
    // Supreme Court Reporter: 123 S.Ct. 456
    /\b\d{1,3}\s+S\.?\s?Ct\.?\s+\d{1,4}\b/gi,
    // Washington Reports: 123 Wash. 2d 456 or 123 Wn.2d 456
    /\b\d{1,3}\s+(?:Wash\.|Wn\.?)\s*2d\s+\d{1,4}\b/gi,
    // California Reporter: 123 Cal.App.4th 456
    /\b\d{1,3}\s+Cal\.?\s?(?:App\.?\s?)?(?:\d)(?:st|d|th)\s+\d{1,4}\b/gi,
    // New York Reports: 123 N.Y.2d 456
    /\b\d{1,3}\s+N\.?Y\.?\s?(?:2d|3d)?\s+\d{1,4}\b/gi,
    // Generic state reporter: 123 [State] 2d 456
    /\b\d{1,3}\s+[A-Z][a-z]{1,10}\.?\s*(?:2d|3d)?\s+\d{1,4}\b/gi
  ];
  
  let detectedCitations = new Set();
  let verifiedCitations = {};
  let settings = null;
  
  // Initialize
  init();
  
  function init() {
    console.log('CaseStrainer: Content script loaded');
    loadSettings().then(() => {
      if (settings && settings.autoVerify) {
        detectAndVerifyCitations();
      }
    });
  }
  
  // Load settings from background
  async function loadSettings() {
    return new Promise((resolve) => {
      chrome.runtime.sendMessage({ action: 'getSettings' }, (response) => {
        if (response && response.success) {
          settings = response.data;
        }
        resolve();
      });
    });
  }
  
  // Detect citations on the page
  function detectCitations() {
    const citations = new Set();
    const textNodes = getTextNodes(document.body);
    
    textNodes.forEach(node => {
      const text = node.textContent;
      CITATION_PATTERNS.forEach(pattern => {
        const matches = text.match(pattern);
        if (matches) {
          matches.forEach(match => {
            const cleaned = match.trim();
            if (cleaned.length > 0) {
              citations.add(cleaned);
            }
          });
        }
      });
    });
    
    return Array.from(citations);
  }
  
  // Get all text nodes in element
  function getTextNodes(element) {
    const textNodes = [];
    const walker = document.createTreeWalker(
      element,
      NodeFilter.SHOW_TEXT,
      {
        acceptNode: function(node) {
          // Skip script and style elements
          if (node.parentElement.tagName === 'SCRIPT' ||
              node.parentElement.tagName === 'STYLE' ||
              node.parentElement.tagName === 'NOSCRIPT') {
            return NodeFilter.FILTER_REJECT;
          }
          // Skip nodes that are already highlighted
          if (node.parentElement.classList.contains('casestrainer-citation')) {
            return NodeFilter.FILTER_REJECT;
          }
          return NodeFilter.FILTER_ACCEPT;
        }
      }
    );
    
    let node;
    while (node = walker.nextNode()) {
      textNodes.push(node);
    }
    
    return textNodes;
  }
  
  // Detect and verify all citations
  async function detectAndVerifyCitations() {
    const citations = detectCitations();
    console.log(`CaseStrainer: Found ${citations.length} citations`);
    
    if (citations.length === 0) {
      return;
    }
    
    detectedCitations = new Set(citations);
    
    // Update badge
    chrome.runtime.sendMessage({
      action: 'updateBadge',
      count: citations.length
    });
    
    // Verify in batches of 10
    const batchSize = 10;
    for (let i = 0; i < citations.length; i += batchSize) {
      const batch = citations.slice(i, i + batchSize);
      await verifyBatch(batch);
    }
    
    // Highlight all citations
    highlightCitations();
  }
  
  // Verify a batch of citations
  async function verifyBatch(citations) {
    return new Promise((resolve) => {
      chrome.runtime.sendMessage({
        action: 'batchVerify',
        citations: citations
      }, (response) => {
        if (response && response.success) {
          Object.assign(verifiedCitations, response.data);
        }
        resolve();
      });
    });
  }
  
  // Highlight citations on the page
  function highlightCitations() {
    if (!settings) return;
    
    const textNodes = getTextNodes(document.body);
    
    textNodes.forEach(node => {
      let text = node.textContent;
      let newHTML = text;
      let hasMatches = false;
      
      // Check each detected citation
      detectedCitations.forEach(citation => {
        const regex = new RegExp(escapeRegex(citation), 'gi');
        if (regex.test(text)) {
          hasMatches = true;
          const result = verifiedCitations[citation];
          const verified = result ? result.verified : false;
          const confidence = result ? result.confidence : 0;
          
          // Determine color based on verification status
          let color = '#6c757d'; // gray for unverified
          if (verified && settings.highlightVerified) {
            color = settings.verifiedColor || '#28a745';
          } else if (!verified && settings.highlightUnverified) {
            color = settings.unverifiedColor || '#dc3545';
          }
          
          const title = result ?
            `${verified ? 'Verified' : 'Unverified'} (Confidence: ${Math.round(confidence * 100)}%)` :
            'Not yet verified';
          
          newHTML = newHTML.replace(regex, (match) => {
            return `<span class="casestrainer-citation" style="background-color: ${color}20; border-bottom: 2px solid ${color}; cursor: help;" title="${title}">${match}</span>`;
          });
        }
      });
      
      if (hasMatches) {
        const span = document.createElement('span');
        span.innerHTML = newHTML;
        node.parentNode.replaceChild(span, node);
      }
    });
  }
  
  // Escape special regex characters
  function escapeRegex(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }
  
  // Listen for messages from popup
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'getCitations') {
      sendResponse({
        success: true,
        data: {
          detected: Array.from(detectedCitations),
          verified: verifiedCitations
        }
      });
    }
    
    if (request.action === 'reanalyze') {
      detectAndVerifyCitations().then(() => {
        sendResponse({ success: true });
      });
      return true;
    }
  });
  
  // Observe DOM changes for dynamically loaded content
  const observer = new MutationObserver((mutations) => {
    if (settings && settings.autoVerify) {
      // Debounce to avoid excessive processing
      clearTimeout(observer.timeout);
      observer.timeout = setTimeout(() => {
        detectAndVerifyCitations();
      }, 1000);
    }
  });
  
  observer.observe(document.body, {
    childList: true,
    subtree: true
  });
  
})();
