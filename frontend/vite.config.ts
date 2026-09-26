import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          const has = (fragment: string) => id.indexOf(fragment) >= 0

          if (!has('node_modules')) {
            return undefined
          }
          if (has('/zrender/')) {
            return 'zrender'
          }
          if (has('/echarts-for-react/')) {
            return 'echarts-react'
          }
          if (has('/echarts/lib/chart/')) {
            return 'echarts-charts'
          }
          if (has('/echarts/lib/component/')) {
            return 'echarts-components'
          }
          if (has('/echarts/')) {
            return 'echarts-core'
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
