// State management
let state = {
  settings: {
    highlightCitations: true,
    apiEndpoint: 'http://localhost:5000/api/analyze'
  },
  citations: [],
  highlights: new Map() // Map of citation text to highlight elements
};

// Initialize content script
async function initialize() {
  // Load saved settings
  const savedSettings = await chrome.storage.sync.get('settings');
  if (savedSettings.settings) {
    state.settings = { ...state.settings, ...savedSettings.settings };
  }

  // Listen for messages from popup
  chrome.runtime.onMessage.addListener(handleMessage);

  // Add mutation observer to handle dynamic content
  const observer = new MutationObserver(handleDOMChanges);
  observer.observe(document.body, {
    childList: true,
    subtree: true,
    characterData: true
  });
}

// Handle messages from popup
function handleMessage(message, sender, sendResponse) {
  switch (message.type) {
    case 'HIGHLIGHT_CITATIONS':
      state.citations = message.citations;
      if (state.settings.highlightCitations) {
        highlightCitations();
      }
      break;

    case 'SETTINGS_UPDATED':
      state.settings = { ...state.settings, ...message.settings };
      if (state.settings.highlightCitations) {
        highlightCitations();
      } else {
        removeHighlights();
      }
      break;
  }
}

// Handle DOM changes
function handleDOMChanges(mutations) {
  if (!state.settings.highlightCitations || !state.citations.length) return;

  // Check if any mutations might affect our highlights
  const shouldRehighlight = mutations.some(mutation => {
    // If nodes were added/removed
    if (mutation.type === 'childList') return true;
    
    // If text content changed
    if (mutation.type === 'characterData') {
      const node = mutation.target;
      // Check if the changed node is part of a highlighted citation
      return Array.from(state.highlights.values()).some(highlight => 
        highlight.contains(node) || node.contains(highlight)
      );
    }
    
    return false;
  });

  if (shouldRehighlight) {
    // Debounce rehighlighting
    clearTimeout(window._rehighlightTimeout);
    window._rehighlightTimeout = setTimeout(highlightCitations, 250);
  }
}

// Highlight citations in the page
function highlightCitations() {
  // Remove existing highlights first
  removeHighlights();

  // Create a tree walker to find text nodes
  const walker = document.createTreeWalker(
    document.body,
    NodeFilter.SHOW_TEXT,
    {
      acceptNode: function(node) {
        // Skip script and style tags
        if (node.parentElement.tagName === 'SCRIPT' || 
            node.parentElement.tagName === 'STYLE') {
          return NodeFilter.FILTER_REJECT;
        }
        return NodeFilter.FILTER_ACCEPT;
      }
    }
  );

  // Process each text node
  let node;
  while (node = walker.nextNode()) {
    const text = node.textContent;
    
    // Check each citation
    for (const citation of state.citations) {
      const index = text.indexOf(citation.text);
      if (index === -1) continue;

      // Split the text node
      const before = text.slice(0, index);
      const after = text.slice(index + citation.text.length);
      
      // Create new nodes
      const beforeNode = document.createTextNode(before);
      const afterNode = document.createTextNode(after);
      
      // Create highlight element
      const highlight = document.createElement('span');
      highlight.className = `casestrainer-citation ${citation.verified ? 'verified' : 'unverified'}`;
      highlight.textContent = citation.text;
      highlight.title = citation.verified ? 
        `Verified: ${citation.case_name || citation.text}` :
        `Unverified: ${citation.case_name || citation.text}`;
      
      // Store highlight element
      state.highlights.set(citation.text, highlight);
      
      // Replace the original node
      const parent = node.parentNode;
      parent.insertBefore(beforeNode, node);
      parent.insertBefore(highlight, node);
      parent.insertBefore(afterNode, node);
      parent.removeChild(node);
      
      // Update walker to point to the new after node
      walker.currentNode = afterNode;
    }
  }

  // Add styles if not already present
  if (!document.getElementById('casestrainer-styles')) {
    const style = document.createElement('style');
    style.id = 'casestrainer-styles';
    style.textContent = `
      .casestrainer-citation {
        padding: 2px 4px;
        border-radius: 3px;
        cursor: help;
        transition: background-color 0.2s;
      }
      .casestrainer-citation.verified {
        background-color: rgba(46, 204, 113, 0.2);
        border-bottom: 2px solid #2ecc71;
      }
      .casestrainer-citation.unverified {
        background-color: rgba(241, 196, 15, 0.2);
        border-bottom: 2px solid #f1c40f;
      }
      .casestrainer-citation:hover {
        background-color: rgba(52, 152, 219, 0.2);
      }
    `;
    document.head.appendChild(style);
  }
}

// Remove all highlights
function removeHighlights() {
  for (const highlight of state.highlights.values()) {
    const parent = highlight.parentNode;
    if (parent) {
      // Replace highlight with its text content
      const textNode = document.createTextNode(highlight.textContent);
      parent.replaceChild(textNode, highlight);
    }
  }
  state.highlights.clear();
}

// Initialize when content script loads
initialize(); 