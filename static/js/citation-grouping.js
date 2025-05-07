/**
 * Citation Grouping JavaScript Module for CaseStrainer
 * 
 * This module provides functions to group and display citations in the UI.
 */

/**
 * Create a grouped citation dropdown item
 * @param {Object} group - The citation group
 * @returns {HTMLElement} - The dropdown item element
 */
function createGroupedCitationItem(group) {
    const item = document.createElement('div');
    item.className = 'citation-group';
    
    // Create header with case name and citation count
    const header = document.createElement('div');
    header.className = 'citation-group-header';
    
    // Determine if the case is real or hallucinated
    const isHallucinated = group.is_hallucinated === true;
    const statusClass = isHallucinated ? 'text-danger' : 'text-success';
    const statusIcon = isHallucinated ? 
        '<i class="bi bi-exclamation-triangle-fill"></i>' : 
        '<i class="bi bi-check-circle-fill"></i>';
    
    header.innerHTML = `
        <div class="d-flex justify-content-between align-items-center">
            <span class="case-name">${group.case_name || 'Unknown Case'}</span>
            <span class="badge bg-secondary">${group.alternate_citations.length + 1} citations</span>
        </div>
        <div class="d-flex justify-content-between align-items-center mt-1">
            <span class="citation-text">${group.citation}</span>
            <span class="${statusClass}">${statusIcon}</span>
        </div>
    `;
    
    // Create content with all citations
    const content = document.createElement('div');
    content.className = 'citation-group-content';
    
    // Add primary citation
    const primaryCitation = document.createElement('div');
    primaryCitation.className = 'citation-item primary-citation';
    
    // Add court listener link if available
    let courtListenerLink = '';
    if (group.url) {
        courtListenerLink = `
            <a href="${group.url}" target="_blank" class="btn btn-sm btn-outline-primary">
                <i class="bi bi-box-arrow-up-right"></i> View Case
            </a>
        `;
    }
    
    primaryCitation.innerHTML = `
        <div class="d-flex justify-content-between align-items-center">
            <div>
                <div class="fw-bold">${group.citation}</div>
                <div class="text-muted small">Source: ${group.source || 'Unknown'}</div>
            </div>
            <div>
                ${courtListenerLink}
            </div>
        </div>
    `;
    content.appendChild(primaryCitation);
    
    // Add alternate citations if available
    if (group.alternate_citations && group.alternate_citations.length > 0) {
        const altHeader = document.createElement('div');
        altHeader.className = 'alternate-citations-header mt-2 mb-1';
        altHeader.textContent = 'Alternate Citations:';
        content.appendChild(altHeader);
        
        group.alternate_citations.forEach(alt => {
            const altCitation = document.createElement('div');
            altCitation.className = 'citation-item alternate-citation';
            
            // Add court listener link if available
            let altCourtListenerLink = '';
            if (alt.url) {
                altCourtListenerLink = `
                    <a href="${alt.url}" target="_blank" class="btn btn-sm btn-outline-secondary">
                        <i class="bi bi-box-arrow-up-right"></i> View
                    </a>
                `;
            }
            
            altCitation.innerHTML = `
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <div>${alt.citation}</div>
                        <div class="text-muted small">Source: ${alt.source || 'Unknown'}</div>
                    </div>
                    <div>
                        ${altCourtListenerLink}
                    </div>
                </div>
            `;
            content.appendChild(altCitation);
        });
    }
    
    // Add click event to toggle content visibility
    header.addEventListener('click', function() {
        content.classList.toggle('show');
        header.classList.toggle('active');
    });
    
    item.appendChild(header);
    item.appendChild(content);
    
    return item;
}

/**
 * Display grouped citations in the container
 * @param {Array} groupedCitations - Array of grouped citation objects
 * @param {HTMLElement} container - Container element to display the citations
 */
function displayGroupedCitations(groupedCitations, container) {
    // Clear the container
    container.innerHTML = '';
    
    if (!groupedCitations || groupedCitations.length === 0) {
        const noResults = document.createElement('p');
        noResults.textContent = 'No citations found.';
        container.appendChild(noResults);
        return;
    }
    
    // Create a container for the grouped citations
    const groupsContainer = document.createElement('div');
    groupsContainer.className = 'citation-groups';
    
    // Add each group to the container
    groupedCitations.forEach(group => {
        const groupItem = createGroupedCitationItem(group);
        groupsContainer.appendChild(groupItem);
    });
    
    container.appendChild(groupsContainer);
}

/**
 * Create a citation dropdown menu with grouped citations
 * @param {Array} groupedCitations - Array of grouped citation objects
 * @param {HTMLElement} dropdownElement - Dropdown element to populate
 * @param {Function} onCitationSelect - Callback function when a citation is selected
 */
function createCitationDropdown(groupedCitations, dropdownElement, onCitationSelect) {
    // Clear the dropdown
    dropdownElement.innerHTML = '';
    
    if (!groupedCitations || groupedCitations.length === 0) {
        const noResults = document.createElement('div');
        noResults.className = 'dropdown-item disabled';
        noResults.textContent = 'No citations found.';
        dropdownElement.appendChild(noResults);
        return;
    }
    
    // Add each group to the dropdown
    groupedCitations.forEach(group => {
        // Create group header
        const groupHeader = document.createElement('div');
        groupHeader.className = 'dropdown-group-header';
        groupHeader.textContent = group.case_name || 'Unknown Case';
        dropdownElement.appendChild(groupHeader);
        
        // Create primary citation item
        const primaryItem = document.createElement('div');
        primaryItem.className = 'dropdown-item primary-citation';
        primaryItem.innerHTML = `
            <span>${group.citation}</span>
            ${group.url ? `<a href="${group.url}" target="_blank" class="citation-link">View Case</a>` : ''}
        `;
        primaryItem.addEventListener('click', function() {
            onCitationSelect(group.citation);
        });
        dropdownElement.appendChild(primaryItem);
        
        // Add alternate citations
        if (group.alternate_citations && group.alternate_citations.length > 0) {
            group.alternate_citations.forEach(alt => {
                const altItem = document.createElement('div');
                altItem.className = 'dropdown-item alternate-citation';
                altItem.innerHTML = `
                    <span>${alt.citation}</span>
                    ${alt.url ? `<a href="${alt.url}" target="_blank" class="citation-link">View Case</a>` : ''}
                `;
                altItem.addEventListener('click', function() {
                    onCitationSelect(alt.citation);
                });
                dropdownElement.appendChild(altItem);
            });
        }
        
        // Add divider
        const divider = document.createElement('div');
        divider.className = 'dropdown-divider';
        dropdownElement.appendChild(divider);
    });
}
