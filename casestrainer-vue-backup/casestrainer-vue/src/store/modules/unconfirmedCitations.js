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
      confidence: null,
      source: null,
      searchTerm: ''
    },
    statistics: {
      total: 0,
      highConfidence: 0,
      mediumConfidence: 0,
      lowConfidence: 0
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
        const response = await api.getUnconfirmedCitations()
        commit('SET_CITATIONS', response.data)
        dispatch('calculateStatistics')
        dispatch('applyFilters')
        commit('SET_LOADING', false, { root: true })
      } catch (error) {
        commit('SET_ERROR', error.message, { root: true })
        commit('SET_LOADING', false, { root: true })
      }
    },
    applyFilters({ commit, state }) {
      const { confidence, source, searchTerm } = state.filters
      
      let filtered = [...state.citations]
      
      if (confidence) {
        filtered = filtered.filter(citation => {
          if (confidence === 'high') return citation.confidence >= 0.7
          if (confidence === 'medium') return citation.confidence >= 0.4 && citation.confidence < 0.7
          if (confidence === 'low') return citation.confidence < 0.4
          return true
        })
      }
      
      if (source) {
        filtered = filtered.filter(citation => 
          citation.source && citation.source.toLowerCase().includes(source.toLowerCase())
        )
      }
      
      if (searchTerm) {
        filtered = filtered.filter(citation => 
          (citation.citation_text && citation.citation_text.toLowerCase().includes(searchTerm.toLowerCase())) ||
          (citation.case_name && citation.case_name.toLowerCase().includes(searchTerm.toLowerCase()))
        )
      }
      
      commit('SET_FILTERED_CITATIONS', filtered)
    },
    calculateStatistics({ commit, state }) {
      const statistics = {
        total: state.citations.length,
        highConfidence: state.citations.filter(c => c.confidence >= 0.7).length,
        mediumConfidence: state.citations.filter(c => c.confidence >= 0.4 && c.confidence < 0.7).length,
        lowConfidence: state.citations.filter(c => c.confidence < 0.4).length
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
    totalPages: state => Math.ceil(state.filteredCitations.length / state.itemsPerPage)
  }
}
