import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "node:path";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    strictPort: true,
    host: "127.0.0.1",
    // Phase 11 live cutover: proxy /api/* to the FastAPI backend on :8000
    // so the SPA's fetch('/api/health') goes through vite and hits
    // the real model. The proxy is only active in dev mode; the
    // production build is served by Vite preview which doesn't
    // proxy, so production needs the backend on the same origin
    // or a reverse proxy (documented in README.md).
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});