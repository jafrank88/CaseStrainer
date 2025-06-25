// Global state to track processing status
window.citationProcessing = {
    isProcessing: false,
    analysisId: null,
    startTime: null,
    totalCitations: 0,
    processedCitations: 0,
    progressInterval: null
};

document.addEventListener('DOMContentLoaded', function() {
    // Always use the /casestrainer/ prefix for API calls to work with Nginx proxy
    // Build base API path using current protocol and host, always matching page protocol
    const isHttps = window.location.protocol === 'https:';
    const apiHost = window.location.host;
    const basePath = (window.location.pathname.includes('/casestrainer/') ? '/casestrainer' : '');
    // Helper to build full API URL with enforced protocol
    // Import apiUrl from shared helper
    // (Assume this is loaded via <script> or ES6 import elsewhere)

    
    // Get form elements
    const fileForm = document.getElementById('fileUploadForm');
    const textForm = document.getElementById('textInputForm');
    const urlForm = document.getElementById('urlInputForm');
    
    // Function to create and update progress bar
    function setupProgressTracking(form) {
        console.log('Setting up progress tracking');
        
        // Create progress UI
        const progressContainer = document.createElement('div');
        progressContainer.className = 'progress mt-3';
        progressContainer.style.height = '20px';
        
        const progressBar = document.createElement('div');
        progressBar.className = 'progress-bar progress-bar-striped progress-bar-animated';
        progressBar.role = 'progressbar';
        progressBar.style.width = '0%';
        progressBar.setAttribute('aria-valuenow', '0');
        progressBar.setAttribute('aria-valuemin', '0');
        progressBar.setAttribute('aria-valuemax', '100');
        progressBar.textContent = 'Starting...';
        
        progressContainer.appendChild(progressBar);
        form.appendChild(progressContainer);
        
        // Initialize progress tracking
        window.citationProcessing = {
            isProcessing: true,
            startTime: new Date(),
            totalCitations: 100, // Default estimate
            processedCitations: 0,
            progressInterval: null
        };
        
        console.log('Starting progress polling');
        
        // Start progress polling
        window.citationProcessing.progressInterval = setInterval(() => {
            console.log('Checking progress...');
            fetch(apiUrl('/analyze'), {
                method: 'GET'
            })
            .then(response => response.json())
            .then(data => {
                console.log('Progress response:', data);
                if (data.status === 'success') {
                    window.citationProcessing.processedCitations = data.processed_citations;
                    
                    // Calculate progress percentage
                    const progress = data.total_citations > 0 ? 
                        Math.min(Math.round((data.processed_citations / data.total_citations) * 100), 100) : 0;
                    
                    console.log(`Progress: ${progress}% (${data.processed_citations}/${data.total_citations})`);
                    
                    // Update progress bar
                    progressBar.style.width = `${progress}%`;
                    progressBar.setAttribute('aria-valuenow', progress);
                    progressBar.textContent = `${progress}% (${data.processed_citations}/${data.total_citations})`;
                    
                    // Check if processing is complete
                    if (data.is_complete) {
                        console.log('Processing complete');
                        clearInterval(window.citationProcessing.progressInterval);
                        window.citationProcessing.isProcessing = false;
                        progressBar.textContent = 'Complete!';
                        progressBar.className = 'progress-bar bg-success';
                    }
                }
            })
            .catch(error => {
                console.error('Error checking progress:', error);
                clearInterval(window.citationProcessing.progressInterval);
                progressBar.textContent = 'Error tracking progress';
                progressBar.className = 'progress-bar bg-danger';
            });
        }, 1000);
        
        return progressContainer;
    }
    
    // Handle file upload form submission
    if (fileForm) {
        fileForm.addEventListener('submit', function(e) {
            e.preventDefault(); // Prevent traditional form submission
            
            const submitButton = this.querySelector('button[type="submit"]');
            const originalButtonText = submitButton.innerHTML;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Analyzing...';
            submitButton.disabled = true;
            
            const formData = new FormData(this);
            
            // Setup progress tracking
            const progressContainer = setupProgressTracking(this);
            
            fetch(apiUrl('/analyze'), {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Analysis results:', data);
                
                // Defensive checks for expected properties
                if (!data || typeof data !== 'object') {
                    alert('Unexpected API response: no data returned.');
                    submitButton.disabled = false;
                    submitButton.textContent = 'Analyze Citations';
                    return;
                }
                if (!Array.isArray(data.citations)) {
                    alert('No citations found in the API response.');
                    submitButton.disabled = false;
                    submitButton.textContent = 'Analyze Citations';
                    return;
                }
                // Store the analysis results
                window.analysisResults = data;
                // Update citation count for progress tracking
                if (data.citations_count) {
                    window.citationProcessing.totalCitations = data.citations_count;
                }
                // Reset button
                submitButton.disabled = false;
                submitButton.textContent = 'Analyze Citations';
                // Switch to the Multitool tab to show results
                const multitoolTab = document.getElementById('multitool-tab');
                if (multitoolTab) {
                    multitoolTab.click();
                }
                // Reset button
                submitButton.innerHTML = originalButtonText;
                submitButton.disabled = false;
                
                // Remove progress bar on error
                if (progressContainer) {
                    progressContainer.remove();
                }
                
                // Clear progress interval
                if (window.citationProcessing.progressInterval) {
                    clearInterval(window.citationProcessing.progressInterval);
                    window.citationProcessing.isProcessing = false;
                }
            })
            .catch(error => {
                console.error('Error analyzing document:', error);
                alert('Error analyzing document: ' + error.message);
                
                // Reset button
                submitButton.innerHTML = originalButtonText;
                submitButton.disabled = false;
                
                // Remove progress bar on error
                if (progressContainer) {
                    progressContainer.remove();
                }
                
                // Clear progress interval
                if (window.citationProcessing.progressInterval) {
                    clearInterval(window.citationProcessing.progressInterval);
                    window.citationProcessing.isProcessing = false;
                }
            });
        });
    }
    
    // Handle text paste form submission
    if (textForm) {
        textForm.addEventListener('submit', function(e) {
            e.preventDefault(); // Prevent traditional form submission
            
            const submitButton = this.querySelector('button[type="submit"]');
            const originalButtonText = submitButton.innerHTML;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Analyzing...';
            submitButton.disabled = true;
            
            // Get the text input value
            const textInput = this.querySelector('textarea[name="text"]');
            const text = textInput ? textInput.value : '';
            
            if (!text || text.trim() === '') {
                alert('Please enter some text to analyze');
                submitButton.innerHTML = originalButtonText;
                submitButton.disabled = false;
                return;
            }
            
            // Setup progress tracking
            const progressContainer = setupProgressTracking(this);
            
            fetch(apiUrl('/analyze'), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ text: text })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Analysis results:', data);
                
                // Store the analysis results
                window.analysisResults = data;
                
                // Update citation count for progress tracking
                if (data.citations_count) {
                    window.citationProcessing.totalCitations = data.citations_count;
                }
                
                // Reset button
                submitButton.innerHTML = originalButtonText;
                submitButton.disabled = false;
            })
            .catch(error => {
                console.error('Error analyzing text:', error);
                alert('Error analyzing text: ' + error.message);
                
                // Reset button
                submitButton.innerHTML = originalButtonText;
                submitButton.disabled = false;
                
                // Remove progress bar on error
                if (progressContainer) {
                    progressContainer.remove();
                }
                
                // Clear progress interval
                if (window.citationProcessing.progressInterval) {
                    clearInterval(window.citationProcessing.progressInterval);
                    window.citationProcessing.isProcessing = false;
                }
            });
        });
    }
    
    // Handle URL form submission
    if (urlForm) {
        urlForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            console.log('Starting URL form submission');
            
            const submitButton = this.querySelector('button[type="submit"]');
            const originalButtonText = submitButton.innerHTML;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Analyzing...';
            submitButton.disabled = true;
            
            const url = document.getElementById('urlInput').value;
            if (!url) {
                alert('Please enter a valid URL');
                submitButton.innerHTML = originalButtonText;
                submitButton.disabled = false;
                return;
            }
            
            console.log('Setting up progress tracking');
            const progressContainer = setupProgressTracking(this);
            
            console.log('Fetching URL content:', url);
            fetch(apiUrl('/analyze'), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ url: url })
            })
            .then(response => {
                console.log('Fetch URL response status:', response.status);
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Fetch URL response:', data);
                if (data.status === 'success' && data.text) {
                    console.log('Starting text analysis with length:', data.text.length);
                    
                    return fetch(apiUrl('/analyze'), {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ text: data.text })
                    });
                } else {
                    throw new Error(data.message || 'Failed to fetch URL content');
                }
            })
            .then(response => {
                console.log('Analyze response status:', response.status);
                submitButton.innerHTML = originalButtonText;
                submitButton.disabled = false;
                
                // Remove progress bar on error
                if (progressContainer) {
                    progressContainer.remove();
                }
                
                // Clear progress interval
                if (window.citationProcessing.progressInterval) {
                    clearInterval(window.citationProcessing.progressInterval);
                    window.citationProcessing.isProcessing = false;
                }
            });
        });
    }
    
    // Load data for tabs when they're clicked
    const tabButtons = document.querySelectorAll('.nav-link[data-bs-toggle="tab"]');
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const tabId = this.getAttribute('data-bs-target');
            
            // Helper function to group citations by their text
            function groupCitations(citations) {
                const grouped = {};
                citations.forEach(citation => {
                    const key = citation.citation_text;
                    if (!grouped[key]) {
                        grouped[key] = {
                            citation: citation,
                            count: 0,
                            contexts: []
                        };
                    }
                    grouped[key].count++;
                    if (citation.context) {
                        grouped[key].contexts.push(citation.context);
                    }
                });
                return Object.values(grouped);
            }
            
            // Display citation statistics
            displayCitationStats(citations);
            
            // Load data based on which tab was clicked
            if (tabId === '#cl-citations') {
                const courtListenerCitations = citations.filter(c => 
                    c.found === true && c.source === 'CourtListener'
                );
                const groupedCitations = groupCitations(courtListenerCitations);
                displayCourtListenerCitations(groupedCitations);
            } else if (tabId === '#multitool') {
                const verifiedNonCLCitations = citations.filter(c => 
                    c.found === true && c.source !== 'CourtListener'
                );
                const groupedCitations = groupCitations(verifiedNonCLCitations);
                displayVerifiedCitations(groupedCitations);
            } else if (tabId === '#unconfirmed') {
                const unverifiedCitations = citations.filter(c => 
                    c.found === false
                );
                const groupedCitations = groupCitations(unverifiedCitations);
                displayUnverifiedCitations(groupedCitations);
            }
        });
    });
});

