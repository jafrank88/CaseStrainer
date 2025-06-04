import { defineStore } from 'pinia';
import citationsApi from '@/api/citations';

export const useCitationsStore = defineStore('citations', {
  state: () => ({
    citations: [],
    currentCitation: null,
    loading: false,
    error: null,
    searchResults: [],
    citationNetwork: {},
    feedback: []
  }),
  
  actions: {
    /**
     * Validate a citation
     * @param {string} citation - The citation to validate
     */
    async validateCitation(citation) {
      this.loading = true;
      this.error = null;
      
      try {
        const response = await citationsApi.validateCitation(citation);
        this.currentCitation = response.data;
        return response.data;
      } catch (error) {
        this.error = error.response?.data?.message || 'Failed to validate citation';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    /**
     * Get citation metadata
     * @param {string} citation - The citation to get metadata for
     */
    async fetchCitationMetadata(citation) {
      this.loading = true;
      this.error = null;
      
      try {
        const response = await citationsApi.getCitationMetadata(citation);
        return response.data;
      } catch (error) {
        this.error = error.response?.data?.message || 'Failed to fetch citation metadata';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    /**
     * Get citation network
     * @param {string} citation - The citation to get network for
     * @param {number} depth - The depth of the network to retrieve
     */
    async fetchCitationNetwork(citation, depth = 1) {
      this.loading = true;
      this.error = null;
      
      try {
        const response = await citationsApi.getCitationNetwork(citation, depth);
        this.citationNetwork = response.data;
        return response.data;
      } catch (error) {
        this.error = error.response?.data?.message || 'Failed to fetch citation network';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    /**
     * Classify a citation
     * @param {string} citation - The citation to classify
     */
    async classifyCitation(citation) {
      this.loading = true;
      this.error = null;
      
      try {
        const response = await citationsApi.classifyCitation(citation);
        return response.data;
      } catch (error) {
        this.error = error.response?.data?.message || 'Failed to classify citation';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    /**
     * Get feedback for a citation
     * @param {string} citation - The citation to get feedback for
     */
    async fetchCitationFeedback(citation) {
      this.loading = true;
      this.error = null;
      
      try {
        const response = await citationsApi.getCitationFeedback(citation);
        this.feedback = response.data;
        return response.data;
      } catch (error) {
        this.error = error.response?.data?.message || 'Failed to fetch feedback';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    /**
     * Submit feedback for a citation
     * @param {Object} feedback - The feedback data
     */
    async submitFeedback(feedback) {
      this.loading = true;
      this.error = null;
      
      try {
        const response = await citationsApi.submitFeedback(feedback);
        // Refresh feedback after submission
        if (feedback.citation) {
          await this.fetchCitationFeedback(feedback.citation);
        }
        return response.data;
      } catch (error) {
        this.error = error.response?.data?.message || 'Failed to submit feedback';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    // Helper method to clear the current citation and related data
    clearCurrentCitation() {
      this.currentCitation = null;
      this.citationNetwork = {};
      this.feedback = [];
    }
  },
  
  getters: {
    // Get citation by ID
    getCitationById: (state) => (id) => {
      return state.citations.find(citation => citation.id === id);
    },
    
    // Get feedback for the current citation
    currentCitationFeedback: (state) => {
      if (!state.currentCitation) return [];
      return state.feedback;
    },
    
    // Get network for the current citation
    currentCitationNetwork: (state) => {
      if (!state.currentCitation) return {};
      return state.citationNetwork;
    }
  }
});
