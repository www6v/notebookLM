import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

import App from './App.vue'
import router from './router'
import { i18n } from './plugins/i18n'
import { useThemeStore } from './stores/useThemeStore'

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
app.use(i18n)
app.use(router)
app.use(ElementPlus)

useThemeStore()
app.mount('#app')
