import tailwindcss from "@tailwindcss/vite";

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
  plugins: [tailwindcss()],
};

export default config;
