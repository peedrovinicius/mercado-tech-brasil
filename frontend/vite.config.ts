import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          react: ['react', 'react-dom', '@tanstack/react-query'],
          charts: [
            'echarts/core',
            'echarts/charts',
            'echarts/components',
            'echarts/renderers',
            'echarts-for-react/lib/core',
          ],
        },
      },
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
