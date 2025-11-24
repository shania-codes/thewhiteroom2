import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: '../static/js',  // Flask can serve from here
    emptyOutDir: true
  },
  base: '/static/js/',
})