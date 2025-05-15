/**
 * File Upload Handler
 * Handles file uploads and displays results in a citation report
 */

// Function to handle file upload form submission
function handleFileUpload(event) {
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
    fetch('/api/upload', {
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
        // Update progress to complete
        progressBar.style.width = '100%';
        progressBar.textContent = '100%';
        progressBar.className = 'progress-bar bg-success progress-bar-striped progress-bar-animated';
        
        debugInfo.innerHTML += '<br><strong>Success:</strong> File processed successfully';
        
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
                    form.parentNode.appendChild(reportContainer);
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
