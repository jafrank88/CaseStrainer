<template>
  <div class="citation-report">
    <div v-if="isLoading" class="text-center py-4">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
      <p class="mt-2 mb-0">Loading citation report...</p>
    </div>
    
    <div v-else-if="error" class="alert alert-warning">
      <i class="fas fa-exclamation-triangle me-2"></i>
      {{ error }}
    </div>
    
    <div v-else>
      <div v-if="hasResults" class="mb-4">
        <div class="d-flex justify-content-between align-items-center mb-3">
          <h5 class="mb-0">Citation Analysis Results</h5>
          <div>
            <button 
              class="btn btn-sm btn-outline-secondary me-2" 
              @click="exportToCSV"
              title="Export to CSV"
            >
              <i class="fas fa-download me-1"></i> Export
            </button>
            <button 
              class="btn btn-sm btn-outline-secondary" 
              @click="refresh"
              title="Refresh Report"
              :disabled="refreshing"
            >
              <i class="fas fa-sync-alt" :class="{ 'fa-spin': refreshing }"></i>
            </button>
          </div>
        </div>
        
        <div id="citation-report-container" class="mt-3"></div>
      </div>
      
      <div v-else class="alert alert-info mb-0">
        <i class="fas fa-info-circle me-2"></i>
        No citations found in the document.
      </div>
    </div>
  </div>
</template>

<script>
import { onMounted, ref, watch } from 'vue';
import { loadScript } from '@/utils/loadScript';

export default {
  name: 'CitationReport',
  props: {
    citationData: {
      type: Object,
      default: () => ({})
    },
    isLoading: {
      type: Boolean,
      default: false
    },
    error: {
      type: String,
      default: ''
    }
  },
  emits: ['refresh'],
  setup(props, { emit }) {
    const hasResults = ref(false);
    const refreshing = ref(false);
    const basePath = ref('');

    // Initialize component
    const init = () => {
      // Determine base path for API requests
      const path = window.location.pathname;
      basePath.value = path.includes('/casestrainer/') ? '/casestrainer' : '';
      
      // Load citation report script
      loadCitationReportScript();
    };

    // Load the citation report script
    const loadCitationReportScript = async () => {
      try {
        if (!window.citationReport) {
          // Use the correct path for the citation report script
          const scriptPath = `${basePath.value}/static/js/citation-report.js`;
          console.log(`Loading citation report script from: ${scriptPath}`);
          await loadScript(scriptPath);
          console.log('Citation report script loaded successfully');
        }
      } catch (error) {
        console.error('Failed to load citation report script:', error);
        throw error; // Re-throw to be caught by the caller
      }
    };

    // Display the citation report
    const displayCitationReport = (data) => {
      try {
        // Ensure the container exists and is empty
        let container = document.getElementById('citation-report-container');
        if (!container) {
          container = document.createElement('div');
          container.id = 'citation-report-container';
          const resultsContainer = document.querySelector('.citation-report');
          if (resultsContainer) {
            resultsContainer.appendChild(container);
          } else {
            console.error('Could not find results container');
            return;
          }
        } else {
          container.innerHTML = '';
        }
        
        // Check if we have the citation report functionality
        if (window.citationReport && window.citationReport.display) {
          // Check if we have results
          const hasCitations = data?.citations?.length > 0 || 
                             data?.validation_results?.length > 0;
          
          hasResults.value = hasCitations;
          
          if (hasCitations) {
            // Display the report
            window.citationReport.display(data);
          }
        } else {
          console.error('Citation report functionality not available');
        }
      } catch (error) {
        console.error('Error displaying citation report:', error);
      }
    };

    // Export citations to CSV
    const exportToCSV = () => {
      if (!props.citationData?.citations?.length) {
        console.error('No citation data available to export');
        return;
      }
      
      try {
        // Get the citations array
        const citations = props.citationData.citations;
        
        // Define CSV headers
        const headers = [
          'Citation', 
          'Case Name', 
          'Status', 
          'Validation Method', 
          'Context'
        ];
        
        // Prepare data rows
        const rows = citations.map(citation => ({
          'Citation': citation.citation_text || citation.citation || '',
          'Case Name': citation.case_name || citation.title || '',
          'Status': citation.verified ? 'Verified' : 'Not Verified',
          'Validation Method': citation.validation_method || citation.source || 'Unknown',
          'Context': citation.context ? citation.context.replace(/[\n\r]+/g, ' ').trim() : ''
        }));
        
        // Convert to CSV
        let csvContent = [
          headers.join(','),
          ...rows.map(row => 
            headers.map(header => 
              `"${String(row[header] || '').replace(/"/g, '""')}"`
            ).join(',')
          )
        ].join('\r\n');
        
        // Create download link
        const blob = new Blob(["\uFEFF" + csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.setAttribute('href', url);
        link.setAttribute('download', `citations_${new Date().toISOString().slice(0, 10)}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
      } catch (error) {
        console.error('Error exporting to CSV:', error);
      }
    };

    // Refresh the report
    const refresh = () => {
      refreshing.value = true;
      emit('refresh');
      // Reset refreshing state after a short delay
      setTimeout(() => {
        refreshing.value = false;
      }, 1000);
    };

    // Watch for changes to citation data
    watch(() => props.citationData, (newVal) => {
      if (newVal) {
        displayCitationReport(newVal);
      }
    }, { immediate: true, deep: true });

    // Initialize component when mounted
    onMounted(() => {
      init();
    });

    return {
      hasResults,
      refreshing,
      exportToCSV,
      refresh
    };
  }
};
</script>

<style scoped>
.citation-report {
  width: 100%;
}

/* Ensure the container takes full width */
#citation-report-container {
  width: 100%;
  overflow-x: auto;
}

/* Style for the export button */
.btn-export {
  transition: all 0.2s ease-in-out;
}

.btn-export:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* Print styles */
@media print {
  .no-print {
    display: none !important;
  }
  
  #citation-report-container {
    width: 100%;
    overflow: visible;
  }
}
</style>
