import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173
  },
  build: {
    chunkSizeWarningLimit: 900,
    rollupOptions: {
      output: {
        manualChunks: {
          react: ["react", "react-dom", "react-router-dom"],
          antd: ["antd", "@ant-design/icons"],
          charts: ["echarts", "echarts-for-react"],
          markdown: ["react-markdown", "rehype-highlight", "highlight.js"],
          query: ["@tanstack/react-query", "axios", "zustand"]
        }
      }
    }
  }
});
