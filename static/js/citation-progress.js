/**
 * Citation Progress Tracker for CaseStrainer
 * Provides real-time progress feedback for citation analysis
 */

class CitationProgressTracker {
    constructor() {
        this.taskId = null;
        this.eventSource = null;
        this.progressCallback = null;
        this.completeCallback = null;
        this.errorCallback = null;
        this.isPolling = false;
        this.pollInterval = null;
    }
    
    /**
     * Start citation analysis with Server-Sent Events (Recommended)
     */
    startAnalysisWithSSE(documentText, documentType, progressCallback, completeCallback, errorCallback) {
        this.progressCallback = progressCallback;
        this.completeCallback = completeCallback;
        this.errorCallback = errorCallback;
        
        // Start the analysis
        fetch('/casestrainer/api/analyze/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: documentText,
                document_type: documentType
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.task_id) {
                this.taskId = data.task_id;
                this.connectToProgressStream();
            } else {
                throw new Error(data.error || 'Failed to start analysis');
            }
        })
        .catch(error => {
            console.error('Error starting analysis:', error);
            if (this.errorCallback) {
                this.errorCallback({ error: error.message });
            }
        });
    }
    
    /**
     * Connect to Server-Sent Events stream
     */
    connectToProgressStream() {
        if (this.eventSource) {
            this.eventSource.close();
        }
        
        this.eventSource = new EventSource(
            `/casestrainer/api/analyze/progress-stream/${this.taskId}`
        );
        
        this.eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                
                if (data.error) {
                    this.handleError(data.error);
                    return;
                }
                
                if (data.results) {
                    // Final results received
                    this.handleComplete(data);
                } else {
                    // Progress update
                    this.handleProgress(data);
                }
                
            } catch (error) {
                console.error('Error parsing progress data:', error);
            }
        };
        
        this.eventSource.onerror = (error) => {
            console.error('SSE connection error:', error);
            this.eventSource.close();
            // Fallback to polling
            this.startPolling();
        };
    }
    
    /**
     * Polling fallback method
     */
    startPolling() {
        if (this.isPolling) return;
        
        this.isPolling = true;
        this.pollInterval = setInterval(async () => {
            try {
                const response = await fetch(`/casestrainer/api/analyze/progress/${this.taskId}`);
                const data = await response.json();
                
                if (data.error) {
                    clearInterval(this.pollInterval);
                    this.handleError(data.error);
                    return;
                }
                
                this.handleProgress(data);
                
                if (data.status === 'completed' || data.status === 'failed') {
                    clearInterval(this.pollInterval);
                    
                    // Get final results
                    const resultsResponse = await fetch(`/casestrainer/api/analyze/results/${this.taskId}`);
                    const results = await resultsResponse.json();
                    this.handleComplete(results);
                }
                
            } catch (error) {
                clearInterval(this.pollInterval);
                this.handleError(error.message);
            }
        }, 1000); // Poll every second
    }
    
    /**
     * Handle progress updates
     */
    handleProgress(progressData) {
        if (this.progressCallback) {
            this.progressCallback({
                progress: progressData.progress,
                message: progressData.message,
                currentStep: progressData.current_step,
                totalSteps: progressData.total_steps,
                resultsCount: progressData.results_count,
                estimatedCompletion: progressData.estimated_completion,
                status: progressData.status
            });
        }
        
        // Update UI
        this.updateProgressBar(progressData.progress);
        this.updateStatusMessage(progressData.message);
        
        // Show partial results if available
        if (progressData.partial_results) {
            this.showPartialResults(progressData.partial_results);
        }
    }
    
    /**
     * Handle completion
     */
    handleComplete(results) {
        this.cleanup();
        
        if (this.completeCallback) {
            this.completeCallback(results);
        }
        
        // Hide progress bar, show final results
        this.hideProgressBar();
        this.showFinalResults(results);
    }
    
    /**
     * Handle errors
     */
    handleError(error) {
        this.cleanup();
        
        console.error('Citation analysis error:', error);
        
        if (this.errorCallback) {
            this.errorCallback({ error: error });
        }
        
        this.hideProgressBar();
        this.showError(error);
    }
    
    /**
     * Update progress bar UI
     */
    updateProgressBar(progress) {
        const progressBar = document.getElementById('citation-progress-bar');
        if (progressBar) {
            progressBar.style.width = `${progress}%`;
            progressBar.setAttribute('aria-valuenow', progress);
        }
        
        const progressText = document.getElementById('progress-text');
        if (progressText) {
            progressText.textContent = `${Math.round(progress)}%`;
        }
    }
    
    /**
     * Update status message
     */
    updateStatusMessage(message) {
        const statusElement = document.getElementById('progress-status');
        if (statusElement) {
            statusElement.textContent = message;
        }
    }
    
    /**
     * Show partial results as they're found
     */
    showPartialResults(partialResults) {
        const partialContainer = document.getElementById('partial-results');
        if (partialContainer && partialResults.length > 0) {
            partialResults.forEach(citation => {
                const citationElement = this.createCitationElement(citation);
                partialContainer.appendChild(citationElement);
            });
        }
    }
    
    /**
     * Create citation element for display
     */
    createCitationElement(citation) {
        const div = document.createElement('div');
        div.className = 'citation-preview';
        div.innerHTML = `
            <div class="citation-case-name">${citation.case_name || 'Unknown Case'}</div>
            <div class="citation-details">
                <span class="year">${citation.year || 'No year'}</span>
                <span class="confidence">Confidence: ${Math.round((citation.confidence_score || 0) * 100)}%</span>
            </div>
        `;
        return div;
    }
    
    /**
     * Hide progress bar
     */
    hideProgressBar() {
        const progressContainer = document.getElementById('progress-container');
        if (progressContainer) {
            progressContainer.style.display = 'none';
        }
    }
    
    /**
     * Show final results
     */
    showFinalResults(results) {
        const resultsContainer = document.getElementById('final-results');
        if (resultsContainer) {
            resultsContainer.innerHTML = this.formatFinalResults(results);
            resultsContainer.style.display = 'block';
        }
    }
    
    /**
     * Format final results for display
     */
    formatFinalResults(results) {
        return `
            <h3>Citation Analysis Complete</h3>
            <p>Found ${results.results ? results.results.length : 0} citations</p>
            <div class="citations-list">
                ${results.results ? results.results.map(citation => this.formatCitation(citation)).join('') : ''}
            </div>
        `;
    }
    
    /**
     * Format individual citation for display
     */
    formatCitation(citation) {
        return `
            <div class="citation-item">
                <div class="citation-text">${citation.raw_text || citation.text || 'Unknown'}</div>
                <div class="citation-details">
                    <span class="case-name">${citation.case_name || 'Unknown Case'}</span>
                    <span class="year">${citation.year || 'No year'}</span>
                    <span class="confidence">Confidence: ${Math.round((citation.confidence_score || 0) * 100)}%</span>
                </div>
            </div>
        `;
    }
    
    /**
     * Show error message
     */
    showError(error) {
        const errorContainer = document.getElementById('error-container');
        if (errorContainer) {
            errorContainer.innerHTML = `<div class="alert alert-danger">Error: ${error}</div>`;
            errorContainer.style.display = 'block';
        }
    }
    
    /**
     * Cleanup resources
     */
    cleanup() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
        
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
        }
        
        this.isPolling = false;
    }
    
    /**
     * Stop tracking
     */
    stop() {
        this.cleanup();
        this.taskId = null;
        this.progressCallback = null;
        this.completeCallback = null;
        this.errorCallback = null;
    }
}

// Vue.js composable for progress tracking
function useCitationProgress() {
    const tracker = new CitationProgressTracker();
    
    const startAnalysis = (documentText, documentType, callbacks = {}) => {
        return new Promise((resolve, reject) => {
            tracker.startAnalysisWithSSE(
                documentText,
                documentType,
                callbacks.progress || (() => {}),
                (results) => {
                    resolve(results);
                },
                (error) => {
                    reject(error);
                }
            );
        });
    };
    
    const stopAnalysis = () => {
        tracker.stop();
    };
    
    return {
        startAnalysis,
        stopAnalysis,
        tracker
    };
}

// Export for use in different environments
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { CitationProgressTracker, useCitationProgress };
} else if (typeof window !== 'undefined') {
    window.CitationProgressTracker = CitationProgressTracker;
    window.useCitationProgress = useCitationProgress;
} 