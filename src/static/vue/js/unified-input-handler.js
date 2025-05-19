/**
 * Unified Input Handler for CaseStrainer
 * Handles all three input methods (file upload, text paste, URL) with a consistent approach
 */

// Main handler function that processes all input types
function handleCitationInput(inputType, inputData) {
    console.log(`handleCitationInput called with type: ${inputType}`, inputData);
    
    // Get the appropriate form and progress elements based on input type
    const formId = `${inputType}Form`;
    const progressId = `${inputType}Progress`;
    const progressBarId = `${inputType}ProgressBar`;
    
    console.log(`Looking for elements with IDs: ${formId}, ${progressId}, ${progressBarId}`);
    
    // Get the form element
    const form = document.getElementById(formId);
    console.log(`Form element (${formId}):`, form);
    
    // Get the progress bar elements
    const progressContainer = document.getElementById(progressId);
    console.log(`Progress container (${progressId}):`, progressContainer);
    
    const progressBar = document.getElementById(progressBarId);
    console.log(`Progress bar (${progressBarId}):`, progressBar);
    
    if (!form) {
        console.error(`Missing form element: ${formId}`);
    }
    
    if (!progressContainer) {
        console.error(`Missing progress container: ${progressId}`);
    }
    
    if (!progressBar) {
        console.error(`Missing progress bar: ${progressBarId}`);
    }
    
    if (!form || !progressContainer || !progressBar) {
        console.error(`Missing UI elements for ${inputType} input`);
        return false;
    }
    
    // Validate input data
    if (!validateInput(inputType, inputData)) {
        return;
    }
    
    // Initialize progress bar
    progressContainer.style.display = 'block';
    progressBar.style.width = '0%';
    progressBar.textContent = '0%';
    progressBar.className = 'progress-bar progress-bar-striped progress-bar-animated';
    
    // Clear any previous debug info
    const debugInfoId = `${inputType}DebugInfo`;
    let debugInfo = document.getElementById(debugInfoId);
    if (debugInfo) {
        debugInfo.remove();
    }
    
    // Create new debug info element
    debugInfo = document.createElement('div');
    debugInfo.id = debugInfoId;
    debugInfo.className = 'alert alert-info mt-3';
    debugInfo.innerHTML = `<strong>Debug:</strong> Starting ${inputType} analysis...`;
    form.appendChild(debugInfo);
    
    // Update progress to show we're starting
    progressBar.style.width = '25%';
    progressBar.textContent = '25%';
    progressBar.className = 'progress-bar progress-bar-striped progress-bar-animated';
    
    // Prepare request data and endpoint
    // Determine the base path based on the current URL
    let basePath = '';
    if (window.location.pathname.includes('/casestrainer/')) {
        basePath = '/casestrainer';
    }
    
    // Log the detected base path for debugging
    console.log(`Detected base path: '${basePath}'`);
    console.log(`Current pathname: '${window.location.pathname}'`);
    
    let endpoint;
    
    // Use different endpoints based on input type
    if (inputType === 'file') {
        // For file uploads, send extracted text as JSON to the enhanced validator endpoint
        endpoint = '/casestrainer/enhanced-validator/api/analyze';
        console.log(`Using enhanced validator endpoint for file upload: ${endpoint}`);
    } else {
        endpoint = `${basePath}/api/analyze`;
        console.log(`Using analyze endpoint: ${endpoint}`);
    }

    console.log(`Using endpoint for ${inputType}:`, endpoint);
    let requestData;

    // For file uploads, read the file as text, then send as JSON
    if (inputType === 'file') {
        const file = inputData;
        if (!file) {
            alert('Please select a file to upload');
            return false;
        }
        const reader = new FileReader();
        reader.onload = function(event) {
            const fileText = event.target.result;
            requestData = { text: fileText };
            debugInfo.innerHTML += `<br><strong>Extracted Text (${fileText.length} chars)</strong>`;
            // Set up request options
            const requestOptions = {
                method: 'POST',
                body: JSON.stringify(requestData),
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                credentials: 'same-origin',
                mode: 'cors'
            };
            // Log the full request details
            console.log('Sending request to:', endpoint);
            console.log('Request options:', {
                method: requestOptions.method,
                headers: requestOptions.headers,
                body: '[Extracted file text as JSON]'
            });
            debugInfo.innerHTML += `<br><strong>Request to ${endpoint}:</strong> [Extracted file text as JSON]`;
            // Send the request to the server
            progressBar.style.width = '50%';
            progressBar.textContent = '50%';
            fetch(endpoint, requestOptions)
                .then(response => {
                    console.log('Received response status:', response.status, response.statusText);
                    progressBar.style.width = '75%';
                    progressBar.textContent = '75%';
                    const contentType = response.headers.get('content-type');
                    console.log('Response content type:', contentType);
                    if (!response.ok) {
                        return response.text().then(text => {
                            console.error('Error response body:', text);
                            throw new Error(`Server responded with status: ${response.status} - ${text}`);
                        });
                    }
                    debugInfo.innerHTML += '<br><strong>Response received:</strong> Processing data...';
                    return response.json().then(json => {
                        console.log('Parsed JSON response:', json);
                        return json;
                    }).catch(err => {
                        console.error('Error parsing JSON response:', err);
                        throw new Error('Failed to parse server response as JSON');
                    });
                })
                .then(data => {
                    progressBar.style.width = '100%';
                    progressBar.textContent = '100%';
                    progressBar.className = 'progress-bar bg-success progress-bar-striped progress-bar-animated';
                    debugInfo.innerHTML += '<br><strong>Success:</strong> ' + JSON.stringify(data, null, 2);
                    displayCitationReport(data);
                })
                .catch(error => {
                    console.error(`Error during file analysis:`, error);
                    progressBar.style.width = '100%';
                    progressBar.textContent = 'Error';
                    progressBar.className = 'progress-bar bg-danger progress-bar-striped';
                    debugInfo.className = 'alert alert-danger mt-3';
                    debugInfo.innerHTML += `<br><strong>Error:</strong> ${error.message}`;
                    alert(`Error analyzing file: ${error.message}`);
                });
        };
        reader.onerror = function(event) {
            console.error('File reading error:', event);
            progressBar.style.width = '100%';
            progressBar.textContent = 'Error';
            progressBar.className = 'progress-bar bg-danger progress-bar-striped';
            debugInfo.className = 'alert alert-danger mt-3';
            debugInfo.innerHTML += `<br><strong>Error:</strong> Failed to read file.`;
            alert('Failed to read file.');
        };
        reader.readAsText(file);
        return; // Prevent the rest of the function from executing for file
    }

    switch (inputType) {
            
        case 'text':
            // For text input, create JSON object
            const text = inputData.trim();
            console.log('Text input received:', text.substring(0, 100) + '...');
            
            if (!text) {
                const errorMsg = 'Please enter text containing citations';
                console.error(errorMsg);
                alert(errorMsg);
                return false;
            }
            
            requestData = {
                text: text
            };
            
            // Add debug info
            const debugText = text.length > 100 ? text.substring(0, 100) + '...' : text;
            debugInfo.innerHTML += `<br><strong>Text Input (${text.length} chars):</strong> ${debugText}`;
            console.log('Request data prepared:', requestData);
            break;
            
        case 'url':
            // For URL input, create JSON object
            const url = inputData.trim();
            if (!url) {
                alert('Please enter a valid URL');
                return false;
            }
            
            requestData = {
                url: url
            };
            
            // Add debug info
            debugInfo.innerHTML += '<br><strong>URL Input:</strong> ' + url;
            break;
    }
    
    // Set up request options
    const requestOptions = {
        method: 'POST',
        body: inputType === 'file' ? requestData : JSON.stringify(requestData),
        headers: inputType !== 'file' ? {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        } : {},
        credentials: 'same-origin',
        mode: 'cors'
    };
    
    // For file uploads, let the browser set the Content-Type header with boundary
    if (inputType === 'file') {
        delete requestOptions.headers; // Let the browser set the correct Content-Type with boundary
    }
    
    // Log the full request details
    console.log('Sending request to:', endpoint);
    console.log('Request options:', {
        method: requestOptions.method,
        headers: requestOptions.headers,
        body: inputType === 'file' ? '[FormData]' : requestOptions.body
    });
    
    // Add request debug info
    const debugRequest = inputType === 'file' 
        ? '[File data]' 
        : JSON.stringify(requestData, null, 2);
    debugInfo.innerHTML += `<br><strong>Request to ${endpoint}:</strong> ${debugRequest}`;
    
    // Send the request to the server
    console.log('Initiating fetch request...');
    fetch(endpoint, requestOptions)
        .then(response => {
            console.log('Received response status:', response.status, response.statusText);
            
            // Update progress
            progressBar.style.width = '75%';
            progressBar.textContent = '75%';
            
            // Log response headers for debugging
            const contentType = response.headers.get('content-type');
            console.log('Response content type:', contentType);
            
            if (!response.ok) {
                return response.text().then(text => {
                    console.error('Error response body:', text);
                    throw new Error(`Server responded with status: ${response.status} - ${text}`);
                });
            }
            
            debugInfo.innerHTML += '<br><strong>Response received:</strong> Processing data...';
            
            return response.json().then(json => {
                console.log('Parsed JSON response:', json);
                return json;
            }).catch(err => {
                console.error('Error parsing JSON response:', err);
                throw new Error('Failed to parse server response as JSON');
            });
        })
        .then(data => {
            // Update progress to complete
            progressBar.style.width = '100%';
            progressBar.textContent = '100%';
            progressBar.className = 'progress-bar bg-success progress-bar-striped progress-bar-animated';
            
            debugInfo.innerHTML += '<br><strong>Success:</strong> ' + JSON.stringify(data, null, 2);
            
            // Display the citation report
            displayCitationReport(data);
        })
        .catch(error => {
            console.error(`Error during ${inputType} analysis:`, error);
            
            // Update progress to error
            progressBar.style.width = '100%';
            progressBar.textContent = 'Error';
            progressBar.className = 'progress-bar bg-danger progress-bar-striped';
            
            // Update debug info
            debugInfo.className = 'alert alert-danger mt-3';
            debugInfo.innerHTML += `<br><strong>Error:</strong> ${error.message}`;
            
            // Display error message
            alert(`Error analyzing ${inputType}: ${error.message}`);
        });
}

