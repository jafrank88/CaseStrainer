// Multitool Citations Tab JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Always use the /casestrainer/ prefix for API calls to work with Nginx proxy
    const basePath = window.location.pathname.includes('/casestrainer/') ? '/casestrainer' : '';
    const multitoolTab = document.getElementById('multitool-tab');
    
    if (multitoolTab) {
        multitoolTab.addEventListener('click', function() {
            fetchMultitoolCitations();
        });
    }
    
    function fetchMultitoolCitations() {
        // Check if we're still processing citations
        if (window.citationProcessing && window.citationProcessing.isProcessing) {
            renderProcessing();
            return;
        }
        
        // Check if we have an analysis ID from the current session
        const currentAnalysisId = window.analysisResults ? window.analysisResults.analysis_id : null;
        if (!currentAnalysisId) {
            renderNoAnalysis();
            return;
        }
        
        // Show loading state
        const container = document.querySelector('#multitool .card-body');
        const loadingDiv = container.querySelector('.text-center');
        const tableDiv = container.querySelector('.mt-3');
        
        loadingDiv.classList.remove('d-none');
        tableDiv.classList.add('d-none');
        
        // Fetch data from API
        fetch(`${basePath}/api/confirmed_with_multitool_data`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Multitool citations data:', data);
                
                // Hide loading, show table
                loadingDiv.classList.add('d-none');
                tableDiv.classList.remove('d-none');
                
                // Render citations
                displayVerifiedCitations(data.citations);
            })
            .catch(error => {
                console.error('Error fetching multitool citations:', error);
                
                // Show error message
                loadingDiv.classList.add('d-none');
                container.innerHTML += `
                    <div class="alert alert-danger">
                        Error loading citations: ${error.message}
                    </div>
                `;
            });
    }
    
    function displayVerifiedCitations(citations) {
        const container = document.getElementById('multitool-citations');
        container.innerHTML = '';
        
        citations.forEach(group => {
            const item = document.createElement('div');
            item.className = 'list-group-item';
            
            // Create the main citation display with count
            const citationDisplay = document.createElement('div');
            citationDisplay.className = 'd-flex justify-content-between align-items-center';
            
            const citationText = document.createElement('div');
            citationText.innerHTML = `
                <strong>${group.citation.citation_text}</strong>
                ${group.count > 1 ? `<span class="badge bg-secondary ms-2">${group.count} occurrences</span>` : ''}
                ${group.citation.case_name ? `<br><small class="text-muted">${group.citation.case_name}</small>` : ''}
                <br>
                <span class="badge bg-success">Verified by: ${group.citation.source}</span>
                ${group.citation.confidence ? `<br><small class="text-muted">Confidence: ${(group.citation.confidence * 100).toFixed(1)}%</small>` : ''}
            `;
            
            const actions = document.createElement('div');
            if (group.citation.url) {
                actions.innerHTML = `
                    <a href="${group.citation.url}" target="_blank" class="btn btn-sm btn-outline-success">
                        <i class="bi bi-box-arrow-up-right"></i> View Source
                    </a>
                `;
            }
            
            citationDisplay.appendChild(citationText);
            citationDisplay.appendChild(actions);
            item.appendChild(citationDisplay);
            
            // Add context if available
            if (group.citation.context) {
                const contextDiv = document.createElement('div');
                contextDiv.className = 'mt-2 text-muted';
                contextDiv.innerHTML = `<small>Context: ${group.citation.context}</small>`;
                item.appendChild(contextDiv);
            }
            
            container.appendChild(item);
        });
        
        // Show the content and hide loading
        document.getElementById('multitool-loading').style.display = 'none';
        document.getElementById('multitool-content').style.display = 'block';
    }
    
    function renderProcessing() {
        const container = document.querySelector('#multitool .card-body');
        
        // Clear existing content
        container.innerHTML = `
            <div class="alert alert-info">
                <div class="d-flex align-items-center mb-2">
                    <div class="spinner-border spinner-border-sm me-2" role="status">
                        <span class="visually-hidden">Processing...</span>
                    </div>
                    <div>
                        <strong>Processing citations...</strong>
                        <div id="multitoolProcessingTime">Please wait while citations are being analyzed.</div>
                    </div>
                </div>
                <div class="progress mt-2">
                    <div id="multitoolProgressBar" class="progress-bar progress-bar-striped progress-bar-animated" 
                         role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100" style="width: 100%">
                        Processing...
                    </div>
                </div>
                <div class="mt-2 small text-muted">
                    <i class="bi bi-info-circle"></i> Results will be shown here when processing is complete.
                </div>
            </div>
        `;
    }
    
    function renderNoAnalysis() {
        const container = document.querySelector('#multitool .card-body');
        
        // Clear existing content
        container.innerHTML = `
            <div class="alert alert-warning">
                <div class="d-flex align-items-center">
                    <i class="bi bi-exclamation-triangle-fill me-2"></i>
                    <div>
                        <strong>No citation analysis available</strong>
                        <p class="mb-0">Please upload a document or paste text in the appropriate tab to analyze citations.</p>
                    </div>
                </div>
                <div class="mt-3">
                    <button class="btn btn-sm btn-primary" id="goto-upload-btn">
                        <i class="bi bi-upload"></i> Go to Upload Tab
                    </button>
                </div>
            </div>
        `;
        
        // Add event listener to the button
        const gotoUploadBtn = container.querySelector('#goto-upload-btn');
        if (gotoUploadBtn) {
            gotoUploadBtn.addEventListener('click', function() {
                const uploadTab = document.getElementById('upload-tab');
                if (uploadTab) {
                    uploadTab.click();
                }
            });
        }
    }
});
