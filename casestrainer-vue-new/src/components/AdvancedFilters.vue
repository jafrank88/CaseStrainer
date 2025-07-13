<template>
  <div class="advanced-filters">
    <div class="filters-header">
      <h4>Advanced Filters & Sorting</h4>
      <button @click="toggleFilters" class="toggle-btn">
        {{ showFilters ? 'Hide' : 'Show' }} Filters
      </button>
    </div>
    
    <div v-if="showFilters" class="filters-content">
      <!-- Search/Filter Bar -->
      <div class="search-section">
        <div class="search-input">
          <input 
            v-model="filters.searchTerm" 
            type="text" 
            placeholder="Search citations, case names, or dates..."
            class="search-field"
          />
          <button @click="clearSearch" class="clear-btn" v-if="filters.searchTerm">
            ✕
          </button>
        </div>
      </div>
      
      <!-- Filter Options -->
      <div class="filter-options">
        <!-- Verification Status Filter -->
        <div class="filter-group">
          <label>Verification Status:</label>
          <div class="checkbox-group">
            <label class="checkbox-item">
              <input 
                type="checkbox" 
                v-model="filters.status.verified"
                @change="applyFilters"
              />
              <span class="checkmark verified"></span>
              Verified
            </label>
            <label class="checkbox-item">
              <input 
                type="checkbox" 
                v-model="filters.status.partial"
                @change="applyFilters"
              />
              <span class="checkmark partial"></span>
              Partially Verified
            </label>
            <label class="checkbox-item">
              <input 
                type="checkbox" 
                v-model="filters.status.unverified"
                @change="applyFilters"
              />
              <span class="checkmark unverified"></span>
              Not Verified
            </label>
          </div>
        </div>
        
        <!-- Date Range Filter -->
        <div class="filter-group">
          <label>Date Range:</label>
          <div class="date-range">
            <div class="date-input">
              <label>From:</label>
              <input 
                type="date" 
                v-model="filters.dateRange.start"
                @change="applyFilters"
                class="date-field"
              />
            </div>
            <div class="date-input">
              <label>To:</label>
              <input 
                type="date" 
                v-model="filters.dateRange.end"
                @change="applyFilters"
                class="date-field"
              />
            </div>
          </div>
        </div>
        
        <!-- Source Filter -->
        <div class="filter-group">
          <label>Verification Sources:</label>
          <div class="checkbox-group">
            <label class="checkbox-item">
              <input 
                type="checkbox" 
                v-model="filters.sources.courtlistener"
                @change="applyFilters"
              />
              <span class="checkmark"></span>
              CourtListener
            </label>
            <label class="checkbox-item">
              <input 
                type="checkbox" 
                v-model="filters.sources.web"
                @change="applyFilters"
              />
              <span class="checkmark"></span>
              Web Search
            </label>
            <label class="checkbox-item">
              <input 
                type="checkbox" 
                v-model="filters.sources.local"
                @change="applyFilters"
              />
              <span class="checkmark"></span>
              Local Database
            </label>
          </div>
        </div>
        
        <!-- Citation Type Filter -->
        <div class="filter-group">
          <label>Citation Type:</label>
          <div class="checkbox-group">
            <label class="checkbox-item">
              <input 
                type="checkbox" 
                v-model="filters.types.complex"
                @change="applyFilters"
              />
              <span class="checkmark"></span>
              Complex Citations
            </label>
            <label class="checkbox-item">
              <input 
                type="checkbox" 
                v-model="filters.types.simple"
                @change="applyFilters"
              />
              <span class="checkmark"></span>
              Simple Citations
            </label>
            <label class="checkbox-item">
              <input 
                type="checkbox" 
                v-model="filters.types.parallel"
                @change="applyFilters"
              />
              <span class="checkmark"></span>
              Parallel Citations
            </label>
          </div>
        </div>
      </div>
      
      <!-- Sorting Options -->
      <div class="sorting-section">
        <label>Sort By:</label>
        <div class="sort-options">
          <select v-model="filters.sortBy" @change="applyFilters" class="sort-select">
            <option value="position">Document Position</option>
            <option value="citation">Citation Text</option>
            <option value="canonical_name">Canonical Case Name</option>
            <option value="extracted_case_name">Extracted Case Name</option>
            <option value="date">Date</option>
            <option value="verification_status">Verification Status</option>
            <option value="reliability">Reliability Score</option>
          </select>
          <button @click="toggleSortOrder" class="sort-order-btn">
            {{ filters.sortOrder === 'asc' ? '↑' : '↓' }}
          </button>
        </div>
      </div>
      
      <!-- Filter Actions -->
      <div class="filter-actions">
        <button @click="clearAllFilters" class="btn btn-secondary">
          Clear All Filters
        </button>
        <button @click="exportFilteredResults" class="btn btn-primary">
          Export Filtered Results
        </button>
      </div>
    </div>
    
    <!-- Results Summary -->
    <div class="results-summary">
      <span class="results-count">
        Showing {{ filteredCitations.length }} of {{ totalCitations }} citations
      </span>
      <span v-if="hasActiveFilters" class="active-filters">
        ({{ getActiveFilterCount() }} filters active)
      </span>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AdvancedFilters',
  props: {
    citations: {
      type: Array,
      required: true
    }
  },
  data() {
    return {
      showFilters: false,
      filters: {
        searchTerm: '',
        status: {
          verified: true,
          partial: true,
          unverified: true
        },
        dateRange: {
          start: '',
          end: ''
        },
        sources: {
          courtlistener: true,
          web: true,
          local: true
        },
        types: {
          complex: true,
          simple: true,
          parallel: true
        },
        sortBy: 'position',
        sortOrder: 'asc'
      }
    };
  },
  computed: {
    filteredCitations() {
      let filtered = [...this.citations];
      
      // Search filter
      if (this.filters.searchTerm) {
        const search = this.filters.searchTerm.toLowerCase();
        filtered = filtered.filter(citation => 
          citation.citation.toLowerCase().includes(search) ||
          (citation.canonical_name && citation.canonical_name.toLowerCase().includes(search)) ||
          (citation.canonical_date && citation.canonical_date.includes(search)) ||
          (citation.year && citation.year.toString().includes(search))
        );
      }
      
      // Status filter
      const activeStatuses = Object.entries(this.filters.status)
        .filter(([key, value]) => value)
        .map(([key]) => key);
      
      if (activeStatuses.length < 3) {
        filtered = filtered.filter(citation => {
          const status = this.getVerificationStatus(citation);
          return activeStatuses.includes(status);
        });
      }
      
      // Date range filter
      if (this.filters.dateRange.start || this.filters.dateRange.end) {
        filtered = filtered.filter(citation => {
          const date = citation.canonical_date || citation.year;
          if (!date) return false;
          
          const citationDate = new Date(date);
          const startDate = this.filters.dateRange.start ? new Date(this.filters.dateRange.start) : null;
          const endDate = this.filters.dateRange.end ? new Date(this.filters.dateRange.end) : null;
          
          if (startDate && citationDate < startDate) return false;
          if (endDate && citationDate > endDate) return false;
          
          return true;
        });
      }
      
      // Source filter
      const activeSources = Object.entries(this.filters.sources)
        .filter(([key, value]) => value)
        .map(([key]) => key);
      
      if (activeSources.length < 3) {
        filtered = filtered.filter(citation => {
          return activeSources.some(source => {
            switch (source) {
              case 'courtlistener': return citation.courtlistener_verified;
              case 'web': return citation.web_verified;
              case 'local': return citation.local_verified;
              default: return false;
            }
          });
        });
      }
      
      // Type filter
      const activeTypes = Object.entries(this.filters.types)
        .filter(([key, value]) => value)
        .map(([key]) => key);
      
      if (activeTypes.length < 3) {
        filtered = filtered.filter(citation => {
          if (activeTypes.includes('complex') && citation.is_complex) return true;
          if (activeTypes.includes('simple') && !citation.is_complex) return true;
          if (activeTypes.includes('parallel') && citation.parallel_citations && citation.parallel_citations.length > 0) return true;
          return false;
        });
      }
      
      // Sorting
      filtered.sort((a, b) => {
        let aValue, bValue;
        
        switch (this.filters.sortBy) {
          case 'position':
            aValue = a.start_index || 0;
            bValue = b.start_index || 0;
            break;
          case 'citation':
            aValue = a.citation.toLowerCase();
            bValue = b.citation.toLowerCase();
            break;
          case 'canonical_name':
            aValue = (a.canonical_name || '').toLowerCase();
            bValue = (b.canonical_name || '').toLowerCase();
            break;
          case 'extracted_case_name':
            aValue = (a.extracted_case_name || '').toLowerCase();
            bValue = (b.extracted_case_name || '').toLowerCase();
            break;
          case 'date':
            aValue = new Date(a.canonical_date || a.year || '1900');
            bValue = new Date(b.canonical_date || b.year || '1900');
            break;
          case 'verification_status':
            aValue = this.getVerificationStatusPriority(a);
            bValue = this.getVerificationStatusPriority(b);
            break;
          case 'reliability':
            aValue = this.getReliabilityScore(a);
            bValue = this.getReliabilityScore(b);
            break;
          default:
            return 0;
        }
        
        if (aValue < bValue) return this.filters.sortOrder === 'asc' ? -1 : 1;
        if (aValue > bValue) return this.filters.sortOrder === 'asc' ? 1 : -1;
        return 0;
      });
      
      return filtered;
    },
    
    totalCitations() {
      return this.citations.length;
    },
    
    hasActiveFilters() {
      return this.filters.searchTerm ||
             !this.filters.status.verified || !this.filters.status.partial || !this.filters.status.unverified ||
             this.filters.dateRange.start || this.filters.dateRange.end ||
             !this.filters.sources.courtlistener || !this.filters.sources.web || !this.filters.sources.local ||
             !this.filters.types.complex || !this.filters.types.simple || !this.filters.types.parallel;
    }
  },
  watch: {
    filteredCitations: {
      handler(newFiltered) {
        this.$emit('filtered-results', newFiltered);
      },
      immediate: true
    }
  },
  methods: {
    toggleFilters() {
      this.showFilters = !this.showFilters;
    },
    
    clearSearch() {
      this.filters.searchTerm = '';
      this.applyFilters();
    },
    
    clearAllFilters() {
      this.filters = {
        searchTerm: '',
        status: { verified: true, partial: true, unverified: true },
        dateRange: { start: '', end: '' },
        sources: { courtlistener: true, web: true, local: true },
        types: { complex: true, simple: true, parallel: true },
        sortBy: 'position',
        sortOrder: 'asc'
      };
      this.applyFilters();
    },
    
    toggleSortOrder() {
      this.filters.sortOrder = this.filters.sortOrder === 'asc' ? 'desc' : 'asc';
      this.applyFilters();
    },
    
    applyFilters() {
      // This will trigger the computed property and emit the filtered results
    },
    
    getVerificationStatus(citation) {
      if (citation.courtlistener_verified) return 'verified';
      if (citation.web_verified || citation.local_verified) return 'partial';
      return 'unverified';
    },
    
    getVerificationStatusPriority(citation) {
      const status = this.getVerificationStatus(citation);
      switch (status) {
        case 'verified': return 3;
        case 'partial': return 2;
        case 'unverified': return 1;
        default: return 0;
      }
    },
    
    getReliabilityScore(citation) {
      let total = 0;
      let count = 0;
      
      if (citation.courtlistener_verified) {
        total += 95;
        count++;
      }
      if (citation.web_verified) {
        total += 85;
        count++;
      }
      if (citation.local_verified) {
        total += 90;
        count++;
      }
      
      return count > 0 ? total / count : 0;
    },
    
    getActiveFilterCount() {
      let count = 0;
      if (this.filters.searchTerm) count++;
      if (!this.filters.status.verified || !this.filters.status.partial || !this.filters.status.unverified) count++;
      if (this.filters.dateRange.start || this.filters.dateRange.end) count++;
      if (!this.filters.sources.courtlistener || !this.filters.sources.web || !this.filters.sources.local) count++;
      if (!this.filters.types.complex || !this.filters.types.simple || !this.filters.types.parallel) count++;
      return count;
    },
    
    exportFilteredResults() {
      const exportData = {
        timestamp: new Date().toISOString(),
        filters: this.filters,
        results: this.filteredCitations
      };
      
      const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `citation_results_${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }
  }
};
</script>

<style scoped>
.advanced-filters {
  background: #fff;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  margin-bottom: 2rem;
}

.filters-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.filters-header h4 {
  margin: 0;
  color: #333;
}

.toggle-btn {
  background: #f5f5f5;
  border: 1px solid #ddd;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
}

.toggle-btn:hover {
  background: #e0e0e0;
}

.filters-content {
  border-top: 1px solid #e0e0e0;
  padding-top: 1rem;
}

.search-section {
  margin-bottom: 1.5rem;
}

.search-input {
  position: relative;
  display: flex;
  align-items: center;
}

.search-field {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 1rem;
}

.search-field:focus {
  outline: none;
  border-color: #1976d2;
  box-shadow: 0 0 0 2px rgba(25, 118, 210, 0.2);
}

.clear-btn {
  position: absolute;
  right: 0.75rem;
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  color: #666;
}

.clear-btn:hover {
  color: #333;
}

.filter-options {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.filter-group label {
  font-weight: 500;
  color: #555;
  font-size: 0.9rem;
}

.checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.checkbox-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  font-size: 0.9rem;
}

.checkbox-item input[type="checkbox"] {
  display: none;
}

.checkmark {
  width: 16px;
  height: 16px;
  border: 2px solid #ddd;
  border-radius: 3px;
  position: relative;
  transition: all 0.2s;
}

.checkbox-item input[type="checkbox"]:checked + .checkmark {
  background: #1976d2;
  border-color: #1976d2;
}

.checkbox-item input[type="checkbox"]:checked + .checkmark::after {
  content: '✓';
  position: absolute;
  top: -2px;
  left: 1px;
  color: white;
  font-size: 12px;
}

.checkmark.verified {
  border-color: #28a745;
}

.checkbox-item input[type="checkbox"]:checked + .checkmark.verified {
  background: #28a745;
  border-color: #28a745;
}

.checkmark.partial {
  border-color: #ffc107;
}

.checkbox-item input[type="checkbox"]:checked + .checkmark.partial {
  background: #ffc107;
  border-color: #ffc107;
}

.checkmark.unverified {
  border-color: #dc3545;
}

.checkbox-item input[type="checkbox"]:checked + .checkmark.unverified {
  background: #dc3545;
  border-color: #dc3545;
}

.date-range {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.date-input {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.date-input label {
  font-size: 0.8rem;
  color: #666;
}

.date-field {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
}

.date-field:focus {
  outline: none;
  border-color: #1976d2;
  box-shadow: 0 0 0 2px rgba(25, 118, 210, 0.2);
}

.sorting-section {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 6px;
}

.sorting-section label {
  font-weight: 500;
  color: #555;
  white-space: nowrap;
}

.sort-options {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.sort-select {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
  min-width: 200px;
}

.sort-select:focus {
  outline: none;
  border-color: #1976d2;
  box-shadow: 0 0 0 2px rgba(25, 118, 210, 0.2);
}

.sort-order-btn {
  padding: 0.5rem 0.75rem;
  border: 1px solid #ddd;
  background: #fff;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
}

.sort-order-btn:hover {
  background: #f5f5f5;
}

.filter-actions {
  display: flex;
  gap: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e0e0e0;
}

.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-primary {
  background: #1976d2;
  color: white;
}

.btn-primary:hover {
  background: #1565c0;
}

.btn-secondary {
  background: #f5f5f5;
  color: #333;
  border: 1px solid #ddd;
}

.btn-secondary:hover {
  background: #e0e0e0;
}

.results-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e0e0e0;
  font-size: 0.9rem;
  color: #666;
}

.active-filters {
  color: #1976d2;
  font-weight: 500;
}

/* Mobile Responsive Design */
@media (max-width: 768px) {
  .advanced-filters {
    padding: 0 1rem;
  }
  
  .filters-header {
    flex-direction: column;
    align-items: stretch;
    gap: 0.75rem;
  }
  
  .toggle-btn {
    width: 100%;
    padding: 0.75rem;
    font-size: 1rem;
  }
  
  .filters-content {
    padding: 1rem;
  }
  
  .search-section {
    margin-bottom: 1.5rem;
  }
  
  .search-input {
    position: relative;
  }
  
  .search-field {
    font-size: 16px; /* Prevent zoom on mobile */
    padding: 0.75rem 2.5rem 0.75rem 1rem;
  }
  
  .clear-btn {
    right: 0.75rem;
    top: 50%;
    transform: translateY(-50%);
  }
  
  .filter-options {
    gap: 1.5rem;
  }
  
  .filter-group {
    gap: 0.75rem;
  }
  
  .filter-group label {
    font-size: 0.95rem;
  }
  
  .checkbox-group {
    gap: 0.75rem;
  }
  
  .checkbox-item {
    font-size: 0.9rem;
    padding: 0.5rem 0;
  }
  
  .checkmark {
    width: 18px;
    height: 18px;
    flex-shrink: 0;
  }
  
  /* Date range - stack vertically on mobile */
  .date-range {
    grid-template-columns: 1fr;
    gap: 0.75rem;
  }
  
  .date-input {
    gap: 0.5rem;
  }
  
  .date-field {
    font-size: 16px; /* Prevent zoom on mobile */
    padding: 0.75rem;
  }
  
  /* Sorting section - stack vertically */
  .sorting-section {
    flex-direction: column;
    align-items: stretch;
    gap: 0.75rem;
  }
  
  .sorting-section label {
    white-space: normal;
    font-size: 0.95rem;
  }
  
  .sort-options {
    flex-direction: column;
    align-items: stretch;
    gap: 0.5rem;
  }
  
  .sort-select {
    width: 100%;
    min-width: auto;
    font-size: 16px; /* Prevent zoom on mobile */
    padding: 0.75rem;
  }
  
  .sort-order-btn {
    width: 100%;
    padding: 0.75rem;
    font-size: 1.1rem;
  }
  
  /* Filter actions - stack vertically */
  .filter-actions {
    flex-direction: column;
    gap: 0.75rem;
  }
  
  .btn {
    width: 100%;
    padding: 0.75rem 1rem;
    font-size: 1rem;
    min-height: 44px;
  }
  
  /* Results summary - stack vertically */
  .results-summary {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .results-count,
  .active-filters {
    font-size: 0.85rem;
  }
}

@media (max-width: 480px) {
  .advanced-filters {
    padding: 0 0.5rem;
  }
  
  .filters-content {
    padding: 0.75rem;
  }
  
  .search-field {
    padding: 0.5rem 2rem 0.5rem 0.75rem;
    font-size: 16px;
  }
  
  .clear-btn {
    right: 0.5rem;
    padding: 0.25rem 0.5rem;
  }
  
  .filter-group {
    gap: 0.5rem;
  }
  
  .filter-group label {
    font-size: 0.9rem;
  }
  
  .checkbox-item {
    font-size: 0.85rem;
    padding: 0.375rem 0;
  }
  
  .checkmark {
    width: 16px;
    height: 16px;
  }
  
  .date-field {
    padding: 0.5rem;
    font-size: 16px;
  }
  
  .sort-select {
    padding: 0.5rem;
    font-size: 16px;
  }
  
  .sort-order-btn {
    padding: 0.5rem;
    font-size: 1rem;
  }
  
  .btn {
    padding: 0.5rem 0.75rem;
    font-size: 0.9rem;
  }
}

/* Touch-friendly improvements */
@media (hover: none) and (pointer: coarse) {
  .toggle-btn,
  .btn,
  .checkbox-item,
  .sort-order-btn {
    min-height: 44px;
  }
  
  .checkmark {
    min-width: 20px;
    min-height: 20px;
  }
  
  /* Remove hover effects on touch devices */
  .btn:hover,
  .sort-order-btn:hover {
    transform: none;
  }
}
</style> 