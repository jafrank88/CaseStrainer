// Processing Feedback Enhancement for CaseStrainer
document.addEventListener('DOMContentLoaded', function() {
    // Global state to track processing status
    window.citationProcessing = {
        isProcessing: false,
        analysisId: null,
        startTime: null,
        elapsedTimeInterval: null,
        totalCitations: 0,
        processedCitations: 0,
        progressInterval: null
    };

    // Get form elements
    const uploadForm = document.getElementById('uploadForm');
    const pasteForm = document.getElementById('pasteForm');
    
    // Function to add processing indicator with progress bar
    function addProcessingIndicator(form) {
        // Create processing indicator
        const processingIndicator = document.createElement('div');
        processingIndicator.id = 'processingIndicator';
        processingIndicator.className = 'alert alert-info mt-3';
        processingIndicator.innerHTML = `
            <div>
                <div class="d-flex align-items-center mb-2">
                    <div class="spinner-border spinner-border-sm me-2" role="status">
                        <span class="visually-hidden">Processing...</span>
                    </div>
                    <div>
                        <strong>Processing citations...</strong>
                        <div id="processingTime">Elapsed time: 0 seconds</div>
                    </div>
                </div>
                <div class="progress mt-2">
                    <div id="processingProgressBar" class="progress-bar progress-bar-striped progress-bar-animated" 
                         role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100" style="width: 0%">
                        0%
                    </div>
                </div>
                <div id="processingStats" class="mt-2 small">Processed: 0 / Estimating...</div>
                <div class="mt-2 small text-muted">
                    <i class="bi bi-info-circle"></i> After processing, check the <strong>Unverified Citations</strong> tab to see citations that couldn't be verified.
                </div>
            </div>
        `;
        form.after(processingIndicator);
        
        // Start elapsed time counter
        window.citationProcessing.elapsedTimeInterval = setInterval(function() {
            const now = new Date();
            const elapsed = Math.floor((now - window.citationProcessing.startTime) / 1000);
            const timeElement = document.getElementById('processingTime');
            if (timeElement) {
                timeElement.textContent = `Elapsed time: ${elapsed} seconds`;
            }
        }, 1000);
        
        // Start progress tracking
        startProgressTracking();
    }
    
    // Function to track citation processing progress
    function startProgressTracking() {
        // Estimate the total number of citations based on form content
        estimateTotalCitations();
        
        // Start polling for progress updates
        window.citationProcessing.progressInterval = setInterval(function() {
            // Get the base URL path for API calls
            const basePath = window.location.pathname.includes('/casestrainer/') ? '/casestrainer' : '';
            
            // Fetch progress from the API
            fetch(`${basePath}/api/processing_progress?total=${window.citationProcessing.totalCitations}`)
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        // Update progress information
                        window.citationProcessing.processedCitations = data.processed_citations;
                        
                        // If total citations was 0 (couldn't estimate), use the server's value
                        if (window.citationProcessing.totalCitations === 0 && data.total_citations > 0) {
                            window.citationProcessing.totalCitations = data.total_citations;
                        }
                        
                        // Update the progress bar
                        updateProgressBar();
                        
                        // If processing is complete, stop polling
                        if (data.is_complete) {
                            clearInterval(window.citationProcessing.progressInterval);
                        }
                    }
                })
                .catch(error => {
                    console.error('Error fetching progress:', error);
                });
        }, 2000); // Poll every 2 seconds
    }
    
    // Function to estimate total citations based on form content
    function estimateTotalCitations() {
        // Try to estimate from file upload or text input
        const fileInput = document.getElementById('fileUpload');
        const textInput = document.getElementById('textInput');
        
        if (fileInput && fileInput.files.length > 0) {
            // For files, we can't easily estimate, so we'll set a placeholder
            window.citationProcessing.totalCitations = 10; // Will be updated as processing progresses
        } else if (textInput && textInput.value) {
            // For text input, estimate based on content
            const text = textInput.value;
            // Rough estimation: count instances of common citation patterns
            const matches = text.match(/\d+\s+U\.S\.\s+\d+|\d+\s+S\.Ct\.\s+\d+|\d+\s+F\.\d+\s+\d+|\d+\s+F\.Supp\.\s+\d+|\d+\s+WL\s+\d+/gi);
            window.citationProcessing.totalCitations = matches ? matches.length : Math.ceil(text.length / 500); // Rough estimate
        } else {
            window.citationProcessing.totalCitations = 0; // Unknown
        }
    }
    
    // Function to update the progress bar
    function updateProgressBar() {
        const progressBar = document.getElementById('processingProgressBar');
        const statsElement = document.getElementById('processingStats');
        
        if (progressBar && statsElement) {
            const total = window.citationProcessing.totalCitations;
            const processed = window.citationProcessing.processedCitations;
            
            // Calculate percentage
            let percentage = 0;
            if (total > 0) {
                percentage = Math.min(Math.round((processed / total) * 100), 100);
            } else if (processed > 0) {
                // If we don't know the total but have processed some, show indeterminate progress
                percentage = Math.min(Math.round((processed / 10) * 100), 95); // Cap at 95% if we don't know total
            }
            
            // Update progress bar
            progressBar.style.width = `${percentage}%`;
            progressBar.setAttribute('aria-valuenow', percentage);
            progressBar.textContent = `${percentage}%`;
            
            // Update stats text
            if (total > 0) {
                statsElement.textContent = `Processed: ${processed} / ${total} citations`;
            } else {
                statsElement.textContent = `Processed: ${processed} citations (total unknown)`;
            }
        }
    }
    
    // Function to remove processing indicator and clean up
    function removeProcessingIndicator() {
        // Clear all intervals
        clearInterval(window.citationProcessing.elapsedTimeInterval);
        clearInterval(window.citationProcessing.progressInterval);
        
        // Reset processing state
        window.citationProcessing.isProcessing = false;
        
        // Remove processing indicator
        const processingIndicator = document.getElementById('processingIndicator');
        if (processingIndicator) {
            processingIndicator.remove();
        }
    }
    
    // Function to add success message
    function addSuccessMessage(form, data) {
        const successMessage = document.createElement('div');
        successMessage.className = 'alert alert-success mt-3';
        successMessage.innerHTML = `
            <div class="d-flex align-items-center mb-2">
                <i class="bi bi-check-circle-fill me-2"></i>
                <strong>Processing complete!</strong> Analyzed ${data.citations_count} citations.
            </div>
            <div class="mt-2 mb-3">
                <div class="small mb-2">
                    <i class="bi bi-info-circle"></i> Check these tabs to review your results:
                </div>
                <div class="d-flex flex-wrap gap-2">
                    <button class="btn btn-sm btn-primary view-gaps-btn">
                        <i class="bi bi-database-fill-exclamation"></i> CourtListener Gaps
                    </button>
                    <button class="btn btn-sm btn-danger view-unverified-btn">
                        <i class="bi bi-exclamation-triangle"></i> Unverified Citations
                    </button>
                </div>
            </div>
        `;
        form.after(successMessage);
        
        // Add event listeners to the buttons
        const viewGapsBtn = successMessage.querySelector('.view-gaps-btn');
        if (viewGapsBtn) {
            viewGapsBtn.addEventListener('click', function() {
                const clGapsTab = document.getElementById('cl-gaps-tab');
                if (clGapsTab) {
                    clGapsTab.click();
                }
            });
        }
        
        const viewUnverifiedBtn = successMessage.querySelector('.view-unverified-btn');
        if (viewUnverifiedBtn) {
            viewUnverifiedBtn.addEventListener('click', function() {
                const unverifiedTab = document.getElementById('unconfirmed-tab');
                if (unverifiedTab) {
                    unverifiedTab.click();
                }
            });
    
    // Start elapsed time counter
    window.citationProcessing.elapsedTimeInterval = setInterval(function() {
        const now = new Date();
        const elapsed = Math.floor((now - window.citationProcessing.startTime) / 1000);
        const timeElement = document.getElementById('processingTime');
        if (timeElement) {
            timeElement.textContent = `Elapsed time: ${elapsed} seconds`;
    }
        
    const viewUnverifiedBtn = successMessage.querySelector('.view-unverified-btn');
    if (viewUnverifiedBtn) {
        viewUnverifiedBtn.addEventListener('click', function() {
            const unverifiedTab = document.getElementById('unconfirmed-tab');
            if (unverifiedTab) {
                unverifiedTab.click();
            }
        });
        
// Start elapsed time counter
window.citationProcessing.elapsedTimeInterval = setInterval(function() {
    const now = new Date();
    const elapsed = Math.floor((now - window.citationProcessing.startTime) / 1000);
    const timeElement = document.getElementById('processingTime');
    if (timeElement) {
        timeElement.textContent = `Elapsed time: ${elapsed} seconds`;
    }
    
    // Intercept tab clicks to show processing state
    const tabButtons = document.querySelectorAll('#citation-tabs button');
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            // If we're processing citations, show a message in the tab content
            if (window.citationProcessing.isProcessing) {
                const tabId = this.getAttribute('data-bs-target');
                const tabContent = document.querySelector(tabId);
                
                if (tabContent && (tabId === '#multitool' || tabId === '#unconfirmed' || tabId === '#cl-gaps')) {
                    // Clear existing content
                    const existingContent = tabContent.querySelector('.card-body');
                    if (existingContent) {
                        existingContent.innerHTML = `
                            <div class="text-center py-4">
                                <div class="spinner-border text-primary" role="status">
                                    <span class="visually-hidden">Loading...</span>
                                </div>
                                <p class="mt-2">Processing citations... Please wait.</p>
                                <div id="tabProcessingTime">Elapsed time: calculating...</div>
                            </div>
                        `;
                        
                        // Update the elapsed time
                        const elapsed = Math.floor((new Date() - window.citationProcessing.startTime) / 1000);
                        const timeElement = document.getElementById('tabProcessingTime');
                        if (timeElement) {
                            timeElement.textContent = `Elapsed time: ${elapsed} seconds`;
                        }
                    }
                }
            }
        });
    });
    
    // Monitor fetch requests to detect when analysis is complete
    const originalFetch = window.fetch;
    window.fetch = function() {
        const fetchPromise = originalFetch.apply(this, arguments);
        
        // Check if this is an analysis request
        const url = arguments[0];
        if (typeof url === 'string' && url.includes('/api/analyze')) {
            fetchPromise
                .then(response => {
                    // Clone the response so we can read it twice
                    const clonedResponse = response.clone();
                    return clonedResponse.json().catch(() => null);
                })
                .then(data => {
                    if (data && data.status === 'success') {
                        // Update processing state
                        window.citationProcessing.isProcessing = false;
                        window.citationProcessing.analysisId = data.analysis_id;
                        
                        // Remove processing indicator
                        removeProcessingIndicator();
                        
                        // Add success message to both forms
                        if (uploadForm) {
                            addSuccessMessage(uploadForm, data);
                        }
                        if (pasteForm) {
                            addSuccessMessage(pasteForm, data);
                        }
                    }
                })
                .catch(error => {
                    console.error('Error monitoring fetch:', error);
                });
        }
        
        return fetchPromise;
    };
});
