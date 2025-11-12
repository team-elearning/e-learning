// vite.config.ts
import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import vueDevTools from "vite-plugin-vue-devtools";
import vueJsx from "@vitejs/plugin-vue-jsx";
import sitemap from "vite-plugin-sitemap";

export default defineConfig(({ mode }) => ({
  base: "/", // 🔹 đảm bảo build ra đường dẫn tuyệt đối
  plugins: [
    vue(),
    vueDevTools(),
    vueJsx(),
    sitemap({ hostname: "https://eduriot.fit" }),
  ],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  server:
    mode === "development"
      ? {
        proxy: {
          "/api": {
            target: "https://api.eduriot.fit",
            changeOrigin: true,
            secure: false, // ✅ linh hoạt hơn
            // Nếu backend KHÔNG có prefix /api, thì dùng dòng này:
            // rewrite: (p) => p.replace(/^\/api/, ""),
          },
        },
      }
      : undefined,
}));