// Input validation function
function validateInput(inputType, inputData) {
    switch (inputType) {
        case 'file':
            if (!inputData) {
                alert('Please select a file to upload');
                return false;
            }
            return true;
            
        case 'text':
            if (!inputData.trim()) {
                alert('Please enter text containing citations');
                return false;
            }
            return true;
            
        case 'url':
            // Validate URL input
            const url = inputData.trim();
            if (!url) {
                alert('Please enter a valid URL');
                return false;
            }
            
            // Validate URL format
            try {
                new URL(url);
            } catch (e) {
                alert('Please enter a valid URL (including http:// or https://)');
                return false;
            }
            
            return true;
    }
}

// Helper function to update progress bar
function updateProgress(progressBar, percentage, success = false, error = false) {
    progressBar.style.width = `${percentage}%`;
    progressBar.textContent = error ? 'Error' : `${percentage}%`;
    
    if (success) {
        progressBar.className = 'progress-bar bg-success progress-bar-striped progress-bar-animated';
    } else if (error) {
        progressBar.className = 'progress-bar bg-danger progress-bar-striped';
    } else {
        progressBar.className = 'progress-bar progress-bar-striped progress-bar-animated';
    }
}

// Helper function to display citation report
function displayCitationReport(data) {
    if (window.citationReport && typeof window.citationReport.display === 'function') {
        // Create a container for the report if it doesn't exist
        let reportContainer = document.getElementById('citation-report-container');
        if (!reportContainer) {
            reportContainer = document.createElement('div');
            reportContainer.id = 'citation-report-container';
            reportContainer.className = 'mt-4';
            
            // Find a good place to insert the report
            const resultsContainer = document.getElementById('resultsContainer');
            if (resultsContainer) {
                resultsContainer.appendChild(reportContainer);
            } else {
                // Find the analyze tab content
                const analyzeTab = document.getElementById('analyze');
                if (analyzeTab) {
                    analyzeTab.appendChild(reportContainer);
                } else {
                    // Fallback to appending to the body
                    document.body.appendChild(reportContainer);
                }
            }
        }
        
        // Add summary information before the citation report
        const summaryContainer = document.createElement('div');
        summaryContainer.className = 'card mb-4';
        
        // Calculate citation counts based on the actual response format
        const totalCitations = data.citations ? data.citations.length : 0;
        const confirmedCitations = data.citations ? data.citations.filter(c => c.valid === true).length : 0;
        const unconfirmedCitations = data.citations ? data.citations.filter(c => c.valid === false).length : 0;
        
        summaryContainer.innerHTML = `
            <div class="card-header bg-primary text-white">
                <h4 class="mb-0">Citation Analysis Summary</h4>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-4 text-center">
                        <div class="h1">${totalCitations}</div>
                        <div>Total Citations</div>
                    </div>
                    <div class="col-md-4 text-center">
                        <div class="h1 text-success">${confirmedCitations}</div>
                        <div>Confirmed Citations</div>
                    </div>
                    <div class="col-md-4 text-center">
                        <div class="h1 text-danger">${unconfirmedCitations}</div>
                        <div>Unconfirmed Citations</div>
                    </div>
                </div>
                <div class="mt-3">
                    <p class="mb-0"><strong>Processing Time:</strong> ${data.processing_time ? data.processing_time.toFixed(2) + ' seconds' : 'N/A'}</p>
                    <p class="mb-0"><strong>Message:</strong> ${data.message || 'Analysis complete'}</p>
                </div>
            </div>
        `;
        
        reportContainer.appendChild(summaryContainer);
        
        // Prepare the data for the citation report
        // The citation report expects a specific format
        const reportData = {
            citations: data.citations || [],
            message: data.message || '',
            processing_time: data.processing_time || 0
        };
        
        // Create a simple citation report if the window.citationReport is not available
        if (!window.citationReport || typeof window.citationReport.display !== 'function') {
            console.log('Creating simple citation report');
            // Create a simple report
            const simpleReport = document.createElement('div');
            simpleReport.className = 'card mt-4';
            
            // Count citations by validity
            const verifiedByCourtListener = reportData.citations.filter(c => c.valid && c.source === 'courtlistener').length;
            const verifiedOtherWay = reportData.citations.filter(c => c.valid && c.source !== 'courtlistener').length;
            const notVerified = reportData.citations.filter(c => !c.valid).length;
            
            simpleReport.innerHTML = `
                <div class="card-header bg-info text-white">
                    <h4 class="mb-0">Citation Analysis Report</h4>
                </div>
                <div class="card-body">
                    <div class="row mb-4">
                        <div class="col-md-4">
                            <div class="card bg-light">
                                <div class="card-body text-center">
                                    <h5>Verified by CourtListener</h5>
                                    <div class="display-4">${verifiedByCourtListener}</div>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card bg-light">
                                <div class="card-body text-center">
                                    <h5>Verified Another Way</h5>
                                    <div class="display-4">${verifiedOtherWay}</div>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card bg-light">
                                <div class="card-body text-center">
                                    <h5>Not Verified</h5>
                                    <div class="display-4">${notVerified}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="citation-list mt-4">
                        ${reportData.citations.map(citation => `
                            <div class="card mb-3 ${citation.valid ? 'border-success' : 'border-warning'}">
                                <div class="card-header ${citation.valid ? 'bg-success text-white' : 'bg-warning'}">
                                    <h5 class="mb-0">
  ${citation.url && citation.name ? `<a href="${citation.url}" target="_blank">${citation.name}</a>` : (citation.name || 'Unknown Case')}
</h5>
                                </div>
                                <div class="card-body">
                                    <p><strong>Citation:</strong> ${citation.text}</p>
                                    <p><strong>Status:</strong> ${citation.valid ? 'Verified' : 'Not Verified'}</p>
                                    <p><strong>Explanation:</strong> ${citation.explanation || 'No explanation provided'}</p>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
            
            reportContainer.appendChild(simpleReport);
        } else {
            // Use the citation report tool if available
            console.log('Using citation report tool');
            window.citationReport.display(reportData);
        }
        
        // Scroll to the report
        reportContainer.scrollIntoView({ behavior: 'smooth' });
    } else {
        // Fallback if citation report script is not available
        alert('Citation report functionality not available. Please use the Citation Report Tool page.');
        
        // Store the data in localStorage for use in the citation report page
        localStorage.setItem('citationData', JSON.stringify(data));
        
        // Redirect to the citation report page
        window.location.href = 'citation-report.html';
    }
}

