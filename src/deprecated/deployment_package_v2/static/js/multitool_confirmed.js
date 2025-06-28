// Multitool Confirmed Citations Tab JavaScript
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing multitool confirmed tab...');
    
    // Always load the data when the page loads
    loadMultitoolConfirmedCitations();
    
    // Check if we're on the multitool-confirmed tab based on URL hash
    if (window.location.hash === '#multitool-confirmed') {
        console.log('URL hash indicates multitool-confirmed tab, activating tab...');
        // Activate the multitool-confirmed tab
        const multitoolTab = document.getElementById('multitool-confirmed-tab');
        if (multitoolTab) {
            multitoolTab.click();
        }
    }
    
    // Add a visible notification to alert users about the new tab
    const mainContainer = document.querySelector('.container-fluid');
    if (mainContainer) {
        const notification = document.createElement('div');
        notification.className = 'alert alert-info alert-dismissible fade show';
        notification.innerHTML = `
            <strong>New Feature!</strong> Check out our new <a href="#" onclick="document.getElementById('multitool-confirmed-tab').click(); return false;">Confirmed with Multitool</a> tab to see citations verified by alternative sources.
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        mainContainer.insertBefore(notification, mainContainer.firstChild);
    }
    // Variables to store citation data and pagination state
    let multitoolCitations = [];
    let multitoolCurrentPage = 1;
    const multitoolItemsPerPage = 10;
    
    // Only load citations when the multitool confirmed tab is shown
    const multitoolTab = document.getElementById('multitool-confirmed-tab');
    console.log('Multitool tab element:', multitoolTab);
    if (multitoolTab) {
        multitoolTab.addEventListener('click', function() {
            console.log('Multitool tab clicked, loading citations...');
            loadMultitoolConfirmedCitations();
        });
    } else {
        console.error('Multitool tab element not found in the DOM');
    }
    
    // Event listener for refresh button
    const refreshButton = document.getElementById('refreshMultitoolCitations');
    if (refreshButton) {
        refreshButton.addEventListener('click', loadMultitoolConfirmedCitations);
    }
    
    // Function to load multitool confirmed citations
    function loadMultitoolConfirmedCitations() {
        const tableBody = document.getElementById('multitoolCitationsTable');
        console.log('Table body element:', tableBody);
        if (!tableBody) {
            console.error('Table body element not found');
            return;
        }
        
        // Show loading indicator
        tableBody.innerHTML = '<tr><td colspan="5" class="text-center">Loading citations...</td></tr>';
        console.log('Loading indicator added to table');
        
        // Determine the correct URL based on the current host and path
        let baseUrl = '';
        if (window.location.hostname === 'wolf.law.uw.edu' || window.location.pathname.includes('/casestrainer')) {
            baseUrl = '/casestrainer';
        }
        const fetchUrl = `${baseUrl}/confirmed_with_multitool/data`;
        console.log('Fetching data from:', fetchUrl);
        
        // For debugging, also log the complete URL
        console.log('Complete URL:', window.location.origin + fetchUrl);
        
        // Fetch citations from the server
        fetch(fetchUrl)
            .then(response => {
                console.log('Response status:', response.status);
                if (!response.ok) {
                    throw new Error(`Server returned ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Received data:', data);
                multitoolCitations = data.citations || [];
                console.log(`Loaded ${multitoolCitations.length} citations`);
                displayMultitoolCitations(multitoolCitations, 1);
                updateMultitoolPagination(multitoolCitations.length, 1);
            })
            .catch(error => {
                console.error('Error loading multitool confirmed citations:', error);
                tableBody.innerHTML = 
                    `<tr><td colspan="5" class="text-center text-danger">Error loading citations: ${error.message}</td></tr>`;
            });
    }
    
    // Function to display multitool confirmed citations with pagination
    function displayMultitoolCitations(citations, page) {
        const tableBody = document.getElementById('multitoolCitationsTable');
        if (!tableBody) return;
        
        tableBody.innerHTML = '';
        
        if (citations.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="5" class="text-center">No citations found.</td></tr>';
            return;
        }
        
        // Calculate pagination
        const start = (page - 1) * multitoolItemsPerPage;
        const end = Math.min(start + multitoolItemsPerPage, citations.length);
        const paginatedCitations = citations.slice(start, end);
        
        // Create table rows
        paginatedCitations.forEach((citation, index) => {
            const actualIndex = start + index;
            const row = document.createElement('tr');
            
            // Citation text
            const citationCell = document.createElement('td');
            citationCell.textContent = citation.citation_text;
            row.appendChild(citationCell);
            
            // Brief URL
            const urlCell = document.createElement('td');
            if (citation.brief_url) {
                const link = document.createElement('a');
                link.href = citation.brief_url;
                link.textContent = 'View Brief';
                link.target = '_blank';
                urlCell.appendChild(link);
            } else {
                urlCell.textContent = 'N/A';
            }
            row.appendChild(urlCell);
            
            // Verification source
            const sourceCell = document.createElement('td');
            sourceCell.textContent = citation.verification_source || 'Unknown';
            row.appendChild(sourceCell);
            
            // Confidence
            const confidenceCell = document.createElement('td');
            const confidence = parseFloat(citation.verification_confidence) || 0;
            confidenceCell.textContent = confidence.toFixed(2);
            row.appendChild(confidenceCell);
            
            // Actions
            const actionsCell = document.createElement('td');
            const detailsButton = document.createElement('button');
            detailsButton.className = 'btn btn-sm btn-info';
            detailsButton.textContent = 'Details';
            detailsButton.onclick = function() { showMultitoolCitationDetails(actualIndex); };
            actionsCell.appendChild(detailsButton);
            row.appendChild(actionsCell);
            
            tableBody.appendChild(row);
        });
    }
    
    // Function to update pagination controls for multitool citations
    function updateMultitoolPagination(totalItems, currentPage) {
        const paginationContainer = document.getElementById('multitoolPagination');
        if (!paginationContainer) return;
        
        paginationContainer.innerHTML = '';
        
        if (totalItems <= multitoolItemsPerPage) {
            return; // No pagination needed
        }
        
        const totalPages = Math.ceil(totalItems / multitoolItemsPerPage);
        const paginationNav = document.createElement('nav');
        const paginationList = document.createElement('ul');
        paginationList.className = 'pagination';
        
        // Previous button
        const prevItem = document.createElement('li');
        prevItem.className = 'page-item' + (currentPage === 1 ? ' disabled' : '');
        const prevLink = document.createElement('a');
        prevLink.className = 'page-link';
        prevLink.href = '#';
        prevLink.textContent = 'Previous';
        prevLink.onclick = function(e) {
            e.preventDefault();
            if (currentPage > 1) {
                changeMultitoolPage(currentPage - 1);
            }
        };
        prevItem.appendChild(prevLink);
        paginationList.appendChild(prevItem);
        
        // Page numbers
        for (let i = 1; i <= totalPages; i++) {
            const pageItem = document.createElement('li');
            pageItem.className = 'page-item' + (i === currentPage ? ' active' : '');
            const pageLink = document.createElement('a');
            pageLink.className = 'page-link';
            pageLink.href = '#';
            pageLink.textContent = i;
            pageLink.onclick = function(e) {
                e.preventDefault();
                changeMultitoolPage(i);
            };
            pageItem.appendChild(pageLink);
            paginationList.appendChild(pageItem);
        }
        
        // Next button
        const nextItem = document.createElement('li');
        nextItem.className = 'page-item' + (currentPage === totalPages ? ' disabled' : '');
        const nextLink = document.createElement('a');
        nextLink.className = 'page-link';
        nextLink.href = '#';
        nextLink.textContent = 'Next';
        nextLink.onclick = function(e) {
            e.preventDefault();
            if (currentPage < totalPages) {
                changeMultitoolPage(currentPage + 1);
            }
        };
        nextItem.appendChild(nextLink);
        paginationList.appendChild(nextItem);
        
        paginationNav.appendChild(paginationList);
        paginationContainer.appendChild(paginationNav);
    }
    
    // Function to change the current page for multitool citations
    function changeMultitoolPage(page) {
        multitoolCurrentPage = page;
        displayMultitoolCitations(multitoolCitations, page);
        updateMultitoolPagination(multitoolCitations.length, page);
        
        // Scroll to top of the table
        const tableElement = document.getElementById('multitoolCitationsTable');
        if (tableElement) {
            tableElement.scrollIntoView({ behavior: 'smooth' });
        }
    }
    
    // Function to show multitool citation details in a modal
    function showMultitoolCitationDetails(index) {
        const citation = multitoolCitations[index];
        if (!citation) return;
        
        const modalContent = document.getElementById('multitoolCitationDetailsContent');
        if (!modalContent) return;
        
        // Create content
        let content = `
            <div class="card mb-3">
                <div class="card-header bg-primary text-white">Citation Information</div>
                <div class="card-body">
                    <p><strong>Citation:</strong> ${citation.citation_text}</p>
                    <p><strong>Verification Source:</strong> ${citation.verification_source || 'Unknown'}</p>
                    <p><strong>Confidence:</strong> ${(parseFloat(citation.verification_confidence) || 0).toFixed(2)}</p>
                </div>
            </div>
        `;
        
        // Add context if available
        if (citation.context) {
            content += `
                <div class="card mb-3">
                    <div class="card-header bg-info text-white">Context</div>
                    <div class="card-body">
                        <p>${citation.context}</p>
                    </div>
                </div>
            `;
        }
        
        // Add explanation if available
        if (citation.verification_explanation) {
            content += `
                <div class="card mb-3">
                    <div class="card-header bg-success text-white">Verification Explanation</div>
                    <div class="card-body">
                        <p>${citation.verification_explanation}</p>
                    </div>
                </div>
            `;
        }
        
        // Set content and show modal
        modalContent.innerHTML = content;
        const modalElement = document.getElementById('multitoolCitationDetailsModal');
        if (modalElement) {
            const modal = new bootstrap.Modal(modalElement);
            modal.show();
        }
    }
});
