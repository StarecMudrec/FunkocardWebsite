import { createStore } from 'vuex'
import { fetchSeasons, checkAuth } from '@/api'

export default createStore({
  state: {
    isAuthenticated: false,
    userId: null,
    seasons: [],
    loading: false,
    error: null
  },
  mutations: {
    SET_AUTH(state, { isAuthenticated, userId }) {
      state.isAuthenticated = isAuthenticated
      state.userId = userId
    },
    SET_SEASONS(state, seasons) {
      state.seasons = seasons
    },
    UPDATE_SEASON(state, updatedSeason) {
      const index = state.seasons.findIndex(s => s.uuid === updatedSeason.uuid)
      if (index !== -1) {
        state.seasons.splice(index, 1, updatedSeason)
      }
    },
    SET_LOADING(state, loading) {
      state.loading = loading
    },
    SET_ERROR(state, error) {
      state.error = error
    },
    REMOVE_SEASON(state, seasonUuid) {
      state.seasons = state.seasons.filter(season => season.uuid !== seasonUuid);
    },
  },
  actions: {
    async checkAuth({ commit }) {
      try {
        const { isAuthenticated, userId } = await checkAuth()
        commit('SET_AUTH', { isAuthenticated, userId })
      } catch (error) {
        console.error('Auth check failed:', error)
      }
    },
    async logout({ commit }) {
      try {
        await fetch('/auth/logout', { 
          method: 'POST',
          credentials: 'include'
        })
        commit('SET_AUTH', { isAuthenticated: false, userId: null })
        window.location.reload();
      } catch (error) {
        console.error('Logout failed:', error)
      }
    },
    async fetchSeasons({ commit }) {
      commit('SET_LOADING', true)
      commit('SET_ERROR', null)
      try {
        const response = await fetch('/api/seasons');
        if (!response.ok) throw new Error('Failed to fetch season IDs');
        const seasonIds = await response.json();
        const seasonPromises = seasonIds.map(id => fetch(`/api/season_info/${id}`).then(res => res.json()));
        const orderedSeasonsData = await Promise.all(seasonPromises);
        commit('SET_SEASONS', orderedSeasonsData);
      } catch (error) {
        commit('SET_ERROR', error)
        console.error('Error fetching seasons:', error)
      } finally {
        commit('SET_LOADING', false)
      }
    },
    async updateSeason({ commit }, { uuid, name }) {
      try {
        const updatedSeason = await updateSeason(uuid, { name });
        commit('UPDATE_SEASON', updatedSeason);
        return updatedSeason;
      } catch (error) {
        console.error('Error updating season:', error);
        throw error;
      }
    }
  }
})