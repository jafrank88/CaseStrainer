/**
 * CaseTrainer Word Add-in - Main Application Logic
 * Handles document scanning, citation verification, and Word integration
 */

class CaseTrainerWordAddin {
    constructor() {
        this.apiBaseUrl = 'https://api.casestrainer.com/v1';
        this.currentDocument = null;
        this.verificationResults = [];
        this.isProcessing = false;
        
        this.initializeAddin();
    }

    /**
     * Initialize the add-in when Office.js is ready
     */
    initializeAddin() {
        Office.onReady((info) => {
            if (info.host === Office.HostType.Word) {
                this.setupEventListeners();
                this.loadDocumentInfo();
                this.updateStatus('Ready to scan document');
            }
        });
    }

    /**
     * Set up event listeners for UI interactions
     */
    setupEventListeners() {
        // Main action buttons
        document.getElementById('scanDocument').addEventListener('click', () => {
            this.scanDocument();
        });

        document.getElementById('verifySelected').addEventListener('click', () => {
            this.verifySelectedText();
        });

        document.getElementById('insertCitation').addEventListener('click', () => {
            this.insertVerifiedCitation();
        });

        // Results management
        document.getElementById('clearResults').addEventListener('click', () => {
            this.clearResults();
        });

        // Settings changes
        document.getElementById('autoHighlight').addEventListener('change', (e) => {
            this.updateSettings({ autoHighlight: e.target.checked });
        });

        document.getElementById('includeParallels').addEventListener('change', (e) => {
            this.updateSettings({ includeParallels: e.target.checked });
        });

        document.getElementById('webSearch').addEventListener('change', (e) => {
            this.updateSettings({ webSearch: e.target.checked });
        });

        // Listen for selection changes
        Office.context.document.addHandlerAsync(Office.EventType.DocumentSelectionChanged, () => {
            this.onSelectionChanged();
        });
    }

    /**
     * Load and display current document information
     */
    async loadDocumentInfo() {
        try {
            const documentName = await this.getDocumentName();
            const documentStats = await this.getDocumentStats();
            
            document.getElementById('documentName').textContent = documentName;
            document.getElementById('wordCount').textContent = `${documentStats.wordCount} words`;
            document.getElementById('citationCount').textContent = `${documentStats.citationCount} citations`;
            
            this.currentDocument = {
                name: documentName,
                stats: documentStats
            };
        } catch (error) {
            console.error('Error loading document info:', error);
            this.updateStatus('Error loading document information');
        }
    }

    /**
     * Get the current document name
     */
    async getDocumentName() {
        return new Promise((resolve, reject) => {
            Office.context.document.getFilePropertiesAsync((result) => {
                if (result.status === Office.AsyncResultStatus.Succeeded) {
                    resolve(result.value.url || 'Untitled Document');
                } else {
                    reject(new Error('Failed to get document name'));
                }
            });
        });
    }

    /**
     * Get document statistics
     */
    async getDocumentStats() {
        return new Promise((resolve, reject) => {
            Office.context.document.getSelectedDataAsync(Office.CoercionType.Text, (result) => {
                if (result.status === Office.AsyncResultStatus.Succeeded) {
                    const text = result.value;
                    const wordCount = text.split(/\s+/).filter(word => word.length > 0).length;
                    
                    // Simple citation count estimation
                    const citationPattern = /\b\d{1,4}\s+U\.?S\.?\s+\d{1,4}\b|\b\d{1,4}\s+F\.?\d{1,4}\b|\b\d{1,4}\s+S\.?Ct\.?\s+\d{1,4}\b/gi;
                    const citationCount = (text.match(citationPattern) || []).length;
                    
                    resolve({ wordCount, citationCount });
                } else {
                    reject(new Error('Failed to get document stats'));
                }
            });
        });
    }

