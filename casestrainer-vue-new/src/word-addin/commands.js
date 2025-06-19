// Global state
let state = {
    isProcessing: false,
    settings: {
        apiEndpoint: 'http://localhost:5000/api/analyze'
    }
};

// Initialize the commands
Office.onReady((info) => {
    if (info.host === Office.HostType.Word) {
        // Load settings
        loadSettings();
        
        // Set up event listeners
        setupEventListeners();
    }
});

// Load settings from Office storage
async function loadSettings() {
    try {
        const savedSettings = await Office.RoamingSettings.get('settings');
        if (savedSettings) {
            state.settings = { ...state.settings, ...JSON.parse(savedSettings) };
        }
    } catch (error) {
        console.error('Error loading settings:', error);
    }
}

// Set up event listeners
function setupEventListeners() {
    // Validate selection button
    document.getElementById('validate-selection').addEventListener('click', validateSelection);
    
    // Validate document button
    document.getElementById('validate-document').addEventListener('click', validateDocument);
    
    // Clear highlights button
    document.getElementById('clear-highlights').addEventListener('click', clearHighlights);
    
    // Export report button
    document.getElementById('export-report').addEventListener('click', exportReport);
}

// Validate the current selection
async function validateSelection() {
    if (state.isProcessing) return;
    
    try {
        state.isProcessing = true;
        updateButtonStates(true);
        
        // Get the selected text
        const selection = await getSelection();
        if (!selection) {
            throw new Error('No text selected');
        }
        
        // Validate the selection
        const response = await validateCitations(selection);
        
        // Process and highlight citations
        await processCitations(response.citations);
        
        // Show success message
        showMessage('Selection validated successfully');
        
    } catch (error) {
        console.error('Error validating selection:', error);
        showMessage('Error validating selection: ' + error.message, 'error');
    } finally {
        state.isProcessing = false;
        updateButtonStates(false);
    }
}

// Validate the entire document
async function validateDocument() {
    if (state.isProcessing) return;
    
    try {
        state.isProcessing = true;
        updateButtonStates(true);
        
        // Get the entire document content
        const content = await getDocumentContent();
        if (!content) {
            throw new Error('Could not get document content');
        }
        
        // Validate the content
        const response = await validateCitations(content);
        
        // Process and highlight citations
        await processCitations(response.citations);
        
        // Show success message
        showMessage(`Found ${response.citations.length} citations (${response.citations.filter(c => c.verified).length} verified)`);
        
    } catch (error) {
        console.error('Error validating document:', error);
        showMessage('Error validating document: ' + error.message, 'error');
    } finally {
        state.isProcessing = false;
        updateButtonStates(false);
    }
}

// Clear all highlights
async function clearHighlights() {
    try {
        // Get all ranges with highlights
        const ranges = await getHighlightedRanges();
        
        // Clear highlights
        for (const range of ranges) {
            range.font.highlightColor = 'white';
            range.font.color = 'black';
        }
        
        showMessage('Highlights cleared');
    } catch (error) {
        console.error('Error clearing highlights:', error);
        showMessage('Error clearing highlights: ' + error.message, 'error');
    }
}

// Export citation report
async function exportReport() {
    try {
        // Get all citations
        const content = await getDocumentContent();
        const response = await validateCitations(content);
        
        // Create report content
        const report = generateReport(response.citations);
        
        // Create a new document with the report
        await createReportDocument(report);
        
        showMessage('Report exported successfully');
    } catch (error) {
        console.error('Error exporting report:', error);
        showMessage('Error exporting report: ' + error.message, 'error');
    }
}

// Get the current selection
async function getSelection() {
    return new Promise((resolve, reject) => {
        Office.context.document.getSelectedDataAsync(
            Office.CoercionType.Text,
            { valueFormat: 'unformatted' },
            (result) => {
                if (result.status === Office.AsyncResultStatus.Succeeded) {
                    resolve(result.value);
                } else {
                    reject(new Error('Could not get selection'));
                }
            }
        );
    });
}

// Get the entire document content
async function getDocumentContent() {
    return new Promise((resolve, reject) => {
        Office.context.document.body.getTextAsync(
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

// Process and highlight citations
async function processCitations(citations) {
    if (!citations || !citations.length) return;
    
    try {
        // Clear existing highlights first
        await clearHighlights();
        
        // Process each citation
        for (const citation of citations) {
            if (!citation.text) continue;
            
            // Search for the citation in the document
            const searchResults = await searchDocument(citation.text);
            
            // Apply highlighting
            for (const result of searchResults) {
                const range = result.range;
                range.font.highlightColor = citation.verified ? '#dff6dd' : '#fde7e9';
                range.font.color = citation.verified ? '#107c10' : '#d83b01';
            }
        }
    } catch (error) {
        console.error('Error processing citations:', error);
        throw new Error('Failed to process citations: ' + error.message);
    }
}

// Get all ranges with highlights
async function getHighlightedRanges() {
    return new Promise((resolve, reject) => {
        Office.context.document.body.getStyleAsync(
            'highlightColor',
            (result) => {
                if (result.status === Office.AsyncResultStatus.Succeeded) {
                    resolve(result.value);
                } else {
                    reject(new Error('Could not get highlighted ranges'));
                }
            }
        );
    });
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

// Generate report content
function generateReport(citations) {
    const verified = citations.filter(c => c.verified);
    const unverified = citations.filter(c => !c.verified);
    
    return `
CaseStrainer Citation Report
Generated: ${new Date().toLocaleString()}

Summary:
--------
Total Citations: ${citations.length}
Verified Citations: ${verified.length}
Unverified Citations: ${unverified.length}

Verified Citations:
------------------
${verified.map(c => `- ${c.text} (${c.case_name || 'Unknown Case'})`).join('\n')}

Unverified Citations:
--------------------
${unverified.map(c => `- ${c.text} (${c.case_name || 'Unknown Case'})`).join('\n')}

Suggestions:
-----------
${unverified.map(c => {
    const suggestions = c.suggestions || [];
    return `For "${c.text}":\n${suggestions.map(s => `  - ${s}`).join('\n')}`;
}).join('\n\n')}
    `.trim();
}

// Create a new document with the report
async function createReportDocument(report) {
    return new Promise((resolve, reject) => {
        Office.context.document.setSelectedDataAsync(
            report,
            { coercionType: Office.CoercionType.Text },
            (result) => {
                if (result.status === Office.AsyncResultStatus.Succeeded) {
                    resolve();
                } else {
                    reject(new Error('Could not create report document'));
                }
            }
        );
    });
}

// Update button states
function updateButtonStates(disabled) {
    const buttons = document.querySelectorAll('.ms-Button');
    buttons.forEach(button => {
        button.disabled = disabled;
    });
}

// Show message to the user
function showMessage(message, type = 'info') {
    // In a real implementation, this would show a message in the UI
    // For now, we'll just log it
    console.log(`[${type.toUpperCase()}] ${message}`);
    
    // You could also use Office.context.document.settings to store the message
    // and have the taskpane pick it up
    Office.context.document.settings.set('lastMessage', JSON.stringify({
        message,
        type,
        timestamp: new Date().toISOString()
    }));
    Office.context.document.settings.saveAsync();
} 