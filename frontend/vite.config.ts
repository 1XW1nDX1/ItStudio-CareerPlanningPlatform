import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8080', // 你们后端的真实地址
        changeOrigin: true,
        // 如果你们后端的接口本来就没有 /api 前缀，需要用下面这行重写；如果有，就注释掉下面这行
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})