function displayCitationStats(citations) {
    const stats = {
        courtListener: 0,
        otherVerified: 0,
        unverified: 0
    };
    
    citations.forEach(citation => {
        if (citation.found && citation.source === 'CourtListener') {
            stats.courtListener++;
        } else if (citation.found) {
            stats.otherVerified++;
        } else {
            stats.unverified++;
        }
    });
    
    // Update tab badges
    document.getElementById('cl-citations-tab').innerHTML = `CourtListener Verified <span class="badge bg-primary">${stats.courtListener}</span>`;
    document.getElementById('multitool-tab').innerHTML = `Other Source Verified <span class="badge bg-success">${stats.otherVerified}</span>`;
    document.getElementById('unconfirmed-tab').innerHTML = `Unverified <span class="badge bg-danger">${stats.unverified}</span>`;
    
    // Add total count to the results section
    const totalCount = stats.courtListener + stats.otherVerified + stats.unverified;
    document.getElementById('resultsContent').innerHTML = `
        <div class="alert alert-info mb-3">
            <h6>Citation Statistics</h6>
            <p>Total Citations Found: ${totalCount}</p>
            <ul class="list-unstyled">
                <li>CourtListener Verified: ${stats.courtListener}</li>
                <li>Other Source Verified: ${stats.otherVerified}</li>
                <li>Unverified: ${stats.unverified}</li>
            </ul>
        </div>
    `;
}