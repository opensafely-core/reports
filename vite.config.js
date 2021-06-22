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
        main: "./assets/scripts/main.js",
        notebook: "./assets/scripts/notebook.js",
      },
    },
    outDir: "static/dist",
    emptyOutDir: true,
  },
  plugins: [
    legacy({
      targets: ["ie >= 11"],
      additionalLegacyPolyfills: ["regenerator-runtime/runtime"],
    }),
  ],
};

export default config;
