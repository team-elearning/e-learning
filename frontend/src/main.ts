// import { createApp } from 'vue'
// import { createPinia } from 'pinia'
// import ElementPlus from 'element-plus'


// import App from './App.vue'
// import router from './router'
// import "@/styles/tailwind.css"

// const app = createApp(App)

// app.use(createPinia())
// app.use(router)
// app.use(ElementPlus)


// app.mount('#app')


import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from '@/router'
import 'element-plus/dist/index.css'
import '@/styles/tailwind.css'
import { useAuthStore } from '@/store/auth.store'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'


const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
app.use(ElementPlus)
useAuthStore().hydrateFromStorage()
app.use(router).mount('#app')
