import legacy from "@vitejs/plugin-legacy";

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
  ],
};

export default config;
