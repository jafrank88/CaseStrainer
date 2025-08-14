<template>
  <div class="export-results">
    <div class="export-header">
      <h4>Export Results</h4>
      <p class="text-muted">Download your citation verification results in various formats</p>
    </div>
    
    <div class="export-options">
      <!-- JSON Export -->
      <div class="export-option">
        <div class="option-header">
          <div class="option-icon">📄</div>
          <div class="option-info">
            <h5>JSON Export</h5>
            <p>Complete data with all verification details</p>
          </div>
        </div>
        <div class="option-actions">
          <button @click="exportJSON" class="btn btn-primary">
            Download JSON
          </button>
          <div class="file-info">
            <span class="size">{{ getFileSize('json') }}</span>
            <span class="format">.json</span>
          </div>
        </div>
      </div>
      
      <!-- CSV Export -->
      <div class="export-option">
        <div class="option-header">
          <div class="option-icon">📊</div>
          <div class="option-info">
            <h5>CSV Export</h5>
            <p>Spreadsheet-friendly format for analysis</p>
          </div>
        </div>
        <div class="option-actions">
          <button @click="exportCSV" class="btn btn-primary">
            Download CSV
          </button>
          <div class="file-info">
            <span class="size">{{ getFileSize('csv') }}</span>
            <span class="format">.csv</span>
          </div>
        </div>
      </div>
      
      <!-- PDF Report -->
      <div class="export-option">
        <div class="option-header">
          <div class="option-icon">📋</div>
          <div class="option-info">
            <h5>PDF Report</h5>
            <p>Formatted report with summary and details</p>
          </div>
        </div>
        <div class="option-actions">
          <button @click="exportPDF" class="btn btn-primary" :disabled="generatingPDF">
            {{ generatingPDF ? 'Generating...' : 'Download PDF' }}
          </button>
          <div class="file-info">
            <span class="size">{{ getFileSize('pdf') }}</span>
            <span class="format">.pdf</span>
          </div>
        </div>
      </div>
      
      <!-- Text Summary -->
      <div class="export-option">
        <div class="option-header">
          <div class="option-icon">📝</div>
          <div class="option-info">
            <h5>Text Summary</h5>
            <p>Plain text summary for easy sharing</p>
          </div>
        </div>
        <div class="option-actions">
          <button @click="exportText" class="btn btn-primary">
            Download Text
          </button>
          <div class="file-info">
            <span class="size">{{ getFileSize('txt') }}</span>
            <span class="format">.txt</span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Export Settings -->
    <div class="export-settings">
      <h5>Export Settings</h5>
      <div class="settings-grid">
        <div class="setting-group">
          <label>Include in Export:</label>
          <div class="checkbox-group">
            <label class="checkbox-item">
              <input type="checkbox" v-model="settings.includeVerificationDetails" />
              <span class="checkmark"></span>
              Verification Details
            </label>
            <label class="checkbox-item">
              <input type="checkbox" v-model="settings.includeSourceUrls" />
              <span class="checkmark"></span>
              Source URLs
            </label>
            <label class="checkbox-item">
              <input type="checkbox" v-model="settings.includeReliabilityScores" />
              <span class="checkmark"></span>
              Reliability Scores
            </label>
            <label class="checkbox-item">
              <input type="checkbox" v-model="settings.includeDocumentContext" />
              <span class="checkmark"></span>
              Document Context
            </label>
          </div>
        </div>
        
        <div class="setting-group">
          <label>Filter Results:</label>
          <div class="checkbox-group">
            <label class="checkbox-item">
              <input type="checkbox" v-model="settings.onlyVerified" />
              <span class="checkmark"></span>
              Only Verified Citations
            </label>
            <label class="checkbox-item">
              <input type="checkbox" v-model="settings.includeParallels" />
              <span class="checkmark"></span>
              Include Parallel Citations
            </label>
            <label class="checkbox-item">
              <input type="checkbox" v-model="settings.includeComplex" />
              <span class="checkmark"></span>
              Include Complex Citations
            </label>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Export History -->
    <div class="export-history" v-if="exportHistory.length > 0">
      <h5>Recent Exports</h5>
      <div class="history-list">
        <div v-for="exportItem in exportHistory.slice(0, 5)" :key="exportItem.id" class="history-item">
          <div class="history-info">
            <span class="format-badge">{{ exportItem.format.toUpperCase() }}</span>
            <span class="timestamp">{{ formatDate(exportItem.timestamp) }}</span>
          </div>
          <div class="history-actions">
            <button @click="downloadFromHistory(exportItem)" class="btn btn-sm btn-secondary">
              Download
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ExportResults',
  props: {
    citations: {
      type: Array,
      required: true
    },
    documentText: {
      type: String,
      default: ''
    },
    documentName: {
      type: String,
      default: 'Document'
    }
  },
  data() {
    return {
      generatingPDF: false,
      settings: {
        includeVerificationDetails: true,
        includeSourceUrls: true,
        includeReliabilityScores: true,
        includeDocumentContext: false,
        onlyVerified: false,
        includeParallels: true,
        includeComplex: true
      },
      exportHistory: []
    };
  },
  methods: {
    getFilteredCitations() {
      let filtered = [...this.citations];
      
      if (this.settings.onlyVerified) {
        filtered = filtered.filter(citation => 
          citation.courtlistener_verified || citation.web_verified || citation.local_verified
        );
      }
      
      if (!this.settings.includeParallels) {
        filtered = filtered.filter(citation => 
          !citation.parallel_citations || citation.parallel_citations.length === 0
        );
      }
      
      if (!this.settings.includeComplex) {
        filtered = filtered.filter(citation => !citation.is_complex);
      }
      
      return filtered;
    },
    
    getFileSize(format) {
      const citations = this.getFilteredCitations();
      const baseSize = citations.length * 500; // Rough estimate
      
      switch (format) {
        case 'json': return this.formatBytes(baseSize * 2);
        case 'csv': return this.formatBytes(baseSize * 0.5);
        case 'pdf': return this.formatBytes(baseSize * 3);
        case 'txt': return this.formatBytes(baseSize * 0.3);
        default: return 'Unknown';
      }
    },
    
    formatBytes(bytes) {
      if (bytes === 0) return '0 Bytes';
      const k = 1024;
      const sizes = ['Bytes', 'KB', 'MB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    },
    
    formatDate(dateString) {
      const date = new Date(dateString);
      return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    },
    
    addToHistory(format, data) {
      const exportRecord = {
        id: Date.now(),
        format,
        timestamp: new Date().toISOString(),
        data
      };
      
      this.exportHistory.unshift(exportRecord);
      if (this.exportHistory.length > 10) {
        this.exportHistory = this.exportHistory.slice(0, 10);
      }
      
      // Store in localStorage
      localStorage.setItem('citationExportHistory', JSON.stringify(this.exportHistory));
    },
    
    exportJSON() {
      const citations = this.getFilteredCitations();
      const exportData = {
        metadata: {
          exportDate: new Date().toISOString(),
          documentName: this.documentName,
          totalCitations: citations.length,
          settings: this.settings
        },
        citations: citations.map(citation => {
          const exportCitation = {
            citation: citation.citation,
            canonical_name: citation.canonical_name,
            extracted_case_name: citation.extracted_case_name,
            year: citation.year,
            canonical_date: citation.canonical_date,
            verified: citation.verified,
            start_index: citation.start_index,
            end_index: citation.end_index
          };
          
          if (this.settings.includeVerificationDetails) {
            exportCitation.verification = {
              courtlistener_verified: citation.courtlistener_verified,
              web_verified: citation.web_verified,
              local_verified: citation.local_verified,
              courtlistener_url: citation.courtlistener_url,
              web_sources: citation.web_sources
            };
          }
          
          if (this.settings.includeReliabilityScores) {
            exportCitation.reliability_score = this.getReliabilityScore(citation);
          }
          
          if (this.settings.includeParallels && citation.parallel_citations) {
            exportCitation.parallel_citations = citation.parallel_citations;
          }
          
          if (this.settings.includeDocumentContext && citation.start_index !== null) {
            const contextStart = Math.max(0, citation.start_index - 100);
            const contextEnd = Math.min(this.documentText.length, citation.end_index + 100);
            exportCitation.context = this.documentText.substring(contextStart, contextEnd);
          }
          
          return exportCitation;
        })
      };
      
      this.downloadFile(exportData, 'json', 'citation_results.json');
      this.addToHistory('json', exportData);
    },
    
    exportCSV() {
      const citations = this.getFilteredCitations();
      const headers = [
        'Citation',
        'Case Name',
        'Year',
        'Canonical Date',
        'Verified',
        'Position',
        'Reliability Score'
      ];
      
      if (this.settings.includeVerificationDetails) {
        headers.push('CourtListener Verified', 'Web Verified', 'Local Verified');
      }
      
      if (this.settings.includeSourceUrls) {
        headers.push('CourtListener URL', 'Web Sources');
      }
      
      const csvContent = [
        headers.join(','),
        ...citations.map(citation => {
          const row = [
            `"${citation.citation}"`,
            `"${citation.canonical_name || ''}"`,
            citation.year || '',
            citation.canonical_date || '',
            citation.verified ? 'Yes' : 'No',
            citation.start_index || '',
            this.getReliabilityScore(citation).toFixed(1)
          ];
          
          if (this.settings.includeVerificationDetails) {
            row.push(
              citation.courtlistener_verified ? 'Yes' : 'No',
              citation.web_verified ? 'Yes' : 'No',
              citation.local_verified ? 'Yes' : 'No'
            );
          }
          
          if (this.settings.includeSourceUrls) {
            row.push(
              `"${citation.courtlistener_url || ''}"`,
              `"${citation.web_sources ? citation.web_sources.map(s => s.url).join('; ') : ''}"`
            );
          }
          
          return row.join(',');
        })
      ].join('\n');
      
      this.downloadFile(csvContent, 'csv', 'citation_results.csv');
      this.addToHistory('csv', csvContent);
    },
    
    async exportPDF() {
      this.generatingPDF = true;
      
      try {
        // Simulate PDF generation
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        const citations = this.getFilteredCitations();
        const pdfContent = this.generatePDFContent(citations);
        
        // For now, we'll create a text file that simulates PDF content
        // In a real implementation, you'd use a PDF library like jsPDF
        this.downloadFile(pdfContent, 'txt', 'citation_report.txt');
        this.addToHistory('pdf', pdfContent);
        
      } catch (error) {
        console.error('PDF generation failed:', error);
        console.error('PDF generation failed. Please try again.');
      } finally {
        this.generatingPDF = false;
      }
    },
    
    generatePDFContent(citations) {
      const verifiedCount = citations.filter(c => c.verified).length;
      const totalCount = citations.length;
      
      let content = `CITATION VERIFICATION REPORT\n`;
      content += `Generated: ${new Date().toLocaleString()}\n`;
      content += `Document: ${this.documentName}\n`;
      content += `Total Citations: ${totalCount}\n`;
      content += `Verified Citations: ${verifiedCount}\n`;
      content += `Verification Rate: ${((verifiedCount / totalCount) * 100).toFixed(1)}%\n\n`;
      
      content += `DETAILED RESULTS:\n`;
      content += `================\n\n`;
      
      citations.forEach((citation, index) => {
        content += `${index + 1}. ${citation.citation}\n`;
        content += `   Case Name: ${citation.canonical_name || 'N/A'}\n`;
        content += `   Date: ${citation.canonical_date || citation.year || 'N/A'}\n`;
        content += `   Status: ${citation.verified ? 'Verified' : 'Not Verified'}\n`;
        content += `   Reliability: ${this.getReliabilityScore(citation).toFixed(1)}%\n`;
        
        if (this.settings.includeVerificationDetails) {
          content += `   Sources: `;
          const sources = [];
          if (citation.courtlistener_verified) sources.push('CourtListener');
          if (citation.web_verified) sources.push('Web Search');
          if (citation.local_verified) sources.push('Local DB');
          content += sources.length > 0 ? sources.join(', ') : 'None';
          content += '\n';
        }
        
        content += '\n';
      });
      
      return content;
    },
    
    exportText() {
      const citations = this.getFilteredCitations();
      const textContent = this.generatePDFContent(citations);
      
      this.downloadFile(textContent, 'txt', 'citation_summary.txt');
      this.addToHistory('txt', textContent);
    },
    
    downloadFile(content, type, filename) {
      let blob;
      
      if (type === 'json') {
        blob = new Blob([JSON.stringify(content, null, 2)], { type: 'application/json' });
      } else if (type === 'csv') {
        blob = new Blob([content], { type: 'text/csv' });
      } else {
        blob = new Blob([content], { type: 'text/plain' });
      }
      
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    },
    
    downloadFromHistory(exportRecord) {
      this.downloadFile(exportRecord.data, exportRecord.format, `citation_results_${exportRecord.id}.${exportRecord.format}`);
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
    }
  },
  
  mounted() {
    // Load export history from localStorage
    const savedHistory = localStorage.getItem('citationExportHistory');
    if (savedHistory) {
      try {
        this.exportHistory = JSON.parse(savedHistory);
      } catch (error) {
        console.error('Failed to load export history:', error);
      }
    }
  }
};
</script>

<style scoped>
.export-results {
  background: #fff;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  margin-bottom: 2rem;
}

.export-header {
  margin-bottom: 1.5rem;
  border-bottom: 1px solid #e0e0e0;
  padding-bottom: 1rem;
}

.export-header h4 {
  margin: 0 0 0.5rem 0;
  color: #333;
}

.export-options {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.export-option {
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  padding: 1rem;
  background: #fafafa;
  transition: all 0.2s;
}

.export-option:hover {
  border-color: #1976d2;
  box-shadow: 0 2px 8px rgba(25, 118, 210, 0.1);
}

.option-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.option-icon {
  font-size: 1.5rem;
}

.option-info h5 {
  margin: 0 0 0.25rem 0;
  color: #333;
}

.option-info p {
  margin: 0;
  font-size: 0.85rem;
  color: #666;
}

.option-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.file-info {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  font-size: 0.8rem;
  color: #666;
}

.file-info .size {
  font-weight: 500;
}

.file-info .format {
  color: #999;
}

.export-settings {
  border-top: 1px solid #e0e0e0;
  padding-top: 1.5rem;
  margin-bottom: 1.5rem;
}

.export-settings h5 {
  margin: 0 0 1rem 0;
  color: #333;
}

.settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

.setting-group {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.setting-group label {
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

.export-history {
  border-top: 1px solid #e0e0e0;
  padding-top: 1.5rem;
}

.export-history h5 {
  margin: 0 0 1rem 0;
  color: #333;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 4px;
  font-size: 0.9rem;
}

.history-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.format-badge {
  background: #1976d2;
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 3px;
  font-size: 0.8rem;
  font-weight: 500;
}

.timestamp {
  color: #666;
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

.btn-primary:hover:not(:disabled) {
  background: #1565c0;
}

.btn-primary:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.btn-secondary {
  background: #f5f5f5;
  color: #333;
  border: 1px solid #ddd;
}

.btn-secondary:hover {
  background: #e0e0e0;
}

.btn-sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.8rem;
}
</style> 