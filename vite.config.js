/**
 * @type {import('vite').UserConfig}
 */
const config = {
  base: '/static/',
  build: {
    manifest: true,
    rollupOptions: {
      input: ["./assets/scripts/main.js"],
    },
    outDir: "static/dist",
    emptyOutDir: true,
  },
};

export default config;
