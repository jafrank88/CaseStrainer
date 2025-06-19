// Global state
let state = {
    settings: {
        autoValidate: true,
        highlightCitations: true,
        apiEndpoint: 'http://localhost:5000/api/analyze'
    },
    citations: [],
    highlights: new Map(), // Map of citation text to highlight elements
    isProcessing: false,
    debounceTimer: null
};

// Initialize the add-in
Office.onReady((info) => {
    if (info.host === Office.HostType.Word) {
        // Load saved settings
        loadSettings();
        
        // Initialize UI
        initializeUI();
        
        // Set up event listeners
        setupEventListeners();
        
        // Start listening for document changes if auto-validate is enabled
        if (state.settings.autoValidate) {
            startDocumentChangeListener();
        }
    }
});

// Load settings from Office storage
async function loadSettings() {
    try {
        const savedSettings = await Office.RoamingSettings.get('settings');
        if (savedSettings) {
            state.settings = { ...state.settings, ...JSON.parse(savedSettings) };
            updateSettingsUI();
        }
    } catch (error) {
        console.error('Error loading settings:', error);
    }
}

// Save settings to Office storage
async function saveSettings() {
    try {
        await Office.RoamingSettings.set('settings', JSON.stringify(state.settings));
        await Office.RoamingSettings.saveAsync();
    } catch (error) {
        console.error('Error saving settings:', error);
    }
}

// Initialize UI elements
function initializeUI() {
    // Update settings UI
    updateSettingsUI();
    
    // Update results UI
    updateResultsUI();
    
    // Show initial status
    updateStatus('Ready to validate citations');
}

// Set up event listeners
function setupEventListeners() {
    // Validate button
    document.getElementById('validate-button').addEventListener('click', validateDocument);
    
    // Clear button
    document.getElementById('clear-button').addEventListener('click', clearHighlights);
    
    // Settings checkboxes
    document.getElementById('auto-validate').addEventListener('change', (e) => {
        state.settings.autoValidate = e.target.checked;
        if (state.settings.autoValidate) {
            startDocumentChangeListener();
        } else {
            stopDocumentChangeListener();
        }
        saveSettings();
    });
    
    document.getElementById('highlight-citations').addEventListener('change', (e) => {
        state.settings.highlightCitations = e.target.checked;
        if (!state.settings.highlightCitations) {
            clearHighlights();
        } else {
            highlightCitations();
        }
        saveSettings();
    });
    
    // API endpoint input
    document.getElementById('api-endpoint').addEventListener('change', (e) => {
        state.settings.apiEndpoint = e.target.value;
        saveSettings();
    });
}

// Update settings UI to match state
function updateSettingsUI() {
    document.getElementById('auto-validate').checked = state.settings.autoValidate;
    document.getElementById('highlight-citations').checked = state.settings.highlightCitations;
    document.getElementById('api-endpoint').value = state.settings.apiEndpoint;
}

// Start listening for document changes
function startDocumentChangeListener() {
    Office.context.document.addHandlerAsync(
        Office.EventType.DocumentSelectionChanged,
        debounce(handleDocumentChange, 1000)
    );
}

// Stop listening for document changes
function stopDocumentChangeListener() {
    Office.context.document.removeHandlerAsync(
        Office.EventType.DocumentSelectionChanged
    );
}

// Handle document changes
async function handleDocumentChange(event) {
    if (!state.settings.autoValidate || state.isProcessing) return;
    
    try {
        await validateDocument();
    } catch (error) {
        console.error('Error handling document change:', error);
        updateStatus('Error processing document changes', 'error');
    }
}

// Validate the entire document
async function validateDocument() {
    if (state.isProcessing) return;
    
    try {
        state.isProcessing = true;
        showLoading(true);
        updateStatus('Validating citations...');
        updateProgress(0);
        
        // Get document content
        const content = await getDocumentContent();
        if (!content) {
            throw new Error('Could not get document content');
        }
        
        // Update progress
        updateProgress(20);
        updateStatus('Extracting citations...');
        
        // Send to API for validation
        const response = await validateCitations(content);
        
        // Update progress
        updateProgress(80);
        updateStatus('Processing results...');
        
        // Process and store citations
        state.citations = response.citations || [];
        
        // Update UI
        updateResultsUI();
        
        // Highlight citations if enabled
        if (state.settings.highlightCitations) {
            await highlightCitations();
        }
        
        // Update final status
        updateProgress(100);
        updateStatus(`Found ${state.citations.length} citations (${state.citations.filter(c => c.verified).length} verified)`);
        
    } catch (error) {
        console.error('Error validating document:', error);
        updateStatus('Error validating citations: ' + error.message, 'error');
    } finally {
        state.isProcessing = false;
        showLoading(false);
    }
}

