import api from '@/api/citations'

export default {
  namespaced: true,
  state: {
    classificationResult: null,
    batchResults: [],
    modelInfo: {
      accuracy: 0.95,
      precision: 0.92,
      recall: 0.93,
      lastTrained: null,
      trainingDataSize: 650
    },
    citationInput: {
      text: '',
      caseName: ''
    }
  },
  mutations: {
    SET_CLASSIFICATION_RESULT(state, result) {
      state.classificationResult = result
    },
    SET_BATCH_RESULTS(state, results) {
      state.batchResults = results
    },
    SET_CITATION_INPUT(state, { text, caseName }) {
      state.citationInput.text = text
      state.citationInput.caseName = caseName || ''
    },
    UPDATE_MODEL_INFO(state, info) {
      state.modelInfo = { ...state.modelInfo, ...info }
    },
    CLEAR_CLASSIFICATION_RESULT(state) {
      state.classificationResult = null
    },
    CLEAR_BATCH_RESULTS(state) {
      state.batchResults = []
    }
  },
  actions: {
    async classifyCitation({ commit, state }) {
      try {
        commit('SET_LOADING', true, { root: true })
        const response = await api.classifyCitation(
          state.citationInput.text,
          state.citationInput.caseName || null
        )
        commit('SET_CLASSIFICATION_RESULT', response.data)
        commit('SET_LOADING', false, { root: true })
        return response.data
      } catch (error) {
        commit('SET_ERROR', error.message, { root: true })
        commit('SET_LOADING', false, { root: true })
        throw error
      }
    },
    async trainModel({ commit }) {
      try {
        commit('SET_LOADING', true, { root: true })
        const response = await api.trainMLClassifier()
        
        // Update model info with new training data
        commit('UPDATE_MODEL_INFO', { 
          lastTrained: new Date().toISOString(),
          ...response.data.model_info
        })
        
        commit('SET_LOADING', false, { root: true })
        return response.data
      } catch (error) {
        commit('SET_ERROR', error.message, { root: true })
        commit('SET_LOADING', false, { root: true })
        throw error
      }
    },
    async processBatch({ commit }, file) {
      try {
        commit('SET_LOADING', true, { root: true })
        
        // In a real implementation, you would:
        // 1. Create a FormData object
        // 2. Append the file
        // 3. Send to API for batch processing
        
        // For now, we'll simulate batch results
        setTimeout(() => {
          const batchResults = [
            { citation: '347 U.S. 483', case_name: 'Brown v. Board of Education', confidence: 0.98 },
            { citation: '410 U.S. 113', case_name: 'Roe v. Wade', confidence: 0.97 },
            { citation: '384 U.S. 436', case_name: 'Miranda v. Arizona', confidence: 0.95 },
            { citation: '123 F.4d 456', case_name: 'Smith v. Jones', confidence: 0.45 },
            { citation: '789 P.3d 123', case_name: 'Washington v. Oregon', confidence: 0.72 }
          ]
          
          commit('SET_BATCH_RESULTS', batchResults)
          commit('SET_LOADING', false, { root: true })
        }, 2000)
      } catch (error) {
        commit('SET_ERROR', error.message, { root: true })
        commit('SET_LOADING', false, { root: true })
        throw error
      }
    },
    setCitationInput({ commit }, { text, caseName }) {
      commit('SET_CITATION_INPUT', { text, caseName })
    },
    clearClassificationResult({ commit }) {
      commit('CLEAR_CLASSIFICATION_RESULT')
    },
    clearBatchResults({ commit }) {
      commit('CLEAR_BATCH_RESULTS')
    }
  },
  getters: {
    confidenceBadgeClass: state => {
      if (!state.classificationResult) return ''
      
      const confidence = state.classificationResult.confidence || 0
      if (confidence >= 0.9) return 'bg-success'
      if (confidence >= 0.7) return 'bg-warning text-dark'
      return 'bg-danger'
    },
    predictionText: state => {
      if (!state.classificationResult) return ''
      
      const confidence = state.classificationResult.confidence || 0
      if (confidence >= 0.9) return 'Likely Real Citation'
      if (confidence >= 0.7) return 'Possibly Real Citation'
      return 'Likely Hallucinated Citation'
    },
    batchResultsSummary: state => {
      const results = state.batchResults
      if (!results.length) return null
      
      const highConfidence = results.filter(r => r.confidence >= 0.9).length
      const mediumConfidence = results.filter(r => r.confidence >= 0.7 && r.confidence < 0.9).length
      const lowConfidence = results.filter(r => r.confidence < 0.7).length
      
      return {
        total: results.length,
        highConfidence,
        mediumConfidence,
        lowConfidence,
        avgConfidence: results.reduce((sum, r) => sum + r.confidence, 0) / results.length
      }
    }
  }
}
