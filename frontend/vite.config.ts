import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vite.dev/config/
// VITE_BASE_PATH: set in CI for GitHub Pages project site (e.g. /vietnam-stock-telegram/)
export default defineConfig({
  base: process.env.VITE_BASE_PATH || "/",
  plugins: [react()],
  server: {
    proxy: {
      "/api": { target: "http://127.0.0.1:5003", changeOrigin: true },
    },
  },
});