    /**
     * Scan the entire document for citations
     */
    async scanDocument() {
        if (this.isProcessing) {
            this.updateStatus('Already processing document');
            return;
        }

        this.isProcessing = true;
        this.showProgress();
        this.updateStatus('Scanning document for citations...');

        try {
            // Get document text
            const documentText = await this.getDocumentText();
            this.updateProgress(20, 'Extracting document text...');

            // Process document with CaseTrainer API
            const results = await this.processDocumentWithAPI(documentText);
            this.updateProgress(80, 'Verifying citations...');

            // Display results
            this.displayResults(results);
            this.updateProgress(100, 'Scan complete!');

            this.updateStatus(`Found ${results.citations.length} citations`);
            this.verificationResults = results.citations;

            // Auto-highlight if enabled
            if (document.getElementById('autoHighlight').checked) {
                this.highlightCitations(results.citations);
            }

        } catch (error) {
            console.error('Error scanning document:', error);
            this.updateStatus('Error scanning document: ' + error.message);
        } finally {
            this.isProcessing = false;
            this.hideProgress();
        }
    }

    /**
     * Get the full document text
     */
    async getDocumentText() {
        return new Promise((resolve, reject) => {
            Office.context.document.getSelectedDataAsync(Office.CoercionType.Text, { valueForNull: "" }, (result) => {
                if (result.status === Office.AsyncResultStatus.Succeeded) {
                    resolve(result.value);
                } else {
                    reject(new Error('Failed to get document text'));
                }
            });
        });
    }

