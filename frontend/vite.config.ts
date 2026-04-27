import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

function manualChunks(id: string): string | undefined {
  const normalizedId = id.replace(/\\/g, "/");
  if (!normalizedId.includes("/node_modules/")) {
    return undefined;
  }

  if (/(\/node_modules\/)(react|react-dom|react-router-dom)\//.test(normalizedId)) {
    return "react";
  }
  if (/(\/node_modules\/)(@tanstack\/react-query|axios|zustand)\//.test(normalizedId)) {
    return "query";
  }
  if (/(\/node_modules\/)(echarts|echarts-for-react)\//.test(normalizedId)) {
    return "charts";
  }
  if (/(\/node_modules\/)(react-markdown|rehype-highlight|highlight\.js)\//.test(normalizedId)) {
    return "markdown";
  }

  if (
    normalizedId.includes("/node_modules/antd/") ||
    normalizedId.includes("/node_modules/@ant-design/") ||
    normalizedId.includes("/node_modules/@rc-component/") ||
    normalizedId.includes("/node_modules/rc-")
  ) {
    return "antd";
  }
  return undefined;
}

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173
  },
  build: {
    chunkSizeWarningLimit: 1300,
    rollupOptions: {
      output: {
        // Ant Design 内部依赖存在互相引用，保持同一 vendor chunk 可避免循环 chunk 告警。
        manualChunks
      }
    }
  }
});