// Get document content
async function getDocumentContent() {
    return new Promise((resolve, reject) => {
        Office.context.document.getSelectedDataAsync(
            Office.CoercionType.Text,
            { valueFormat: 'unformatted' },
            (result) => {
                if (result.status === Office.AsyncResultStatus.Succeeded) {
                    resolve(result.value);
                } else {
                    reject(new Error('Could not get document content'));
                }
            }
        );
    });
}

// Validate citations using the API
async function validateCitations(content) {
    try {
        const response = await fetch(state.settings.apiEndpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: content,
                options: {
                    batch_process: true,
                    return_debug: false
                }
            })
        });
        
        if (!response.ok) {
            throw new Error(`API error: ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API error:', error);
        throw new Error('Failed to validate citations: ' + error.message);
    }
}

// Highlight citations in the document
async function highlightCitations() {
    if (!state.settings.highlightCitations || !state.citations.length) return;
    
    try {
        // Clear existing highlights first
        await clearHighlights();
        
        // Create a range for each citation
        for (const citation of state.citations) {
            if (!citation.text) continue;
            
            // Search for the citation in the document
            const searchResults = await searchDocument(citation.text);
            
            // Apply highlighting
            for (const result of searchResults) {
                const range = result.range;
                range.font.highlightColor = citation.verified ? '#dff6dd' : '#fde7e9';
                range.font.color = citation.verified ? '#107c10' : '#d83b01';
                
                // Store the highlight for later removal
                state.highlights.set(citation.text, range);
            }
        }
    } catch (error) {
        console.error('Error highlighting citations:', error);
        updateStatus('Error highlighting citations: ' + error.message, 'error');
    }
}

// Search for text in the document
async function searchDocument(searchText) {
    return new Promise((resolve, reject) => {
        const results = [];
        
        Office.context.document.body.searchAsync(
            searchText,
            { matchCase: true, matchWholeWord: true },
            (result) => {
                if (result.status === Office.AsyncResultStatus.Succeeded) {
                    results.push(...result.value);
                    resolve(results);
                } else {
                    reject(new Error('Search failed'));
                }
            }
        );
    });
}

// Clear all highlights
async function clearHighlights() {
    try {
        for (const range of state.highlights.values()) {
            range.font.highlightColor = 'white';
            range.font.color = 'black';
        }
        state.highlights.clear();
    } catch (error) {
        console.error('Error clearing highlights:', error);
    }
}

// Update the results UI
function updateResultsUI() {
    const totalCitations = state.citations.length;
    const verifiedCitations = state.citations.filter(c => c.verified).length;
    const unverifiedCitations = totalCitations - verifiedCitations;
    
    // Update summary
    document.getElementById('total-citations').textContent = totalCitations;
    document.getElementById('verified-citations').textContent = verifiedCitations;
    document.getElementById('unverified-citations').textContent = unverifiedCitations;
    
    // Update citations list
    const citationsList = document.getElementById('citations-list');
    citationsList.innerHTML = '';
    
    state.citations.forEach(citation => {
        const item = document.createElement('div');
        item.className = 'citation-item';
        
        const text = document.createElement('div');
        text.className = 'citation-text';
        text.textContent = citation.text;
        
        const status = document.createElement('div');
        status.className = `citation-status ${citation.verified ? 'verified' : 'unverified'}`;
        status.textContent = citation.verified ? 'Verified' : 'Unverified';
        
        item.appendChild(text);
        item.appendChild(status);
        citationsList.appendChild(item);
    });
}

// Update status message
function updateStatus(message, type = 'info') {
    const statusElement = document.getElementById('status-message');
    statusElement.textContent = message;
    statusElement.className = `status-message ${type}`;
}

// Update progress bar
function updateProgress(percent) {
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const progressContainer = document.getElementById('progress-container');
    
    progressContainer.style.display = percent > 0 ? 'block' : 'none';
    progressBar.style.width = `${percent}%`;
    progressText.textContent = `${percent}%`;
}

// Show/hide loading spinner
function showLoading(show) {
    document.getElementById('loading-spinner').style.display = show ? 'flex' : 'none';
}

// Utility function for debouncing
function debounce(func, wait) {
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(state.debounceTimer);
            func(...args);
        };
        clearTimeout(state.debounceTimer);
        state.debounceTimer = setTimeout(later, wait);
    };
} 