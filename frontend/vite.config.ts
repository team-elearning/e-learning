// vite.config.ts
import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import vueDevTools from "vite-plugin-vue-devtools";
import vueJsx from "@vitejs/plugin-vue-jsx";
import sitemap from "vite-plugin-sitemap";
import https from "node:https";

export default defineConfig(({ mode }) => {
  // 2. Tạo một Agent để giữ kết nối (Keep-Alive)
  const agent = new https.Agent({
    keepAlive: true,
    keepAliveMsecs: 20000, // Giữ kết nối 20s
  });

  return {
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

                // 3. Thêm dòng này để dùng Agent đã tạo
                agent: agent, 
                configure: (proxy, _options) => {
                  proxy.on('error', (err, _req, _res) => {
                    console.log('proxy error', err);
                  });
                  proxy.on('proxyReq', (proxyReq, req, _res) => {
                  // Log để xem nó có thực sự đi qua proxy không
                  // console.log('Sending Request to the Target:', req.method, req.url);
                  });
                },
              },
          },
        }
      : undefined,
  };
});


// export default defineConfig(({ mode }) => {
//   // 2. Tạo một Agent để giữ kết nối (Keep-Alive)
//   const agent = new https.Agent({
//     keepAlive: true,
//     keepAliveMsecs: 20000, // Giữ kết nối 20s
//   });

//   return {
//     base: "/",
//     plugins: [
//       vue(),
//       vueDevTools(),
//       vueJsx(),
//       sitemap({ hostname: "https://eduriot.fit" }),
//     ],
//     resolve: {
//       alias: {
//         "@": fileURLToPath(new URL("./src", import.meta.url)),
//       },
//     },
//     server:
//       mode === "development"
//         ? {
//             proxy: {
//               "/api": {
//                 target: "https://api.eduriot.fit",
//                 changeOrigin: true,
//                 secure: false,
//                 // 3. Thêm dòng này để dùng Agent đã tạo
//                 agent: agent, 
//                 configure: (proxy, _options) => {
//                   proxy.on('error', (err, _req, _res) => {
//                     console.log('proxy error', err);
//                   });
//                   proxy.on('proxyReq', (proxyReq, req, _res) => {
//                     // Log để xem nó có thực sự đi qua proxy không
//                     // console.log('Sending Request to the Target:', req.method, req.url);
//                   });
//                 },
//               },
//             },
//           }
//         : undefined,
//   };
// });
