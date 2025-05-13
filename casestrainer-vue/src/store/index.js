import { createStore } from 'vuex'
import unconfirmedCitations from './modules/unconfirmedCitations'
import multitoolConfirmed from './modules/multitoolConfirmed'
import citationNetwork from './modules/citationNetwork'
import mlClassifier from './modules/mlClassifier'

export default createStore({
  state: {
    loading: false,
    error: null
  },
  mutations: {
    SET_LOADING(state, status) {
      state.loading = status
    },
    SET_ERROR(state, error) {
      state.error = error
    }
  },
  actions: {
    setLoading({ commit }, status) {
      commit('SET_LOADING', status)
    },
    setError({ commit }, error) {
      commit('SET_ERROR', error)
    }
  },
  modules: {
    unconfirmedCitations,
    multitoolConfirmed,
    citationNetwork,
    mlClassifier
  }
})
