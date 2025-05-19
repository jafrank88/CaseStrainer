/**
 * CourtListener Citations Tab functionality
 * Displays citations found in the CourtListener database with links to the original cases
 */

document.addEventListener('DOMContentLoaded', function() {
  // Get elements
  const clCitationsTab = document.getElementById('cl-citations-tab');
  const clCitationsLoading = document.getElementById('cl-citations-loading');
  const clCitationsContent = document.getElementById('cl-citations-content');
  const clCitationsList = document.getElementById('cl-citations-list');
  const clCitationsSearch = document.getElementById('cl-citations-search');
  
  // Determine the base path for API calls
  const basePath = window.location.pathname.includes('/casestrainer/') ? '/casestrainer' : '';
  
  // Store citations data
  let clCitationsData = [];
  
  // Function to load CourtListener citations
  function loadCourtListenerCitations() {
    // Show loading indicator
    clCitationsLoading.style.display = 'block';
    clCitationsContent.style.display = 'none';
    
    // Fetch CourtListener citations
    const apiUrl = `${basePath}/api/courtlistener_citations`;
    fetch(`${basePath}/api/courtlistener_citations`)
      .then(response => response.json())
      .then(data => {
        // Store the data
        clCitationsData = data.citations || [];
        
        // Display the citations
        displayCourtListenerCitations(clCitationsData);
        
        // Hide loading indicator
        clCitationsLoading.style.display = 'none';
        clCitationsContent.style.display = 'block';
      })
      .catch(error => {
        console.error('Error loading CourtListener citations:', error);
        clCitationsLoading.style.display = 'none';
        clCitationsContent.style.display = 'block';
        clCitationsList.innerHTML = `<div class="alert alert-danger">Error loading CourtListener citations: ${error.message}</div>`;
      });
  }
  
  // Function to display CourtListener citations
  function displayCourtListenerCitations(citations) {
    const container = document.getElementById('cl-citations-list');
    container.innerHTML = '';
    
    citations.forEach(group => {
        const item = document.createElement('div');
        item.className = 'list-group-item';
        
        // Create the main citation display with count
        const citationDisplay = document.createElement('div');
        citationDisplay.className = 'd-flex justify-content-between align-items-center';
        
        const citationText = document.createElement('div');
        const docCaseName = group.citation.extracted_case_name || group.citation.name_in_document || 'Case name in document: (not found)';
        const clCaseName = group.citation.case_name || 'Case name from CourtListener: (not found)';
        const clCaseUrl = group.citation.url;
        citationText.innerHTML = `
            <strong>${group.citation.citation_text}</strong>
            ${group.count > 1 ? `<span class="badge bg-primary ms-2">${group.count} occurrences</span>` : ''}
            <br>
            <span class="text-muted">${docCaseName}</span>
            <br>
            ${clCaseUrl && clCaseName !== 'Case name from CourtListener: (not found)' ? `<a href="${clCaseUrl}" target="_blank" class="text-decoration-underline">${clCaseName}</a>` : `<span class="text-muted">${clCaseName}</span>`}
        `;
        
        const actions = document.createElement('div');
        if (group.citation.url) {
            actions.innerHTML = `
                <a href="${group.citation.url}" target="_blank" class="btn btn-sm btn-outline-primary">
                    <i class="bi bi-box-arrow-up-right"></i> View Case
                </a>
            `;
        }
        
        citationDisplay.appendChild(citationText);
        citationDisplay.appendChild(actions);
        item.appendChild(citationDisplay);
        
        // Add contexts if available
        if (group.contexts && group.contexts.length > 0) {
            const contextsDiv = document.createElement('div');
            contextsDiv.className = 'mt-2';
            contextsDiv.innerHTML = '<small class="text-muted">Contexts:</small>';
            
            const contextsList = document.createElement('ul');
            contextsList.className = 'list-unstyled ms-3';
            group.contexts.forEach(context => {
                const contextItem = document.createElement('li');
                contextItem.className = 'text-muted small';
                contextItem.textContent = context;
                contextsList.appendChild(contextItem);
            });
            
            contextsDiv.appendChild(contextsList);
            item.appendChild(contextsDiv);
        }
        
        container.appendChild(item);
    });
    
    // Show the content and hide loading
    document.getElementById('cl-citations-loading').style.display = 'none';
    document.getElementById('cl-citations-content').style.display = 'block';
  }
  
  // Function to filter citations based on search input
  function filterCitations(searchText) {
    if (!searchText) {
      displayCourtListenerCitations(clCitationsData);
      return;
    }
    
    const searchLower = searchText.toLowerCase();
    const filtered = clCitationsData.filter(citation => {
      const citationText = (citation.citation_text || '').toLowerCase();
      const caseName = (citation.case_name || '').toLowerCase();
      return citationText.includes(searchLower) || caseName.includes(searchLower);
    });
    
    displayCourtListenerCitations(filtered);
  }
  
  // Add event listener to the tab
  if (clCitationsTab) {
    clCitationsTab.addEventListener('shown.bs.tab', function() {
      loadCourtListenerCitations();
    });
  }
  
  // Add event listener to the search input
  if (clCitationsSearch) {
    clCitationsSearch.addEventListener('input', function() {
      filterCitations(this.value);
    });
  }
});
