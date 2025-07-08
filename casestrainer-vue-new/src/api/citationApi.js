/**
 * Comprehensive API client for CaseTrainer citation verification
 * Supports batch processing, webhooks, and third-party integrations
 */

import axios from 'axios';

// API Configuration
const API_BASE_URL = process.env.VUE_APP_API_BASE_URL || 'http://localhost:5000/api';
const API_VERSION = 'v1';

class CitationApi {
  constructor() {
    this.client = axios.create({
      baseURL: `${API_BASE_URL}/${API_VERSION}`,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      }
    });

    // Request interceptor for authentication
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response.data,
      (error) => {
        console.error('API Error:', error.response?.data || error.message);
        return Promise.reject(error);
      }
    );
  }

  // ===== CORE CITATION VERIFICATION =====

  /**
   * Verify a single citation
   */
  async verifyCitation(citation, options = {}) {
    const payload = {
      citation,
      options: {
        include_parallels: options.includeParallels ?? true,
        include_complex: options.includeComplex ?? true,
        include_web_search: options.includeWebSearch ?? true,
        include_courtlistener: options.includeCourtListener ?? true,
        include_local_db: options.includeLocalDB ?? true,
        ...options
      }
    };

    return this.client.post('/citations/verify', payload);
  }

  /**
   * Verify multiple citations in batch
   */
  async verifyCitationsBatch(citations, options = {}) {
    const payload = {
      citations,
      options: {
        parallel_processing: options.parallelProcessing ?? false,
        max_concurrent: options.maxConcurrent ?? 3,
        priority: options.priority ?? 'normal',
        ...options
      }
    };

    return this.client.post('/citations/verify/batch', payload);
  }

  /**
   * Extract and verify citations from document text
   */
  async processDocument(documentText, options = {}) {
    const payload = {
      document_text: documentText,
      options: {
        extract_citations: options.extractCitations ?? true,
        verify_citations: options.verifyCitations ?? true,
        include_positions: options.includePositions ?? true,
        include_context: options.includeContext ?? false,
        ...options
      }
    };

    return this.client.post('/documents/process', payload);
  }

  /**
   * Upload and process a document file
   */
  async uploadDocument(file, options = {}) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('options', JSON.stringify(options));

    return this.client.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 60000, // Longer timeout for file uploads
    });
  }

  // ===== BATCH PROCESSING =====

  /**
   * Start a batch processing job
   */
  async startBatchJob(files, options = {}) {
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));
    formData.append('options', JSON.stringify({
      processing_mode: options.processingMode ?? 'sequential',
      priority: options.priority ?? 'normal',
      email_notification: options.emailNotification ?? false,
      email_address: options.emailAddress,
      webhook_url: options.webhookUrl,
      ...options
    }));

    return this.client.post('/batch/start', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 60000,
    });
  }

  /**
   * Get batch job status
   */
  async getBatchJobStatus(jobId) {
    return this.client.get(`/batch/status/${jobId}`);
  }

  /**
   * Get batch job results
   */
  async getBatchJobResults(jobId) {
    return this.client.get(`/batch/results/${jobId}`);
  }

  /**
   * Cancel a batch job
   */
  async cancelBatchJob(jobId) {
    return this.client.post(`/batch/cancel/${jobId}`);
  }

  /**
   * List user's batch jobs
   */
  async listBatchJobs(filters = {}) {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        params.append(key, value);
      }
    });

    return this.client.get(`/batch/jobs?${params.toString()}`);
  }

  // ===== WEBHOOKS =====

  /**
   * Register a webhook for notifications
   */
  async registerWebhook(webhookConfig) {
    return this.client.post('/webhooks/register', webhookConfig);
  }

  /**
   * List registered webhooks
   */
  async listWebhooks() {
    return this.client.get('/webhooks');
  }

  /**
   * Update webhook configuration
   */
  async updateWebhook(webhookId, webhookConfig) {
    return this.client.put(`/webhooks/${webhookId}`, webhookConfig);
  }

  /**
   * Delete a webhook
   */
  async deleteWebhook(webhookId) {
    return this.client.delete(`/webhooks/${webhookId}`);
  }

  // ===== INTEGRATIONS =====

  /**
   * Zotero Integration - Export citations to Zotero
   */
  async exportToZotero(citations, zoteroConfig) {
    return this.client.post('/integrations/zotero/export', {
      citations,
      zotero_config: zoteroConfig
    });
  }

  /**
   * Mendeley Integration - Export citations to Mendeley
   */
  async exportToMendeley(citations, mendeleyConfig) {
    return this.client.post('/integrations/mendeley/export', {
      citations,
      mendeley_config: mendeleyConfig
    });
  }

  /**
   * EndNote Integration - Export citations to EndNote
   */
  async exportToEndNote(citations, endnoteConfig) {
    return this.client.post('/integrations/endnote/export', {
      citations,
      endnote_config: endnoteConfig
    });
  }

  /**
   * Microsoft Word Add-in - Get citation data for Word
   */
  async getWordCitationData(citation) {
    return this.client.post('/integrations/word/citation', { citation });
  }

  /**
   * Microsoft Word Add-in - Insert citation into Word document
   */
  async insertWordCitation(citation, documentId) {
    return this.client.post('/integrations/word/insert', {
      citation,
      document_id: documentId
    });
  }

  /**
   * Google Docs Integration - Insert citation into Google Doc
   */
  async insertGoogleDocsCitation(citation, documentId, accessToken) {
    return this.client.post('/integrations/googledocs/insert', {
      citation,
      document_id: documentId,
      access_token: accessToken
    });
  }

  // ===== LEGAL RESEARCH TOOL INTEGRATIONS =====

  /**
   * Westlaw Integration - Search for case in Westlaw
   */
  async searchWestlaw(query, westlawConfig) {
    return this.client.post('/integrations/westlaw/search', {
      query,
      westlaw_config: westlawConfig
    });
  }

  /**
   * LexisNexis Integration - Search for case in LexisNexis
   */
  async searchLexisNexis(query, lexisConfig) {
    return this.client.post('/integrations/lexis/search', {
      query,
      lexis_config: lexisConfig
    });
  }

  /**
   * Bloomberg Law Integration - Search for case in Bloomberg
   */
  async searchBloomberg(query, bloombergConfig) {
    return this.client.post('/integrations/bloomberg/search', {
      query,
      bloomberg_config: bloombergConfig
    });
  }

  /**
   * CourtListener Integration - Direct API access
   */
  async searchCourtListener(query, options = {}) {
    return this.client.post('/integrations/courtlistener/search', {
      query,
      options
    });
  }

  // ===== EXPORT FORMATS =====

  /**
   * Export results in various formats
   */
  async exportResults(results, format, options = {}) {
    const payload = {
      results,
      format,
      options: {
        include_verification_details: options.includeVerificationDetails ?? true,
        include_source_urls: options.includeSourceUrls ?? true,
        include_reliability_scores: options.includeReliabilityScores ?? true,
        include_document_context: options.includeDocumentContext ?? false,
        ...options
      }
    };

    return this.client.post('/export', payload, {
      responseType: 'blob'
    });
  }

  /**
   * Generate PDF report
   */
  async generatePDFReport(results, template = 'default') {
    return this.client.post('/export/pdf', {
      results,
      template
    }, {
      responseType: 'blob'
    });
  }

  /**
   * Generate BibTeX export
   */
  async generateBibTeX(citations) {
    return this.client.post('/export/bibtex', { citations });
  }

  /**
   * Generate RIS export
   */
  async generateRIS(citations) {
    return this.client.post('/export/ris', { citations });
  }

  // ===== USER PREFERENCES & SETTINGS =====

  /**
   * Get user preferences
   */
  async getUserPreferences() {
    return this.client.get('/user/preferences');
  }

  /**
   * Update user preferences
   */
  async updateUserPreferences(preferences) {
    return this.client.put('/user/preferences', preferences);
  }

  /**
   * Get API usage statistics
   */
  async getUsageStats(timeRange = '30d') {
    return this.client.get(`/user/usage?range=${timeRange}`);
  }

  /**
   * Get API rate limits
   */
  async getRateLimits() {
    return this.client.get('/user/rate-limits');
  }

  // ===== ADMIN & SYSTEM =====

  /**
   * Get system status
   */
  async getSystemStatus() {
    return this.client.get('/system/status');
  }

  /**
   * Get API version information
   */
  async getApiVersion() {
    return this.client.get('/system/version');
  }

  /**
   * Health check
   */
  async healthCheck() {
    return this.client.get('/health');
  }

  // ===== UTILITY METHODS =====

  /**
   * Download file from blob response
   */
  downloadFile(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  /**
   * Create a streaming connection for real-time updates
   */
  createStreamingConnection(jobId, onUpdate) {
    const eventSource = new EventSource(`${API_BASE_URL}/${API_VERSION}/batch/stream/${jobId}`);
    
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      onUpdate(data);
    };

    eventSource.onerror = (error) => {
      console.error('Streaming connection error:', error);
      eventSource.close();
    };

    return eventSource;
  }

  /**
   * Poll for updates (fallback for browsers without EventSource)
   */
  startPolling(jobId, onUpdate, interval = 2000) {
    const poll = async () => {
      try {
        const status = await this.getBatchJobStatus(jobId);
        onUpdate(status);
        
        if (status.status === 'completed' || status.status === 'failed') {
          return; // Stop polling
        }
        
        setTimeout(poll, interval);
      } catch (error) {
        console.error('Polling error:', error);
        setTimeout(poll, interval * 2); // Exponential backoff
      }
    };

    poll();
  }
}

// Create and export singleton instance
const citationApi = new CitationApi();
export default citationApi;

// Export individual methods for direct import
export const {
  verifyCitation,
  verifyCitationsBatch,
  processDocument,
  uploadDocument,
  startBatchJob,
  getBatchJobStatus,
  getBatchJobResults,
  cancelBatchJob,
  listBatchJobs,
  registerWebhook,
  listWebhooks,
  updateWebhook,
  deleteWebhook,
  exportToZotero,
  exportToMendeley,
  exportToEndNote,
  getWordCitationData,
  insertWordCitation,
  insertGoogleDocsCitation,
  searchWestlaw,
  searchLexisNexis,
  searchBloomberg,
  searchCourtListener,
  exportResults,
  generatePDFReport,
  generateBibTeX,
  generateRIS,
  getUserPreferences,
  updateUserPreferences,
  getUsageStats,
  getRateLimits,
  getSystemStatus,
  getApiVersion,
  healthCheck,
  downloadFile,
  createStreamingConnection,
  startPolling
} = citationApi; 