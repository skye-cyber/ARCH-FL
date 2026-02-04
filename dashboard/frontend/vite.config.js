import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],
    resolve: {
        alias: {
            '@': path.resolve(__dirname, './src'),
        },
    },
    //base: './',
    server: {
        // host: '0.0.0.0',
        port: 3000,
        proxy: {
            '/api': {
                target: 'http://localhost:8008',
                changeOrigin: true,
                rewrite: (path) => path.replace(/^\/api/, '/api'),
            },
            '/ws': {
                target: 'ws://localhost:8008',
                ws: true,
            },
            //strictPort: true,    // Don't try other ports if occupied
            //open: false,         // Don't open browser automatically
            // cors: true,          // Enable CORS for captive portal
            hmr: {
                host: 'localhost', // HMR still on localhost for dev
                port: 24678
            }
        }
    }
})
