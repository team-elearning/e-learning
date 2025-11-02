// vite.config.ts
import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import vueJsx from '@vitejs/plugin-vue-jsx'
import sitemap from 'vite-plugin-sitemap'

export default defineConfig(({ mode }) => ({
  plugins: [
    vue(),
    vueDevTools(),
    vueJsx(),
    sitemap({ hostname: 'https://eduriot.fit' }),
  ],
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
  // chỉ bật proxy khi dev (vite serve)
  server: mode === 'development' ? {
    proxy: {
      '/api': {
        target: 'https://api.eduriot.fit',
        changeOrigin: true,
        secure: true,
        rewrite: (p) => p.replace(/^\/api/, '/api'),
      }
    }
  } : undefined
}))
