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
    console.log('DOMContentLoaded event fired - initializing CaseStrainer JS');
    
    // Always use the /casestrainer/ prefix for API calls to work with Nginx proxy
    const basePath = window.location.pathname.includes('/casestrainer/') ? '/casestrainer' : '';
    console.log('Base path for API calls:', basePath);
    
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
        
        // Use the citation report functionality from citation-report.js
        if (window.citationReport && typeof window.citationReport.display === 'function') {
            // Use the new citation report functionality
            window.citationReport.display(data);
        } else {
            // Fallback to a simple display if the citation report script is not loaded
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
                        <p>Found ${data.citations.length} citations.</p>
                    </div>
                </div>
            `;
            resultsContainer.innerHTML = html;
        }
        
        // Scroll to results
        resultsContainer.scrollIntoView({ behavior: 'smooth' });
    }
    
    // Add immediate debug logging
    console.log('Document loaded, checking for uploadForm:', uploadForm ? 'Found' : 'Not found');
    if (uploadForm) {
        console.log('Adding event listener to uploadForm');
    } else {
        console.error('ERROR: uploadForm not found! DOM might not be properly loaded or form ID is incorrect');
        // Try to find the form by other means
        const possibleForms = document.querySelectorAll('form');
        console.log(`Found ${possibleForms.length} forms on the page:`);
        possibleForms.forEach((form, i) => {
            console.log(`Form ${i+1} ID: ${form.id}, Action: ${form.action}`);
        });
    }
    
    // Handle file upload form submission
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            console.log('Upload form submit event triggered!');
            e.preventDefault();
            
            const submitButton = this.querySelector('button[type="submit"]');
            const fileInput = document.getElementById('fileUpload');
            
            // Disable button during processing
            submitButton.disabled = true;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
            
            // Show progress bar
            const progressElement = document.getElementById('uploadProgress');
            const progressBar = document.getElementById('uploadProgressBar');
            
            // Start progress polling
            const progressInterval = startProgressPolling(progressElement, progressBar);
            
            // Create form data
            const formData = new FormData();
            const file = fileInput.files[0];
            formData.append('file', file);
            
            // Create debug div
            const debugDiv = document.createElement('div');
            debugDiv.className = 'alert alert-info mt-3';
            debugDiv.innerHTML = `<h5>Debug Information</h5>`;
            progressElement.parentNode.insertBefore(debugDiv, progressElement);
            
            // Function to add debug info
            function addDebugInfo(message) {
                const timestamp = new Date().toISOString();
                console.log(`[${timestamp}] ${message}`);
                const msgElement = document.createElement('p');
                msgElement.textContent = `[${timestamp}] ${message}`;
                debugDiv.appendChild(msgElement);
            }
            
            // Log file details for debugging
            addDebugInfo(`File upload initiated: ${file.name} (${file.size} bytes, ${file.type})`);
            
            // Send request to API
            const uploadUrl = `${basePath}/api/upload`;
            addDebugInfo(`Sending file to ${uploadUrl} endpoint...`);
            addDebugInfo(`Current pathname: ${window.location.pathname}`);
            addDebugInfo(`Base path: ${basePath}`);
            
            fetch(uploadUrl, {
                method: 'POST',
                headers: {
                    'Accept': 'application/json',
                    // Don't set Content-Type with FormData as the browser will set it with the boundary
                },
                body: formData,
                credentials: 'same-origin'
            })
            .then(response => {
                // Log response details
                const responseInfo = {
                    status: response.status,
                    statusText: response.statusText,
                    headers: Object.fromEntries([...response.headers]),
                    timestamp: new Date().toISOString()
                };
                
                addDebugInfo(`Response received: ${response.status} ${response.statusText}`);
                addDebugInfo(`Content-Type: ${response.headers.get('Content-Type')}`);
                
                if (!response.ok) {
                    addDebugInfo(`ERROR: Server returned error status: ${response.status}`);
                    throw new Error(`Server responded with status: ${response.status}`);
                }
                
                addDebugInfo('Response OK, parsing JSON...');
                return response.json().catch(error => {
                    addDebugInfo(`ERROR: Failed to parse JSON response: ${error.message}`);
                    throw error;
                });
            })
            .then(data => {
                addDebugInfo('JSON parsed successfully!');
                addDebugInfo(`Found ${data.citations ? data.citations.length : 0} citations`);
                
                // Re-enable button
                submitButton.disabled = false;
                submitButton.innerHTML = '<i class="bi bi-upload me-2"></i>Upload and Verify';
                
                // Clear progress polling
                clearInterval(progressInterval);
                
                // Update progress to complete
                progressBar.style.width = '100%';
                progressBar.setAttribute('aria-valuenow', 100);
                progressBar.textContent = 'Complete!';
                progressBar.className = 'progress-bar bg-success';
                
                // Add more detailed debug info
                if (data.citations && data.citations.length > 0) {
                    addDebugInfo('Citation details:');
                    data.citations.forEach((citation, index) => {
                        addDebugInfo(`Citation ${index+1}: ${citation.text} (${citation.name})`);
                    });
                } else {
                    addDebugInfo('No citations found in the document.');
                }
                
                // Display results
                displayCitationResults(data);
            })
            .catch(error => {
                // Log error details
                const errorInfo = {
                    message: error.message,
                    stack: error.stack,
                    timestamp: new Date().toISOString()
                };
                console.error('File upload error:', errorInfo);
                
                // Add debug information
                addDebugInfo(`ERROR: ${error.message}`);
                addDebugInfo(`Error occurred at: ${new Date().toISOString()}`);
                
                // Try to get more details about the error
                if (error.name) addDebugInfo(`Error type: ${error.name}`);
                if (error.stack) {
                    const stackLines = error.stack.split('\n');
                    addDebugInfo(`Stack trace (first line): ${stackLines[0]}`);
                }
                
                submitButton.disabled = false;
                submitButton.innerHTML = '<i class="bi bi-upload me-2"></i>Upload and Verify';
                
                // Clear progress polling
                clearInterval(progressInterval);
                
                // Update progress to error
                progressBar.style.width = '100%';
                progressBar.setAttribute('aria-valuenow', 100);
                progressBar.textContent = 'Error!';
                progressBar.className = 'progress-bar bg-danger';
                
                // Create a more detailed error message
                const errorDetails = document.createElement('div');
                errorDetails.className = 'alert alert-danger mt-3';
                errorDetails.innerHTML = `
                    <h5>Error Processing File</h5>
                    <p>${error.message || 'Unknown error occurred'}</p>
                    <p>Please check the debug information above for more details.</p>
                    <p>Try using a different file format or a smaller file.</p>
                `;
                
                // Insert error details after the progress bar
                progressElement.parentNode.insertBefore(errorDetails, progressElement.nextSibling);
                
                // Add troubleshooting tips
                addDebugInfo('Troubleshooting tips:');
                addDebugInfo('1. Try a different file format (PDF, DOCX, TXT)');
                addDebugInfo('2. Make sure the file contains legal citations');
                addDebugInfo('3. Try a smaller file size');
                addDebugInfo('4. Check if the server is running properly');
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
            
            // Show progress bar
            const progressElement = document.getElementById('pasteProgress');
            const progressBar = document.getElementById('pasteProgressBar');
            
            // Start progress polling
            const progressInterval = startProgressPolling(progressElement, progressBar);
            
            // Send request to API
            fetch(`${basePath}/api/analyze`, {
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
                
                // Clear progress polling
                clearInterval(progressInterval);
                
                // Update progress to complete
                progressBar.style.width = '100%';
                progressBar.setAttribute('aria-valuenow', 100);
                progressBar.textContent = 'Complete!';
                progressBar.className = 'progress-bar bg-success';
                
                // Display results
                displayCitationResults(data);
            })
            .catch(error => {
                console.error('Error:', error);
                submitButton.disabled = false;
                submitButton.innerHTML = '<i class="bi bi-check-circle me-2"></i>Verify Citations';
                
                // Clear progress polling
                clearInterval(progressInterval);
                
                // Update progress to error
                progressBar.style.width = '100%';
                progressBar.setAttribute('aria-valuenow', 100);
                progressBar.textContent = 'Error!';
                progressBar.className = 'progress-bar bg-danger';
                
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
            
            // Show progress bar
            const progressElement = document.getElementById('urlProgress');
            const progressBar = document.getElementById('urlProgressBar');
            
            // Start progress polling
            const progressInterval = startProgressPolling(progressElement, progressBar);
            
            // Send request to API
            fetch(`${basePath}/api/analyze`, {
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
                
                // Clear progress polling
                clearInterval(progressInterval);
                
                // Update progress to complete
                progressBar.style.width = '100%';
                progressBar.setAttribute('aria-valuenow', 100);
                progressBar.textContent = 'Complete!';
                progressBar.className = 'progress-bar bg-success';
                
                // Display results
                displayCitationResults(data);
            })
            .catch(error => {
                console.error('Error:', error);
                submitButton.disabled = false;
                submitButton.innerHTML = '<i class="bi bi-globe me-2"></i>Fetch and Verify';
                
                // Clear progress polling
                clearInterval(progressInterval);
                
                // Update progress to error
                progressBar.style.width = '100%';
                progressBar.setAttribute('aria-valuenow', 100);
                progressBar.textContent = 'Error!';
                progressBar.className = 'progress-bar bg-danger';
                
                alert('An error occurred while analyzing the URL content. Please try again.');
            });
            
            // This section is now handled by the validation and API call above
        });
    }
    
    // Add direct event listeners to all submit buttons as a backup
    console.log('Adding direct event listeners to submit buttons');
    document.querySelectorAll('button[type="submit"]').forEach((button, index) => {
        console.log(`Found submit button ${index+1}: ${button.textContent.trim()}`);
        button.addEventListener('click', function(e) {
});

// This section is now handled by the validation and API call above
});

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

        // Show progress bar
        const progressElement = document.getElementById('pasteProgress');
        const progressBar = document.getElementById('pasteProgressBar');

        // Start progress polling
        const progressInterval = startProgressPolling(progressElement, progressBar);

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

            // Clear progress polling
            clearInterval(progressInterval);

            // Update progress to complete
            progressBar.style.width = '100%';
            progressBar.setAttribute('aria-valuenow', 100);
            progressBar.textContent = 'Complete!';
            progressBar.className = 'progress-bar bg-success';

            // Display results
            displayCitationResults(data);
        })
        .catch(error => {
            console.error('Error:', error);
            submitButton.disabled = false;
            submitButton.innerHTML = '<i class="bi bi-check-circle me-2"></i>Verify Citations';

            // Clear progress polling
            clearInterval(progressInterval);

            // Update progress to error
            progressBar.style.width = '100%';
            progressBar.setAttribute('aria-valuenow', 100);
            progressBar.textContent = 'Error!';
            progressBar.className = 'progress-bar bg-danger';

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

        // Show progress bar
        const progressElement = document.getElementById('urlProgress');
        const progressBar = document.getElementById('urlProgressBar');

        // Start progress polling
        const progressInterval = startProgressPolling(progressElement, progressBar);

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

            // Clear progress polling
            clearInterval(progressInterval);

            // Update progress to complete
            progressBar.style.width = '100%';
            progressBar.setAttribute('aria-valuenow', 100);
            progressBar.textContent = 'Complete!';
            progressBar.className = 'progress-bar bg-success';

            // Display results
            displayCitationResults(data);
        })
        .catch(error => {
            console.error('Error:', error);
            submitButton.disabled = false;
            submitButton.innerHTML = '<i class="bi bi-globe me-2"></i>Fetch and Verify';

            // Clear progress polling
            clearInterval(progressInterval);

            // Update progress to error
            progressBar.style.width = '100%';
            progressBar.setAttribute('aria-valuenow', 100);
            progressBar.textContent = 'Error!';
            progressBar.className = 'progress-bar bg-danger';

            alert('An error occurred while analyzing the URL content. Please try again.');
        });

        // This section is now handled by the validation and API call above
    });
}

// Add direct event listeners to all submit buttons as a backup
console.log('Adding direct event listeners to submit buttons');
document.querySelectorAll('button[type="submit"]').forEach((button, index) => {
    console.log(`Found submit button ${index+1}: ${button.textContent.trim()}`);
    button.addEventListener('click', function(e) {
        console.log(`Button clicked: ${this.textContent.trim()}`);
        // Don't prevent default here, let the form handler do that
    });
});

// Function to handle file upload
function handleFileUpload(event) {
    event.preventDefault();
    console.log('File upload form submitted');

    // Add debug message directly to the page
    const debugInfo = document.createElement('div');
    debugInfo.className = 'alert alert-info mt-3';
    debugInfo.innerHTML = '<strong>Debug:</strong> Form submission detected';
    document.getElementById('uploadForm').appendChild(debugInfo);

    const fileInput = document.getElementById('fileUpload');
    const file = fileInput.files[0];

    if (!file) {
        alert('Please select a file to upload');
        debugInfo.className = 'alert alert-danger mt-3';
        debugInfo.innerHTML += '<br><strong>Error:</strong> No file selected';
        return;
    }

    console.log(`Selected file: ${file.name}, Size: ${file.size}, Type: ${file.type}`);
    debugInfo.innerHTML += `<br>File: ${file.name}, Size: ${Math.round(file.size/1024)}KB, Type: ${file.type}`;

    // Based on the URL pattern we observed, it seems the application might be using a different approach
    // Let's try redirecting to the URL pattern we saw in the browser
    const redirectUrl = `${basePath}/?file=${encodeURIComponent(file.name)}`;
    debugInfo.innerHTML += `<br>Redirecting to: ${redirectUrl}`;

    // Save the file to localStorage so we can access it after the redirect
    try {
        // Create a temporary URL for the file
        const fileUrl = URL.createObjectURL(file);
        localStorage.setItem('lastUploadedFile', fileUrl);
        localStorage.setItem('lastUploadedFileName', file.name);
        debugInfo.innerHTML += '<br>File saved to localStorage for access after redirect';

        // Redirect to the URL pattern we observed
        window.location.href = redirectUrl;
    } catch (error) {
        console.error('Error saving file to localStorage:', error);
        debugInfo.className = 'alert alert-danger mt-3';
        debugInfo.innerHTML += `<br><strong>Error:</strong> ${error.message}`;

        // Fall back to the original method
        debugInfo.innerHTML += '<br>Falling back to original upload method...';

        // Show progress bar
        const progressBar = document.getElementById('uploadProgressBar');
        const progressContainer = document.getElementById('uploadProgress');
        progressContainer.style.display = 'block';
        progressBar.style.width = '0%';
        progressBar.textContent = '0%';

        const formData = new FormData();
        formData.append('file', file);

        // Make API request
        fetch('/api/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            console.log(`Response status: ${response.status}`);
            console.log(`Response headers: ${JSON.stringify(Array.from(response.headers.entries()))}`);
            console.log(`Response type: ${response.type}`);

            debugInfo.innerHTML += `<br>Response received: Status ${response.status}`;

            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }

            return response.json();
        })
        .then(data => {
            console.log('Upload successful:', data);
            progressBar.style.width = '100%';
            progressBar.textContent = '100%';

            debugInfo.innerHTML += '<br><strong>Success:</strong> File processed successfully';

            // Process the citations
            processCitations(data.citations);
        })
        .catch(error => {
            console.error('Error during file upload:', error);
            progressBar.classList.remove('bg-info');
            progressBar.classList.add('bg-danger');
            progressBar.textContent = 'Error: ' + error.message;

            debugInfo.className = 'alert alert-danger mt-3';
            debugInfo.innerHTML += `<br><strong>Error:</strong> ${error.message}`;

            // Display error message on the page
            const resultsContainer = document.getElementById('resultsContainer');
            resultsContainer.innerHTML = `
                <div class="alert alert-danger">
                    <h4>Error During File Upload</h4>
                    <p>${error.message}</p>
                    <h5>Troubleshooting:</h5>
                    <ul>
                        <li>Check that the file format is supported (.pdf, .docx, .txt, etc.)</li>
                        <li>Make sure the file is not empty or corrupted</li>
                        <li>Try using the Direct Upload button for more detailed error information</li>
                    </ul>
                </div>
            `;
        });
    }
}

// Add a manual file upload function as a last resort
window.manualFileUpload = function() {
    console.log('Manual file upload function called');
    const fileInput = document.getElementById('fileUpload');
    if (!fileInput || !fileInput.files || !fileInput.files[0]) {
        console.error('No file selected or file input not found');
        alert('Please select a file first');
        return;
    }
    
    const file = fileInput.files[0];
    console.log(`Manually uploading file: ${file.name} (${file.size} bytes)`);
    
    // Create debug info element
    const debugInfo = document.createElement('div');
    debugInfo.className = 'alert alert-info mt-3';
    debugInfo.innerHTML = '<strong>Debug:</strong> Manual upload initiated';
    document.getElementById('uploadForm').appendChild(debugInfo);
    
    // Create a new form element
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = `${basePath}/api/upload`;
    form.enctype = 'multipart/form-data';
    
    // Create a hidden input for the file name
    const fileNameInput = document.createElement('input');
    fileNameInput.type = 'hidden';
    fileNameInput.name = 'filename';
    fileNameInput.value = file.name;
    form.appendChild(fileNameInput);
    
    // Create a file input and copy the selected file
    const newFileInput = document.createElement('input');
    newFileInput.type = 'file';
    newFileInput.name = 'file';
    newFileInput.style.display = 'none';
    
    // We can't directly set the files property, so we'll use the DataTransfer API
    const dt = new DataTransfer();
    dt.items.add(file);
    newFileInput.files = dt.files;
    form.appendChild(newFileInput);
    
    // Add the form to the document and submit it
    document.body.appendChild(form);
    debugInfo.innerHTML += '<br>Created and submitting form to /casestrainer/api/analyze';
    
    try {
        form.submit();
    } catch (error) {
        console.error('Error submitting form:', error);
        debugInfo.innerHTML += `<br>Error submitting form: ${error.message}`;
        
        // Fall back to direct URL navigation
        debugInfo.innerHTML += '<br>Falling back to direct URL navigation';
        window.location.href = `/casestrainer/api/analyze?file=${encodeURIComponent(file.name)}`;
    }
};

// Add event listener to the upload form
const fileUploadForm = document.getElementById('uploadForm');
if (fileUploadForm) {
    fileUploadForm.addEventListener('submit', handleFileUpload);
}

// Add a manual upload button to the page
const filePanel = document.getElementById('file-panel');
if (filePanel) {
    const manualButton = document.createElement('button');
    manualButton.type = 'button';
    manualButton.className = 'btn btn-danger ms-2';
    manualButton.textContent = 'Direct Upload (Debug)';
    manualButton.onclick = window.manualFileUpload;
    
    // Find the submit button and insert after it
    const submitButton = filePanel.querySelector('button[type="submit"]');
    if (submitButton && submitButton.parentNode) {
        submitButton.parentNode.insertBefore(manualButton, submitButton.nextSibling);
    } else {
        filePanel.appendChild(manualButton);
    }
    
    console.log('Added manual upload button to the page');
}

// Close the DOMContentLoaded event listener
});
