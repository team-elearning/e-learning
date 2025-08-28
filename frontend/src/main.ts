import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { createPinia } from 'pinia'
import i18n from './plugins/i18n'
import ElementPlus from './plugins/element-plus'
import './styles/index.scss'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(ElementPlus)
app.use(i18n)

app.mount('#app')
