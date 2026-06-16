import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/dtu/api': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/daylight/api': {
        target: 'http://localhost:8002',
        changeOrigin: true,
      },
      '/sunlight/api': {
        target: 'http://localhost:8003',
        changeOrigin: true,
      },
      '/alarm/api': {
        target: 'http://localhost:8004',
        changeOrigin: true,
      },
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
