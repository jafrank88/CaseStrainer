/**
 * Citation Report Generator
 * Creates a tabbed report showing citations organized by verification status
 */

// Function to create the citation report
function createCitationReport(citations, containerId) {
    // Get the container element
    const container = document.getElementById(containerId) || document.createElement('div');
    if (!container.id) {
        container.id = containerId;
        document.body.appendChild(container);
    }
    
    // Categorize citations
    const verifiedByCourtListener = [];
    const verifiedAnotherWay = [];
    const notVerified = [];
    
    // Process and categorize each citation
    citations.forEach(citation => {
        if (citation.valid && citation.metadata && citation.metadata.source === 'CourtListener') {
            verifiedByCourtListener.push(citation);
        } else if (citation.valid) {
            verifiedAnotherWay.push(citation);
        } else {
            notVerified.push(citation);
        }
    });
    
    // Create HTML for the report
    const html = `
        <div class="card mb-4 shadow-sm">
            <div class="card-header bg-primary text-white">
                <h3 class="mb-0">Citation Analysis Report</h3>
            </div>
            <div class="card-body">
                <ul class="nav nav-tabs" id="citationTabs" role="tablist">
                    <li class="nav-item" role="presentation">
                        <button class="nav-link active" id="court-listener-tab" data-bs-toggle="tab" data-bs-target="#court-listener" type="button" role="tab" aria-controls="court-listener" aria-selected="true">
                            Verified by CourtListener <span class="badge bg-primary">${verifiedByCourtListener.length}</span>
                        </button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="other-verified-tab" data-bs-toggle="tab" data-bs-target="#other-verified" type="button" role="tab" aria-controls="other-verified" aria-selected="false">
                            Verified Another Way <span class="badge bg-primary">${verifiedAnotherWay.length}</span>
                        </button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="not-verified-tab" data-bs-toggle="tab" data-bs-target="#not-verified" type="button" role="tab" aria-controls="not-verified" aria-selected="false">
                            Not Verified <span class="badge bg-danger">${notVerified.length}</span>
                        </button>
                    </li>
                </ul>
                
                <div class="tab-content pt-3" id="citationTabsContent">
                    <!-- Verified by CourtListener -->
                    <div class="tab-pane fade show active" id="court-listener" role="tabpanel" aria-labelledby="court-listener-tab">
                        ${createCitationTable(verifiedByCourtListener, 'CourtListener')}
                    </div>
                    
                    <!-- Verified Another Way -->
                    <div class="tab-pane fade" id="other-verified" role="tabpanel" aria-labelledby="other-verified-tab">
                        ${createCitationTable(verifiedAnotherWay, 'Other Sources')}
                    </div>
                    
                    <!-- Not Verified -->
                    <div class="tab-pane fade" id="not-verified" role="tabpanel" aria-labelledby="not-verified-tab">
                        ${createCitationTable(notVerified, 'Unverified')}
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Set the HTML content
    container.innerHTML = html;
    
    // Return the container for chaining
    return container;
}

// Helper function to create a table for citations
function createCitationTable(citations, source) {
    if (citations.length === 0) {
        return `<div class="alert alert-info">No citations in this category.</div>`;
    }
    
    let tableHtml = `
        <div class="table-responsive">
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>Citation</th>
                        <th>Case Name</th>
                        <th>Details</th>
                        ${source === 'Unverified' ? '<th>Explanation</th>' : ''}
                    </tr>
                </thead>
                <tbody>
    `;
    
    citations.forEach(citation => {
        // Determine if this is a Westlaw citation
        const isWestlaw = citation.text && citation.text.match(/\d+\s+WL\s+\d+/i);
        const isId = citation.text && citation.text.match(/^Id\.$/i);
        const isSupra = citation.text && citation.text.match(/supra/i);
        
        // Add special styling for different citation types
        let citationClass = '';
        if (isWestlaw) citationClass = 'text-info';
        if (isId || isSupra) citationClass = 'text-warning';
        
        tableHtml += `
            <tr>
                <td><strong class="${citationClass}">${citation.text}</strong></td>
                <td>${citation.name || 'Unknown Case'}</td>
                <td>
        `;
        
        // Add metadata if available
        if (citation.metadata) {
            if (citation.metadata.year) {
                tableHtml += `<div>Year: ${citation.metadata.year}</div>`;
            }
            if (citation.metadata.court) {
                tableHtml += `<div>Court: ${citation.metadata.court}</div>`;
            }
            if (citation.metadata.reporter) {
                tableHtml += `<div>Reporter: ${citation.metadata.reporter}</div>`;
            }
            if (citation.metadata.volume) {
                tableHtml += `<div>Volume: ${citation.metadata.volume}</div>`;
            }
            if (citation.metadata.page) {
                tableHtml += `<div>Page: ${citation.metadata.page}</div>`;
            }
            if (citation.metadata.source) {
                tableHtml += `<div>Source: ${citation.metadata.source}</div>`;
            }
        }
        
        // Add verification status
        if (source === 'CourtListener') {
            tableHtml += `<div class="mt-2 badge bg-success">Verified by CourtListener</div>`;
        } else if (source === 'Other Sources') {
            tableHtml += `<div class="mt-2 badge bg-success">Verified by ${citation.metadata?.source || 'Alternative Source'}</div>`;
        }
        
        tableHtml += `
                </td>
        `;
        
        // Add explanation column for unverified citations
        if (source === 'Unverified') {
            let explanation = '';
            
            // Use explanation from the API if available
            if (citation.explanation) {
                explanation = citation.explanation;
            }
            // Otherwise generate explanations based on citation type
            else if (isWestlaw) {
                explanation = 'Westlaw citations require subscription access and may not be verifiable through public APIs.';
            } else if (isId) {
                explanation = '"Id." citations refer to the immediately preceding citation and cannot be verified independently.';
            } else if (isSupra) {
                explanation = '"Supra" citations refer to earlier citations in the document and cannot be verified independently.';
            } else {
                explanation = 'Citation could not be verified through available APIs.';
            }
            
            tableHtml += `<td><span class="text-muted">${explanation}</span></td>`;
        }
        
        tableHtml += `
            </tr>
        `;
    });
    
    tableHtml += `
                </tbody>
            </table>
        </div>
    `;
    
    return tableHtml;
}

// Function to display the citation report
function displayCitationReport(data) {
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
    
    // Create the citation report
    createCitationReport(data.citations, 'citation-report-container');
    
    // Display a success message
    const messageContainer = document.createElement('div');
    messageContainer.className = 'alert alert-success';
    messageContainer.innerHTML = `
        <i class="bi bi-check-circle-fill me-2"></i>
        ${data.message}
    `;
    reportContainer.prepend(messageContainer);
}

// Export the functions
window.citationReport = {
    create: createCitationReport,
    display: displayCitationReport
};
