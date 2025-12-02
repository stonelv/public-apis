import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // 配置静态资源目录
    static: {
      directory: resolve(__dirname, 'data'),
      publicPath: '/data'
    }
  }
})
