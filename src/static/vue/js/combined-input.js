/**
 * Combined Input Methods JavaScript
 * Handles file upload, text paste, and URL input for citation analysis
 */

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
    const basePath = window.location.pathname.includes('/casestrainer/') ? '/casestrainer' : '';
    
    // Get form elements
    const uploadForm = document.getElementById('uploadForm');
    const pasteForm = document.getElementById('pasteForm');
    const urlForm = document.getElementById('urlForm');
    
    // Get input option elements
    const inputOptions = document.querySelectorAll('.input-option');
    const inputPanels = document.querySelectorAll('.input-panel');
    const closePanelButtons = document.querySelectorAll('.close-panel');
    
    // Handle input option selection
    inputOptions.forEach(option => {
        option.addEventListener('click', function() {
            const target = this.getAttribute('data-target');
            
            // Remove active class from all options
            inputOptions.forEach(opt => opt.classList.remove('active'));
            
            // Add active class to clicked option
            this.classList.add('active');
            
            // Hide all panels
            inputPanels.forEach(panel => panel.classList.remove('active'));
            
            // Show the selected panel
            document.getElementById(`${target}-panel`).classList.add('active');
        });
    });
    
    // Handle close panel buttons
    closePanelButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Hide all panels
            inputPanels.forEach(panel => panel.classList.remove('active'));
            
            // Remove active class from all options
            inputOptions.forEach(opt => opt.classList.remove('active'));
        });
    });
    
    // Progress elements
    const uploadProgress = document.getElementById('uploadProgress');
    const uploadProgressBar = document.getElementById('uploadProgressBar');
    const pasteProgress = document.getElementById('pasteProgress');
    const pasteProgressBar = document.getElementById('pasteProgressBar');
    const urlProgress = document.getElementById('urlProgress');
    const urlProgressBar = document.getElementById('urlProgressBar');
    
    // Function to update progress bar
    function updateProgressBar(progressBar, progress) {
        progressBar.style.width = `${progress}%`;
        progressBar.setAttribute('aria-valuenow', progress);
        progressBar.textContent = `${progress}%`;
    }
    
    // Function to start progress polling
    function startProgressPolling(progressElement, progressBar) {
        // Show progress bar
        progressElement.style.display = 'block';
        
        // Reset progress
        updateProgressBar(progressBar, 0);
        
        // Initialize progress tracking
        window.citationProcessing = {
            isProcessing: true,
            startTime: new Date(),
            totalCitations: 100, // Default estimate
            processedCitations: 0,
            progressInterval: null
        };
        
        // Start progress polling
        const progressInterval = setInterval(() => {
            fetch(`${basePath}/api/processing_progress?total=${window.citationProcessing.totalCitations}`, {
                method: 'GET'
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    window.citationProcessing.processedCitations = data.processed_citations;
                    
                    // Calculate progress percentage
                    const progress = data.total_citations > 0 ? 
                        Math.min(Math.round((data.processed_citations / data.total_citations) * 100), 100) : 0;
                    
                    // Update progress bar
                    updateProgressBar(progressBar, progress);
                    
                    // Check if processing is complete
                    if (data.is_complete) {
                        clearInterval(progressInterval);
                        window.citationProcessing.isProcessing = false;
                        progressBar.className = 'progress-bar bg-success';
                        progressBar.textContent = 'Complete!';
                        
                        // Switch to the appropriate results tab
                        switchToResultsTab();
                    }
                }
            })
            .catch(error => {
                console.error('Error checking progress:', error);
                clearInterval(progressInterval);
                progressBar.className = 'progress-bar bg-danger';
                progressBar.textContent = 'Error';
            });
        }, 1000);
        
        return progressInterval;
    }
    
    // Function to switch to the results tab
    function switchToResultsTab() {
        // First try CourtListener Citations tab
        const clCitationsTab = document.getElementById('cl-citations-tab');
        if (clCitationsTab) {
            clCitationsTab.click();
            return;
        }
        
        // Fall back to Verified Citations tab
        const multitoolTab = document.getElementById('multitool-tab');
        if (multitoolTab) {
            multitoolTab.click();
        }
    }
    
    // Create a results container for displaying citation results
    function createResultsContainer() {
        // Check if results container already exists
        let resultsContainer = document.getElementById('citation-results-container');
        if (!resultsContainer) {
            resultsContainer = document.createElement('div');
            resultsContainer.id = 'citation-results-container';
            resultsContainer.className = 'mt-5';
            document.querySelector('.input-panels').after(resultsContainer);
        }
        return resultsContainer;
    }
    
    // Display citation results
    function displayCitationResults(data) {
        const resultsContainer = createResultsContainer();
        
        // Create results HTML
        let html = `
            <div class="card mb-4 shadow-sm">
                <div class="card-header bg-primary text-white">
                    <h3 class="mb-0">Citation Analysis Results</h3>
                </div>
                <div class="card-body">
                    <div class="alert alert-success">
                        <i class="bi bi-check-circle-fill me-2"></i>
                        ${data.message}
                    </div>
                    <h4>Found Citations:</h4>
                    <div class="table-responsive">
                        <table class="table table-striped">
                            <thead>
                                <tr>
                                    <th>Citation</th>
                                    <th>Case Name</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
        `;
        
        // Add each citation to the table
        data.citations.forEach(citation => {
            html += `
                <tr>
                    <td><strong>${citation.text}</strong></td>
                    <td>${citation.name}</td>
                    <td>
                        ${citation.valid ? 
                            '<span class="badge bg-success">Valid</span>' : 
                            '<span class="badge bg-danger">Invalid</span>'}
                    </td>
                </tr>
            `;
        });
        
        html += `
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;
        
        resultsContainer.innerHTML = html;
        
        // Scroll to results
        resultsContainer.scrollIntoView({ behavior: 'smooth' });
    }
    
    // Handle file upload form submission
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const submitButton = this.querySelector('button[type="submit"]');
            const fileInput = document.getElementById('fileUpload');
            
            // Disable button during processing
            submitButton.disabled = true;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
            
            // Create form data
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            
            // Send request to API
            fetch(`${basePath}/api/upload`, {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                // Re-enable button
                submitButton.disabled = false;
                submitButton.innerHTML = '<i class="bi bi-upload me-2"></i>Upload and Verify';
                
                // Display results
                displayCitationResults(data);
            })
            .catch(error => {
                console.error('Error:', error);
                submitButton.disabled = false;
                submitButton.innerHTML = '<i class="bi bi-upload me-2"></i>Upload and Verify';
                alert('An error occurred while processing your file. Please try again.');
            });
            
            // This section is now handled by the validation and API call above
        });
    }
    
    // Handle paste text form submission
    if (pasteForm) {
        pasteForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const submitButton = this.querySelector('button[type="submit"]');
            const textArea = document.getElementById('textInput');
            
            // Validate input
            if (!textArea.value.trim()) {
                alert('Please enter text containing citations');
                return;
            }
            
            // Disable button during processing
            submitButton.disabled = true;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Analyzing...';
            
            // Send request to API
            fetch(`${basePath}/api/text`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: textArea.value
                })
            })
            .then(response => response.json())
            .then(data => {
                // Re-enable button
                submitButton.disabled = false;
                submitButton.innerHTML = '<i class="bi bi-check-circle me-2"></i>Verify Citations';
                
                // Display results
                displayCitationResults(data);
            })
            .catch(error => {
                console.error('Error:', error);
                submitButton.disabled = false;
                submitButton.innerHTML = '<i class="bi bi-check-circle me-2"></i>Verify Citations';
                alert('An error occurred while analyzing your text. Please try again.');
            });
        });
    }
    
    // Handle URL form submission
    if (urlForm) {
        urlForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const submitButton = this.querySelector('button[type="submit"]');
            const urlInput = document.getElementById('urlInput');
            
            // Validate input
            if (!urlInput.value.trim()) {
                alert('Please enter a valid URL');
                return;
            }
            
            // Disable button during processing
            submitButton.disabled = true;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Analyzing...';
            
            // Send request to API
            fetch(`${basePath}/api/url`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    url: urlInput.value
                })
            })
            .then(response => response.json())
            .then(data => {
                // Re-enable button
                submitButton.disabled = false;
                submitButton.innerHTML = '<i class="bi bi-globe me-2"></i>Fetch and Verify';
                
                // Display results
                displayCitationResults(data);
            })
            .catch(error => {
                console.error('Error:', error);
                submitButton.disabled = false;
                submitButton.innerHTML = '<i class="bi bi-globe me-2"></i>Fetch and Verify';
                alert('An error occurred while analyzing the URL content. Please try again.');
            });
            
            // This section is now handled by the validation and API call above
        });
    }
});
