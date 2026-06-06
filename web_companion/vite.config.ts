import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// NOTE: vite-plugin-pwa removed to avoid build collision with static public/sw.js
// and public/manifest.webmanifest. The static shell (public/ dir) is the single
// source of truth until npm install + a real build run is set up on Mac Studio.
// Re-enabling vite-plugin-pwa requires: remove public/sw.js, public/manifest.webmanifest,
// and the manual registerServiceWorker script from index.html first.

export default defineConfig({
  plugins: [
    react()
  ],
  server: { host: true, port: 5173 }
})
