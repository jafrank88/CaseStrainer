import api from '@/api/citations'

export default {
  namespaced: true,
  state: {
    networkData: null,
    visualizationType: 'force',
    filter: 'all',
    depth: 1,
    statistics: {
      nodes: 0,
      edges: 0,
      confirmedNodes: 0,
      unconfirmedNodes: 0,
      sourceDocuments: 0
    }
  },
  mutations: {
    SET_NETWORK_DATA(state, data) {
      state.networkData = data
    },
    SET_VISUALIZATION_TYPE(state, type) {
      state.visualizationType = type
    },
    SET_FILTER(state, filter) {
      state.filter = filter
    },
    SET_DEPTH(state, depth) {
      state.depth = depth
    },
    SET_STATISTICS(state, statistics) {
      state.statistics = statistics
    }
  },
  actions: {
    async fetchNetworkData({ commit, dispatch, state }) {
      try {
        commit('SET_LOADING', true, { root: true })
        const response = await api.getCitationNetworkData(state.filter, state.depth)
        commit('SET_NETWORK_DATA', response.data)
        dispatch('calculateStatistics')
        commit('SET_LOADING', false, { root: true })
        return response.data
      } catch (error) {
        commit('SET_ERROR', error.message, { root: true })
        commit('SET_LOADING', false, { root: true })
        throw error
      }
    },
    setVisualizationType({ commit }, type) {
      commit('SET_VISUALIZATION_TYPE', type)
    },
    setFilter({ commit }, filter) {
      commit('SET_FILTER', filter)
    },
    setDepth({ commit }, depth) {
      commit('SET_DEPTH', depth)
    },
    calculateStatistics({ commit, state }) {
      if (!state.networkData) return
      
      const nodes = state.networkData.nodes || []
      const links = state.networkData.links || []
      
      const confirmedNodes = nodes.filter(node => node.status === 'confirmed').length
      const unconfirmedNodes = nodes.filter(node => node.status === 'unconfirmed').length
      const sourceDocuments = nodes.filter(node => node.type === 'source_document').length
      
      const statistics = {
        nodes: nodes.length,
        edges: links.length,
        confirmedNodes,
        unconfirmedNodes,
        sourceDocuments
      }
      
      commit('SET_STATISTICS', statistics)
    }
  },
  getters: {
    nodesByType: state => type => {
      if (!state.networkData || !state.networkData.nodes) return []
      return state.networkData.nodes.filter(node => node.type === type)
    },
    nodesByStatus: state => status => {
      if (!state.networkData || !state.networkData.nodes) return []
      return state.networkData.nodes.filter(node => node.status === status)
    }
  }
}
