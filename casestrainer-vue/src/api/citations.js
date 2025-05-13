import axios from 'axios';

const API_URL = process.env.NODE_ENV === 'production' 
  ? '/casestrainer/api' 
  : '/api';

export default {
  // Citation analysis endpoints
  analyzeBriefText(text, apiKey) {
    return axios.post(`${API_URL}/analyze`, { text, api_key: apiKey });
  },
  
  analyzeFile(formData) {
    return axios.post(`${API_URL}/analyze`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  },
  
  analyzeFilePath(filePath, apiKey) {
    return axios.post(`${API_URL}/analyze`, { file_path: filePath, api_key: apiKey });
  },
  
  getAnalysisStatus(analysisId) {
    return axios.get(`${API_URL}/status?analysis_id=${analysisId}`);
  },
  
  // Unconfirmed citations endpoints
  getUnconfirmedCitations(filters = {}) {
    return axios.post(`${API_URL}/unconfirmed_citations_data`, filters);
  },
  
  // Multitool confirmed citations endpoints
  getMultitoolConfirmedCitations() {
    return axios.get(`${API_URL}/confirmed_with_multitool_data`);
  },
  
  // Citation correction suggestions
  getCorrectionSuggestions(citation) {
    return axios.post(`${API_URL}/correction_suggestions`, { citation });
  },
  
  // Citation network data
  getCitationNetworkData(filter = 'all', depth = 1) {
    return axios.get(`${API_URL}/citation_network_data?filter=${filter}&depth=${depth}`);
  },
  
  // ML Classifier endpoints
  trainMLClassifier() {
    return axios.post(`${API_URL}/train_ml_classifier`);
  },
  
  classifyCitation(citation, caseName) {
    return axios.post(`${API_URL}/classify_citation`, { citation, case_name: caseName });
  },
  
  // Citation tester endpoints
  getTestCitations(count, includeConfirmed, includeUnconfirmed) {
    return axios.get(`${API_URL}/citation_tester_data`, {
      params: {
        count,
        include_confirmed: includeConfirmed,
        include_unconfirmed: includeUnconfirmed
      }
    });
  },
  
  // Citation export endpoints
  exportCitations(format, filters = {}) {
    return axios.post(`${API_URL}/export_citations`, { format, filters });
  },
  
  // Single citation verification
  verifyCitation(citation, caseName) {
    return axios.post(`${API_URL}/verify_citation`, { citation, case_name: caseName });
  }
};
