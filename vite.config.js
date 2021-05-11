/**
 * @type {import('vite').UserConfig}
 */
const config = {
  build: {
    manifest: false,
    rollupOptions: {
      input: ["./assets/scripts/main.js"],
      output: {
        entryFileNames: `[name].js`,
        chunkFileNames: `[name].js`,
        assetFileNames: `[name].[ext]`,
        manualChunks: {},
      },
    },
    outDir: "./dist",
    emptyOutDir: true,
  },
};

export default config;
