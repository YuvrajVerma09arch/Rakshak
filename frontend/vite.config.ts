import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// In dev, /api proxies to the local FastAPI backend; in production the nginx
// container does the same rewrite — the client code only ever calls /api/*.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
