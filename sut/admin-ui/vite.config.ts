import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  build: {
    outDir: '../app/static/admin',
    emptyOutDir: true,
  },
  server: {
    proxy: {
      '/auth': 'http://localhost:8000',
      '/products': 'http://localhost:8000',
      '/orders': 'http://localhost:8000',
      '/coupons': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
  },
})
