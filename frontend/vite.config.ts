import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) {
            return undefined
          }
          if (id.includes('/zrender/')) {
            return 'zrender'
          }
          if (id.includes('/echarts-for-react/')) {
            return 'echarts-react'
          }
          if (id.includes('/echarts/lib/chart/')) {
            return 'echarts-charts'
          }
          if (id.includes('/echarts/lib/component/')) {
            return 'echarts-components'
          }
          if (id.includes('/echarts/')) {
            return 'echarts-core'
          }
          if (
            id.includes('/react/') ||
            id.includes('/react-dom/') ||
            id.includes('/@tanstack/react-query/')
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
