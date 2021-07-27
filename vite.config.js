import legacy from "@vitejs/plugin-legacy";
import copy from "rollup-plugin-copy";

/**
 * @type {import('vite').UserConfig}
 */
const config = {
  base: "/static/",
  build: {
    manifest: true,
    rollupOptions: {
      input: {
        main: "./assets/src/scripts/main.js",
        notebook: "./assets/src/scripts/notebook.js",
      },
    },
    outDir: "assets/dist",
    emptyOutDir: true,
  },
  plugins: [
    legacy({
      targets: ["ie >= 11"],
      additionalLegacyPolyfills: ["regenerator-runtime/runtime"],
      polyfills: ["es.promise", "es.array.iterator"],
    }),
    copy({
      targets: [
        {
          src: "./node_modules/alpinejs/dist/*",
          dest: "./assets/dist/vendor",
        },
      ],
      hook: "writeBundle",
    }),
  ],
};

export default config;
