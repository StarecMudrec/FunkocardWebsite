import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'

// Create the Vue app
const app = createApp(App)

// Use plugins
app.use(store)
app.use(router)

// Mount the app
app.mount('#app')

// Check authentication status when the app starts
store.dispatch('checkAuth')