// Event handler functions for the different input methods
function handleFileUpload(event) {
    console.log('handleFileUpload called', event);
    event.preventDefault();
    
    const fileInput = document.getElementById('fileUpload');
    console.log('File input element:', fileInput);
    
    if (!fileInput) {
        console.error('Could not find file input element');
        alert('Error: Could not find file input');
        return false;
    }
    
    if (!fileInput.files || fileInput.files.length === 0) {
        console.log('No file selected');
        alert('Please select a file to upload');
        return false;
    }
    
    const file = fileInput.files[0];
    console.log('Selected file:', file);
    
    // Call handleCitationInput with the file
    return handleCitationInput('file', file);
}

function handleTextSubmit(event) {
    event.preventDefault();
    const textInput = document.getElementById('textInput');
    if (textInput && textInput.value.trim() !== '') {
        handleCitationInput('text', textInput.value);
    } else {
        alert('Please enter some text to analyze');
    }
}

function handleUrlSubmit(event) {
    event.preventDefault();
    const urlInput = document.getElementById('urlInput');
    if (urlInput && urlInput.value.trim() !== '') {
        handleCitationInput('url', urlInput.value);
    } else {
        alert('Please enter a URL to analyze');
    }
}

// Attach event listeners when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, setting up event listeners...');
    
    // File upload form
    const fileForm = document.getElementById('fileForm');
    if (fileForm) {
        console.log('Found file form');
        fileForm.addEventListener('submit', handleFileUpload);
    } else {
        console.error('Could not find file form');
    }
    
    // Text paste form
    const pasteForm = document.getElementById('pasteForm');
    if (pasteForm) {
        console.log('Found paste form');
        pasteForm.addEventListener('submit', handleTextSubmit);
    } else {
        console.error('Could not find paste form');
    }
    
    // URL input form
    const urlForm = document.getElementById('urlForm');
    if (urlForm) {
        console.log('Found URL form');
        urlForm.addEventListener('submit', handleUrlSubmit);
    } else {
        console.error('Could not find URL form');
    }
    
    // Also add click handlers to the buttons for better UX
    const analyzeFileBtn = document.querySelector('#file-panel button[onclick^="handleCitationInput"]');
    if (analyzeFileBtn) {
        console.log('Found file analyze button');
        analyzeFileBtn.onclick = handleFileUpload;
    } else {
        console.error('Could not find file analyze button');
    }
    
    const analyzeTextBtn = document.querySelector('#text-panel button[onclick^="handleCitationInput"]');
    if (analyzeTextBtn) {
        console.log('Found text analyze button');
        analyzeTextBtn.onclick = handleTextSubmit;
    } else {
        console.error('Could not find text analyze button');
    }
    
    const analyzeUrlBtn = document.querySelector('#url-panel button[onclick^="handleCitationInput"]');
    if (analyzeUrlBtn) {
        console.log('Found URL analyze button');
        analyzeUrlBtn.onclick = handleUrlSubmit;
    } else {
        console.error('Could not find URL analyze button');
    }
    
    console.log('Event listeners setup complete');
});
