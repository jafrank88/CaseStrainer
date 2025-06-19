// Global state to track processing status
window.citationProcessing = {
    isProcessing: false,
    analysisId: null,
    totalCitations: 0,
    processedCitations: 0,
    progressInterval: null
};

document.addEventListener('DOMContentLoaded', function() {
    // Determine the base path for API calls
    const basePath = window.location.pathname.includes('/casestrainer/') ? '/casestrainer' : '';
    
    // Get form elements
    const uploadForm = document.getElementById('uploadForm');
    const pasteForm = document.getElementById('pasteForm');
    const urlForm = document.getElementById('urlForm');
    
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
            totalCitations: 100, // Default estimate
            processedCitations: 0,
            progressInterval: null
        };
        
        // Start progress polling
        const progressInterval = setInterval(() => {
            fetch(apiUrl('/api/enhanced/analyze'), {
                method: 'GET'
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    const progress = data.total_citations > 0 ? 
                        Math.min(Math.round((data.processed_citations / data.total_citations) * 100), 100) : 0;
                    
                    // Update progress bar
                    updateProgressBar(progressBar, progress);
                    
                    // Check if processing is complete
                    if (data.is_complete) {
                        clearInterval(progressInterval);
                        window.citationProcessing.isProcessing = false;
                        progressBar.className = 'progress-bar bg-success';
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
    
    // Handle file upload form submission
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const submitButton = this.querySelector('button[type="submit"]');
            submitButton.disabled = true;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Analyzing...';
            
            const fileInput = document.getElementById('fileUpload');
            if (!fileInput.files || fileInput.files.length === 0) {
                alert('Please select a file to upload');
                submitButton.disabled = false;
                submitButton.textContent = 'Analyze Citations';
                return;
            }
            
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            
            // Start progress tracking
            const progressInterval = startProgressPolling(uploadProgress, uploadProgressBar);
            
            // Submit the form
            fetch(apiUrl('/api/enhanced/analyze'), {
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
            })
            .catch(error => {
                console.error('Error analyzing file:', error);
                alert('Error analyzing file: ' + error.message);
                
                // Reset button
                submitButton.disabled = false;
                submitButton.textContent = 'Analyze Citations';
                
                // Hide progress bar
                uploadProgress.style.display = 'none';
                
                // Clear progress interval
                clearInterval(progressInterval);
            });
        });
    }
    
    // Handle paste text form submission
    if (pasteForm) {
        pasteForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const submitButton = this.querySelector('button[type="submit"]');
            submitButton.disabled = true;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Analyzing...';
            
            const textInput = document.getElementById('textInput');
            if (!textInput.value.trim()) {
                alert('Please enter some text to analyze');
                submitButton.disabled = false;
                submitButton.textContent = 'Analyze Citations';
                return;
            }
            
            const formData = new FormData();
            formData.append('text', textInput.value);
            
            // Start progress tracking
            const progressInterval = startProgressPolling(pasteProgress, pasteProgressBar);
            
            // Submit the form
            fetch(apiUrl('/api/enhanced/analyze'), {
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
            })
            .catch(error => {
                console.error('Error analyzing text:', error);
                alert('Error analyzing text: ' + error.message);
                
                // Reset button
                submitButton.disabled = false;
                submitButton.textContent = 'Analyze Citations';
                
                // Hide progress bar
                pasteProgress.style.display = 'none';
                
                // Clear progress interval
                clearInterval(progressInterval);
            });
        });
    }
    
    // Handle URL form submission
    if (urlForm) {
        urlForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const submitButton = this.querySelector('button[type="submit"]');
            submitButton.disabled = true;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Analyzing...';
            
            const urlInput = document.getElementById('urlInput');
            if (!urlInput.value.trim()) {
                alert('Please enter a URL to analyze');
                submitButton.disabled = false;
                submitButton.textContent = 'Analyze Citations';
                return;
            }
            
            // Start progress tracking
            const progressInterval = startProgressPolling(urlProgress, urlProgressBar);
            
            // First fetch the URL content
            fetch(apiUrl('/api/analyze'), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ url: urlInput.value })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.status === 'success' && data.text) {
                    // Now analyze the fetched text
                    const textFormData = new FormData();
                    textFormData.append('text', data.text);
                    
                    return fetch(apiUrl('/api/enhanced/analyze'), {
                        method: 'POST',
                        body: textFormData
                    });
                } else {
                    throw new Error(data.message || 'Failed to fetch URL content');
                }
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
                submitButton.disabled = false;
                submitButton.textContent = 'Analyze Citations';
                
                // Switch to the Multitool tab to show results
                const multitoolTab = document.getElementById('multitool-tab');
                if (multitoolTab) {
                    multitoolTab.click();
                }
            })
            .catch(error => {
                console.error('Error analyzing URL:', error);
                alert('Error analyzing URL: ' + error.message);
                
                // Reset button
                submitButton.disabled = false;
                submitButton.textContent = 'Analyze Citations';
                
                // Hide progress bar
                urlProgress.style.display = 'none';
                
                // Clear progress interval
                clearInterval(progressInterval);
            });
        });
    }
});
