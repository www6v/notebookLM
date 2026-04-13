import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import vuetify from './plugins/vuetify'
import { i18n } from './plugins/i18n'
import { useThemeStore } from './stores/useThemeStore'
import { initWebVitals } from './utils/performance'

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
app.use(vuetify)
app.use(i18n)
app.use(router)

useThemeStore()
initWebVitals()
app.mount('#app')
