import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api/v1/ai-chat': {
        target: 'http://localhost:8002',
        changeOrigin: true,
      },
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
        // 后端 Controller 已带 /api 前缀，不做 rewrite
      },
      '/ws/v1/ai-chat': {
        target: 'ws://localhost:8002',
        ws: true,
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8080',
        ws: true,
        changeOrigin: true,
      },
    },
  },
})