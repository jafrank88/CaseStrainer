import api from '@/api/citations'

export default {
  namespaced: true,
  state: {
    citations: [],
    filteredCitations: [],
    currentPage: 1,
    itemsPerPage: 10,
    totalItems: 0,
    filters: {
      verificationSource: null,
      confidence: null,
      searchTerm: ''
    },
    statistics: {
      total: 0,
      bySource: {}
    }
  },
  mutations: {
    SET_CITATIONS(state, citations) {
      state.citations = citations
      state.totalItems = citations.length
    },
    SET_FILTERED_CITATIONS(state, citations) {
      state.filteredCitations = citations
    },
    SET_CURRENT_PAGE(state, page) {
      state.currentPage = page
    },
    SET_FILTER(state, { type, value }) {
      state.filters[type] = value
    },
    SET_STATISTICS(state, statistics) {
      state.statistics = statistics
    }
  },
  actions: {
    async fetchCitations({ commit, dispatch }) {
      try {
        commit('SET_LOADING', true, { root: true })
        const response = await api.getMultitoolConfirmedCitations()
        commit('SET_CITATIONS', response.data.citations)
        dispatch('calculateStatistics')
        dispatch('applyFilters')
        commit('SET_LOADING', false, { root: true })
      } catch (error) {
        commit('SET_ERROR', error.message, { root: true })
        commit('SET_LOADING', false, { root: true })
      }
    },
    applyFilters({ commit, state }) {
      const { verificationSource, confidence, searchTerm } = state.filters
      
      let filtered = [...state.citations]
      
      if (verificationSource) {
        filtered = filtered.filter(citation => 
          citation.verification_source && 
          citation.verification_source.toLowerCase().includes(verificationSource.toLowerCase())
        )
      }
      
      if (confidence) {
        filtered = filtered.filter(citation => {
          const confidenceValue = citation.verification_confidence || 0
          if (confidence === 'high') return confidenceValue >= 0.9
          if (confidence === 'medium') return confidenceValue >= 0.8 && confidenceValue < 0.9
          if (confidence === 'low') return confidenceValue < 0.8
          return true
        })
      }
      
      if (searchTerm) {
        filtered = filtered.filter(citation => 
          (citation.citation_text && citation.citation_text.toLowerCase().includes(searchTerm.toLowerCase())) ||
          (citation.context && citation.context.toLowerCase().includes(searchTerm.toLowerCase()))
        )
      }
      
      commit('SET_FILTERED_CITATIONS', filtered)
    },
    calculateStatistics({ commit, state }) {
      // Count citations by verification source
      const bySource = {}
      state.citations.forEach(citation => {
        const source = citation.verification_source || 'Unknown'
        bySource[source] = (bySource[source] || 0) + 1
      })
      
      const statistics = {
        total: state.citations.length,
        bySource
      }
      
      commit('SET_STATISTICS', statistics)
    },
    setFilter({ commit, dispatch }, { type, value }) {
      commit('SET_FILTER', { type, value })
      dispatch('applyFilters')
    },
    setCurrentPage({ commit }, page) {
      commit('SET_CURRENT_PAGE', page)
    }
  },
  getters: {
    paginatedCitations: state => {
      const start = (state.currentPage - 1) * state.itemsPerPage
      const end = start + state.itemsPerPage
      return state.filteredCitations.slice(start, end)
    },
    totalPages: state => Math.ceil(state.filteredCitations.length / state.itemsPerPage),
    verificationSources: state => {
      const sources = new Set()
      state.citations.forEach(citation => {
        if (citation.verification_source) {
          sources.add(citation.verification_source)
        }
      })
      return Array.from(sources)
    }
  }
}
