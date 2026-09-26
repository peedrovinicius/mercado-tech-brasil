import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react()],
  build: {
    chunkSizeWarningLimit: 600,
    rollupOptions: {
      output: {
        manualChunks(id) {
          const has = (fragment: string) => id.indexOf(fragment) >= 0

          if (!has('node_modules')) {
            return undefined
          }
          if (
            has('/echarts/') ||
            has('/zrender/') ||
            has('/echarts-for-react/')
          ) {
            return 'charts'
          }
          if (
            has('/react/') ||
            has('/react-dom/') ||
            has('/@tanstack/react-query/')
          ) {
            return 'react'
          }
          return undefined
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
