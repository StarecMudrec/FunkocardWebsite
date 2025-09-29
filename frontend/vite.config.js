import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  server: {
    host: true,
    allowedHosts: ['dahole.ru'],
    proxy: {
      '/api': {
        target: 'http://web:8000',
        changeOrigin: true,
        secure: false
      },
      '/auth': {
        target: 'http://web:8000',
        changeOrigin: true,
        secure: false
      },
      '/card_imgs': {
        target: 'http://web:8000',
        changeOrigin: true,
        secure: false
      }
    }
  }
})
