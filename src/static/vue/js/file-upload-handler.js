/**
 * File Upload Handler
 * Handles file uploads and displays results in a citation report
 */

console.log('file-upload-handler.js loaded');

// Function to handle file upload form submission
const basePath = window.location.pathname.includes('/casestrainer/') ? '/casestrainer' : '';

function handleFileUpload(event) {
    console.log('handleFileUpload called');
    event.preventDefault();
    
    const form = document.getElementById('uploadForm');
    const fileInput = document.getElementById('fileUpload');
    const progressBar = document.getElementById('uploadProgressBar');
    const progressContainer = document.getElementById('uploadProgress');
    
    // Check if a file was selected
    if (!fileInput.files || !fileInput.files[0]) {
        alert('Please select a file to upload');
        return;
    }
    
    // Show progress bar
    progressContainer.style.display = 'block';
    progressBar.style.width = '0%';
    progressBar.textContent = '0%';
    
    // Create FormData object
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    
    // Create debug info element
    let debugInfo = document.getElementById('uploadDebugInfo');
    if (!debugInfo) {
        debugInfo = document.createElement('div');
        debugInfo.id = 'uploadDebugInfo';
        debugInfo.className = 'alert alert-info mt-3';
        debugInfo.innerHTML = '<strong>Debug:</strong> Starting file upload...';
        form.appendChild(debugInfo);
    }
    
    // Send the file to the server
    fetch(`${basePath}/api/analyze`, {
        method: 'POST',
        body: formData
    })
    .then(response => {
        // Update progress
        progressBar.style.width = '75%';
        progressBar.textContent = '75%';
        
        if (!response.ok) {
            throw new Error(`Server responded with status: ${response.status}`);
        }
        
        debugInfo.innerHTML += '<br><strong>Response received:</strong> Processing data...';
        return response.json();
    })
    .then(data => {
        console.log('Response data:', data);
        
        // Check if this is an async response with task_id
        if (data.task_id && (data.status === 'processing' || data.status === 'queued')) {
            debugInfo.innerHTML += '<br><strong>Processing:</strong> File is being processed in the background...';
            
            // Start polling for task status
            pollTaskStatus(data.task_id, debugInfo, progressBar);
        } else {
            // Direct response - display results immediately
            progressBar.style.width = '100%';
            progressBar.textContent = '100%';
            progressBar.className = 'progress-bar bg-success progress-bar-striped progress-bar-animated';
            
            debugInfo.innerHTML += '<br><strong>Success:</strong> File processed successfully';
            
            // Display the citation report
            displayResults(data);
        }
    })
    .catch(error => {
        console.error('Error during file upload:', error);
        
        // Update progress to error
        progressBar.style.width = '100%';
        progressBar.textContent = 'Error';
        progressBar.className = 'progress-bar bg-danger progress-bar-striped';
        
        // Update debug info
        debugInfo.className = 'alert alert-danger mt-3';
        debugInfo.innerHTML += `<br><strong>Error:</strong> ${error.message}`;
        
        // Display error message
        alert(`Error uploading file: ${error.message}`);
    });
}

// Function to poll task status
function pollTaskStatus(taskId, debugInfo, progressBar) {
    const maxAttempts = 60; // 5 minutes with 5-second intervals
    let attempts = 0;
    
    const pollInterval = setInterval(() => {
        attempts++;
        
        fetch(`${basePath}/api/task_status/${taskId}`)
            .then(response => {
                console.log('Raw response:', response);
                console.log('Response status:', response.status);
                console.log('Response headers:', response.headers);
                return response.json();
            })
            .then(data => {
                console.log('Task status:', data);
                console.log('Task status type:', typeof data.status);
                console.log('Task status value:', data.status);
                console.log('Task citations:', data.citations);
                console.log('Task result:', data.result);
                console.log('Task success:', data.success);
                console.log('Full response data:', JSON.stringify(data, null, 2));
                console.log('Checking condition:', (data.status === 'finished' || data.status === 'completed') && (data.citations || data.clusters));
                console.log('Status check:', data.status === 'finished' || data.status === 'completed');
                console.log('Data check:', data.citations || data.clusters);
                
                if ((data.status === 'finished' || data.status === 'completed') && (data.citations || data.clusters)) {
                    clearInterval(pollInterval);
                    
                    // Update progress to complete
                    progressBar.style.width = '100%';
                    progressBar.textContent = '100%';
                    progressBar.className = 'progress-bar bg-success progress-bar-striped progress-bar-animated';
                    
                    debugInfo.innerHTML += '<br><strong>Success:</strong> File processing completed!';
                    
                    // Pass the whole data object to displayResults
                    displayResults(data);
                } else if (data.status === 'failed') {
                    clearInterval(pollInterval);
                    
                    progressBar.style.width = '100%';
                    progressBar.textContent = 'Error';
                    progressBar.className = 'progress-bar bg-danger progress-bar-striped';
                    
                    debugInfo.className = 'alert alert-danger mt-3';
                    debugInfo.innerHTML += `<br><strong>Error:</strong> ${data.error || 'Task failed'}`;
                } else {
                    // Still processing - update progress
                    const progress = Math.min(90, attempts * 2); // Show progress up to 90%
                    progressBar.style.width = `${progress}%`;
                    progressBar.textContent = `${progress}%`;
                    
                    debugInfo.innerHTML += `<br><strong>Processing:</strong> Still working... (${attempts}/${maxAttempts})`;
                }
            })
            .catch(error => {
                console.error('Error polling task status:', error);
                debugInfo.innerHTML += `<br><strong>Error:</strong> ${error.message}`;
            });
        
        // Stop polling after max attempts
        if (attempts >= maxAttempts) {
            clearInterval(pollInterval);
            progressBar.style.width = '100%';
            progressBar.textContent = 'Timeout';
            progressBar.className = 'progress-bar bg-warning progress-bar-striped';
            
            debugInfo.className = 'alert alert-warning mt-3';
            debugInfo.innerHTML += '<br><strong>Warning:</strong> Processing is taking longer than expected. Please check back later.';
        }
    }, 5000); // Poll every 5 seconds
}

// Function to display results
function displayResults(data) {
    // Display the citation report
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
                // Fallback to appending after the form
                const form = document.getElementById('uploadForm');
                if (form) {
                    form.parentNode.appendChild(reportContainer);
                }
            }
        }
        
        // Display the citation report
        window.citationReport.display(data);
        
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
