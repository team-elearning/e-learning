import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import vueJsx from '@vitejs/plugin-vue-jsx'  // thêm plugin vue-jsx
// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueJsx(),  // sử dụng plugin vue-jsx
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
})
