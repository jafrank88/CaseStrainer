import api from './api';

const citationsApi = {
  /**
   * Validate a citation
   * @param {string} citation - The citation to validate
   * @returns {Promise} - API response
   */
  validateCitation(citation) {
    // Send single citations through the paste text pipeline for consistency
    return api.post('/analyze', { 
      text: citation,
      type: 'text'
    });
  },

  /**
   * Poll for task results
   * @param {string} taskId - The task ID to poll for
   * @returns {Promise} - API response
   */
  pollTaskResults(taskId) {
    return api.get(`/casestrainer/api/analyze/progress/${taskId}`);
  },

  /**
   * Get citation metadata
   * @param {string} citation - The citation to get metadata for
   * @returns {Promise} - API response
   */
  getCitationMetadata(citation) {
    return api.get(`/metadata?citation=${encodeURIComponent(citation)}`);
  },

  /**
   * Get citation network
   * @param {string} citation - The citation to get network for
   * @param {number} depth - The depth of the network to retrieve
   * @returns {Promise} - API response
   */
  getCitationNetwork(citation, depth = 1) {
    return api.get(`/network?citation=${encodeURIComponent(citation)}&depth=${depth}`);
  },

  /**
   * Classify a citation
   * @param {string} citation - The citation to classify
   * @returns {Promise} - API response
   */
  classifyCitation(citation) {
    return api.post('/classify', { citation });
  },

  /**
   * Get citation feedback
   * @param {string} citation - The citation to get feedback for
   * @returns {Promise} - API response
   */
  getCitationFeedback(citation) {
    return api.get(`/feedback?citation=${encodeURIComponent(citation)}`);
  },

  /**
   * Submit feedback for a citation
   * @param {Object} feedback - The feedback data
   * @param {string} feedback.citation - The citation the feedback is for
   * @param {string} feedback.feedback - The feedback text
   * @param {string} feedback.rating - The rating (e.g., 'positive', 'negative')
   * @returns {Promise} - API response
   */
  submitFeedback(feedback) {
    return api.post('/feedback', feedback);
  },
};

export default citationsApi;
