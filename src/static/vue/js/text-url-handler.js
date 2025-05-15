/**
 * Text and URL Input Handler
 * Handles text paste and URL input submissions and displays results in a citation report
 */

// Function to handle text paste form submission
function handleTextSubmit(event) {
    event.preventDefault();
    
    const form = document.getElementById('pasteForm');
    const textArea = document.getElementById('textInput');
    const progressBar = document.getElementById('pasteProgressBar');
    const progressContainer = document.getElementById('pasteProgress');
    
    // Check if text was entered
    if (!textArea.value.trim()) {
        alert('Please enter text containing citations');
        return;
    }
    
    // Show progress bar
    progressContainer.style.display = 'block';
    progressBar.style.width = '0%';
    progressBar.textContent = '0%';
    
    // Create debug info element
    let debugInfo = document.getElementById('textDebugInfo');
    if (!debugInfo) {
        debugInfo = document.createElement('div');
        debugInfo.id = 'textDebugInfo';
        debugInfo.className = 'alert alert-info mt-3';
        debugInfo.innerHTML = '<strong>Debug:</strong> Starting text analysis...';
        form.appendChild(debugInfo);
    }
    
    // Update progress
    progressBar.style.width = '25%';
    progressBar.textContent = '25%';
    
    // Send the text to the server
    fetch('/api/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            text: textArea.value
        })
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
        
        debugInfo.innerHTML += '<br><strong>Success:</strong> Text processed successfully';
        
        // Display the citation report
        displayCitationReport(data);
    })
    .catch(error => {
        console.error('Error during text analysis:', error);
        
        // Update progress to error
        progressBar.style.width = '100%';
        progressBar.textContent = 'Error';
        progressBar.className = 'progress-bar bg-danger progress-bar-striped';
        
        // Update debug info
        debugInfo.className = 'alert alert-danger mt-3';
        debugInfo.innerHTML += `<br><strong>Error:</strong> ${error.message}`;
        
        // Display error message
        alert(`Error analyzing text: ${error.message}`);
    });
}

// Function to handle URL input form submission
function handleUrlSubmit(event) {
    event.preventDefault();
    
    const form = document.getElementById('urlForm');
    const urlInput = document.getElementById('urlInput');
    const progressBar = document.getElementById('urlProgressBar');
    const progressContainer = document.getElementById('urlProgress');
    
    // Check if URL was entered
    if (!urlInput.value.trim()) {
        alert('Please enter a valid URL');
        return;
    }
    
    // Validate URL format
    try {
        new URL(urlInput.value);
    } catch (e) {
        alert('Please enter a valid URL (including http:// or https://)');
        return;
    }
    
    // Show progress bar
    progressContainer.style.display = 'block';
    progressBar.style.width = '0%';
    progressBar.textContent = '0%';
    
    // Create debug info element
    let debugInfo = document.getElementById('urlDebugInfo');
    if (!debugInfo) {
        debugInfo = document.createElement('div');
        debugInfo.id = 'urlDebugInfo';
        debugInfo.className = 'alert alert-info mt-3';
        debugInfo.innerHTML = '<strong>Debug:</strong> Starting URL analysis...';
        form.appendChild(debugInfo);
    }
    
    // Update progress
    progressBar.style.width = '25%';
    progressBar.textContent = '25%';
    
    // Send the URL to the server
    fetch('/api/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            url: urlInput.value
        })
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
        
        debugInfo.innerHTML += '<br><strong>Success:</strong> URL processed successfully';
        
        // Display the citation report
        displayCitationReport(data);
    })
    .catch(error => {
        console.error('Error during URL analysis:', error);
        
        // Update progress to error
        progressBar.style.width = '100%';
        progressBar.textContent = 'Error';
        progressBar.className = 'progress-bar bg-danger progress-bar-striped';
        
        // Update debug info
        debugInfo.className = 'alert alert-danger mt-3';
        debugInfo.innerHTML += `<br><strong>Error:</strong> ${error.message}`;
        
        // Display error message
        alert(`Error analyzing URL: ${error.message}`);
    });
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
                // Fallback to appending to the body
                document.body.appendChild(reportContainer);
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

// Attach event listeners when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Text paste form
    const pasteForm = document.getElementById('pasteForm');
    if (pasteForm) {
        pasteForm.addEventListener('submit', handleTextSubmit);
    }
    
    // URL input form
    const urlForm = document.getElementById('urlForm');
    if (urlForm) {
        urlForm.addEventListener('submit', handleUrlSubmit);
    }
});
