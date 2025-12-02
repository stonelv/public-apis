import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // 将 data 目录添加为静态资源目录
    publicDir: path.resolve(__dirname, 'data'),
  },
})
