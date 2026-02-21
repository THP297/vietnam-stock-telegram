import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vite.dev/config/
// - Dev: API calls go to /api and are proxied to local backend (below). No VITE_API_URL needed.
// - Production build: set VITE_API_URL to your API origin (e.g. https://vietnam-stock-telegram.onrender.com).
// - VITE_BASE_PATH: set in CI for GitHub Pages project site (e.g. /vietnam-stock-telegram/).
export default defineConfig({
  base: process.env.VITE_BASE_PATH || "/",
  plugins: [react()],
  server: {
    proxy: {
      "/api": { target: "http://127.0.0.1:5003", changeOrigin: true },
    },
  },
});
