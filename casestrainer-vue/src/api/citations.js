import api from '../services/api';

export default {
  // Citation analysis endpoints
  analyzeBriefText(text, apiKey) {
    return api.post(`/analyze`, { text, api_key: apiKey });
  },
  
  analyzeFile(formData) {
    return api.post(`/analyze`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  },
  
  analyzeFilePath(filePath, apiKey) {
    return api.post(`/analyze`, { file_path: filePath, api_key: apiKey });
  },
  
  getAnalysisStatus(analysisId) {
    return api.get(`/status?analysis_id=${analysisId}`);
  },
  
  // Unconfirmed citations endpoints
  getUnconfirmedCitations(filters = {}) {
    return api.post(`/unconfirmed_citations_data`, filters);
  },
  
  // Multitool confirmed citations endpoints
  getMultitoolConfirmedCitations() {
    return api.get(`/confirmed_with_multitool_data`);
  },
  
  // Citation correction suggestions
  getCorrectionSuggestions(citation) {
    return api.post(`/correction_suggestions`, { citation });
  },
  
  // Citation network data
  getCitationNetworkData(filter = 'all', depth = 1) {
    return api.get(`/citation_network_data?filter=${filter}&depth=${depth}`);
  },
  
  // ML Classifier endpoints
  trainMLClassifier() {
    return api.post(`/train_ml_classifier`);
  },
  
  classifyCitation(citation, caseName) {
    return api.post(`/classify_citation`, { citation, case_name: caseName });
  },
  
  // Citation tester endpoints
  getTestCitations(count, includeConfirmed, includeUnconfirmed) {
    return api.get(
      `/test_citations?count=${count}&include_confirmed=${includeConfirmed}&include_unconfirmed=${includeUnconfirmed}`
    );
  },
  
  // Citation export endpoints
  exportCitations(format, filters = {}) {
    return api.post(
      `/export_citations?format=${format}`,
      { filters },
      { responseType: 'blob' }
    );
  },
  
  // Single citation verification
  verifyCitation(citation, caseName) {
    return api.post(`/casestrainer/api/verify-citation`, { 
      citation: citation,
      case_name: caseName || ''
    });
  }
};