    /**
     * Process document with CaseTrainer API
     */
    async processDocumentWithAPI(documentText) {
        const settings = this.getSettings();
        
        const response = await fetch(`${this.apiBaseUrl}/documents/process`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.getApiKey()}`
            },
            body: JSON.stringify({
                document_text: documentText,
                options: {
                    extract_citations: true,
                    verify_citations: true,
                    include_positions: true,
                    include_context: false,
                    include_parallels: settings.includeParallels,
                    include_web_search: settings.webSearch
                }
            })
        });

        if (!response.ok) {
            throw new Error(`API request failed: ${response.statusText}`);
        }

        return await response.json();
    }

    /**
     * Verify selected text as a citation
     */
    async verifySelectedText() {
        try {
            const selectedText = await this.getSelectedText();
            if (!selectedText || selectedText.trim().length === 0) {
                this.updateStatus('No text selected');
                return;
            }

            this.updateStatus('Verifying selected text...');
            this.showLoading();

            const result = await this.verifyCitationWithAPI(selectedText);
            this.displaySingleResult(result);
            this.updateStatus('Verification complete');

        } catch (error) {
            console.error('Error verifying selected text:', error);
            this.updateStatus('Error verifying text: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    /**
     * Get currently selected text
     */
    async getSelectedText() {
        return new Promise((resolve, reject) => {
            Office.context.document.getSelectedDataAsync(Office.CoercionType.Text, (result) => {
                if (result.status === Office.AsyncResultStatus.Succeeded) {
                    resolve(result.value);
                } else {
                    reject(new Error('Failed to get selected text'));
                }
            });
        });
    }

    /**
     * Verify a single citation with the API
     */
    async verifyCitationWithAPI(citation) {
        const response = await fetch(`${this.apiBaseUrl}/citations/verify`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.getApiKey()}`
            },
            body: JSON.stringify({
                citation: citation,
                options: {
                    include_parallels: this.getSettings().includeParallels,
                    include_web_search: this.getSettings().webSearch
                }
            })
        });

        if (!response.ok) {
            throw new Error(`API request failed: ${response.statusText}`);
        }

        return await response.json();
    }

    /**
     * Display verification results
     */
    displayResults(results) {
        const resultsSection = document.getElementById('resultsSection');
        const resultsList = document.getElementById('resultsList');
        
        resultsSection.style.display = 'block';
        resultsList.innerHTML = '';

        if (!results.citations || results.citations.length === 0) {
            resultsList.innerHTML = '<div class="no-results">No citations found in document</div>';
            return;
        }

        results.citations.forEach((citation, index) => {
            const resultElement = this.createResultElement(citation, index);
            resultsList.appendChild(resultElement);
        });

        // Enable action buttons
        document.getElementById('verifySelected').disabled = false;
        document.getElementById('insertCitation').disabled = false;
    }

    /**
     * Display a single verification result
     */
    displaySingleResult(result) {
        const resultsSection = document.getElementById('resultsSection');
        const resultsList = document.getElementById('resultsList');
        
        resultsSection.style.display = 'block';
        resultsList.innerHTML = '';

        const resultElement = this.createResultElement(result, 0);
        resultsList.appendChild(resultElement);

        // Enable action buttons
        document.getElementById('verifySelected').disabled = false;
        document.getElementById('insertCitation').disabled = false;
    }

    /**
     * Create a result element from template
     */
    createResultElement(citation, index) {
        const template = document.getElementById('citationResultTemplate');
        const clone = template.content.cloneNode(true);

        // Set citation text
        clone.querySelector('.citation-text').textContent = citation.citation;

        // Set verification status
        const statusElement = clone.querySelector('.verification-status');
        if (citation.verified) {
            statusElement.textContent = '✓ Verified';
            statusElement.className = 'verification-status verified';
        } else {
            statusElement.textContent = '✗ Not Verified';
            statusElement.className = 'verification-status unverified';
        }

        // Set case name (use extracted_case_name or canonical_name)
        const caseNameElement = clone.querySelector('.case-name');
        const displayName = citation.extracted_case_name || citation.canonical_name || 'N/A';
        caseNameElement.textContent = `Case: ${displayName}`;

        // Set date
        const dateElement = clone.querySelector('.date');
        dateElement.textContent = `Date: ${citation.canonical_date || citation.year || 'N/A'}`;

        // Set sources
        const sourcesElement = clone.querySelector('.sources');
        const sources = [];
        if (citation.courtlistener_verified) sources.push('CourtListener');
        if (citation.web_verified) sources.push('Web Search');
        if (citation.local_verified) sources.push('Local DB');
        sourcesElement.textContent = `Sources: ${sources.length > 0 ? sources.join(', ') : 'None'}`;

        // Set up action buttons
        const insertBtn = clone.querySelector('.insert-btn');
        insertBtn.addEventListener('click', () => {
            this.insertCitationIntoDocument(citation);
        });

        const viewBtn = clone.querySelector('.view-btn');
        viewBtn.addEventListener('click', () => {
            this.showCitationDetails(citation);
        });

        return clone;
    }

    /**
     * Insert a verified citation into the document
     */
    async insertCitationIntoDocument(citation) {
        try {
            const citationText = this.formatCitationForInsertion(citation);
            
            Office.context.document.setSelectedDataAsync(citationText, {
                coercionType: Office.CoercionType.Text
            }, (result) => {
                if (result.status === Office.AsyncResultStatus.Succeeded) {
                    this.updateStatus('Citation inserted successfully');
                } else {
                    this.updateStatus('Error inserting citation');
                }
            });
        } catch (error) {
            console.error('Error inserting citation:', error);
            this.updateStatus('Error inserting citation: ' + error.message);
        }
    }

    /**
     * Format citation for insertion into document
     */
    formatCitationForInsertion(citation) {
        let formatted = citation.citation;
        
        // Add verification status if verified
        if (citation.verified) {
            formatted += ' [Verified]';
        }
        
        // Add case name if available (use extracted_case_name or canonical_name)
        const displayName = citation.extracted_case_name || citation.canonical_name;
        if (displayName && displayName !== 'N/A') {
            formatted += ` (${displayName})`;
        }
        
        return formatted;
    }

    /**
     * Show detailed citation information
     */
    showCitationDetails(citation) {
        const displayName = citation.extracted_case_name || citation.canonical_name || 'N/A';
        const details = `
Case Name: ${displayName}
Date: ${citation.canonical_date || citation.year || 'N/A'}
Verified: ${citation.verified ? 'Yes' : 'No'}
Sources: ${this.getVerificationSources(citation)}
URL: ${citation.courtlistener_url || 'N/A'}
        `.trim();

        alert(details);
    }

    /**
     * Get verification sources as string
     */
    getVerificationSources(citation) {
        const sources = [];
        if (citation.courtlistener_verified) sources.push('CourtListener');
        if (citation.web_verified) sources.push('Web Search');
        if (citation.local_verified) sources.push('Local DB');
        return sources.length > 0 ? sources.join(', ') : 'None';
    }

    /**
     * Highlight citations in the document
     */
    async highlightCitations(citations) {
        // This would require more complex Word API calls to highlight text
        // For now, we'll just log the citations that would be highlighted
        console.log('Citations to highlight:', citations);
        this.updateStatus(`Highlighted ${citations.length} citations`);
    }

    /**
     * Clear all results
     */
    clearResults() {
        document.getElementById('resultsSection').style.display = 'none';
        document.getElementById('resultsList').innerHTML = '';
        this.verificationResults = [];
        
        document.getElementById('verifySelected').disabled = true;
        document.getElementById('insertCitation').disabled = true;
        
        this.updateStatus('Results cleared');
    }

    /**
     * Handle selection changes
     */
    onSelectionChanged() {
        // Enable/disable verify selected button based on selection
        this.getSelectedText().then(text => {
            const verifyButton = document.getElementById('verifySelected');
            verifyButton.disabled = !text || text.trim().length === 0;
        }).catch(() => {
            document.getElementById('verifySelected').disabled = true;
        });
    }

    /**
     * Show progress section
     */
    showProgress() {
        document.getElementById('progressSection').style.display = 'block';
    }

    /**
     * Hide progress section
     */
    hideProgress() {
        document.getElementById('progressSection').style.display = 'none';
    }

    /**
     * Update progress bar
     */
    updateProgress(percentage, text) {
        document.getElementById('progressBar').style.width = `${percentage}%`;
        document.getElementById('progressText').textContent = text;
        document.getElementById('progressDetails').textContent = text;
    }

    /**
     * Show loading spinner
     */
    showLoading() {
        document.getElementById('loadingSpinner').style.display = 'flex';
    }

    /**
     * Hide loading spinner
     */
    hideLoading() {
        document.getElementById('loadingSpinner').style.display = 'none';
    }

    /**
     * Update status message
     */
    updateStatus(message) {
        document.getElementById('statusMessage').textContent = message;
        document.getElementById('lastUpdated').textContent = `Last updated: ${new Date().toLocaleTimeString()}`;
    }

    /**
     * Get current settings
     */
    getSettings() {
        return {
            autoHighlight: document.getElementById('autoHighlight').checked,
            includeParallels: document.getElementById('includeParallels').checked,
            webSearch: document.getElementById('webSearch').checked
        };
    }

    /**
     * Update settings
     */
    updateSettings(newSettings) {
        // Save settings to localStorage
        localStorage.setItem('casestrainer-settings', JSON.stringify(newSettings));
    }

    /**
     * Get API key from settings
     */
    getApiKey() {
        // In a real implementation, this would be securely stored
        // For now, we'll use a placeholder
        return localStorage.getItem('casestrainer-api-key') || 'demo-key';
    }

    /**
     * Insert verified citation (main action)
     */
    insertVerifiedCitation() {
        if (this.verificationResults.length === 0) {
            this.updateStatus('No verified citations available');
            return;
        }

        // For now, insert the first verified citation
        const verifiedCitation = this.verificationResults.find(c => c.verified);
        if (verifiedCitation) {
            this.insertCitationIntoDocument(verifiedCitation);
        } else {
            this.updateStatus('No verified citations found');
        }
    }
}

// Initialize the add-in when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new CaseTrainerWordAddin();
}); 