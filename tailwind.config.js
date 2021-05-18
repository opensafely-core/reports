module.exports = {
  mode: "jit",
  purge: {
    enabled: true,
    layers: ["components", "utilities"],
    content: [
      "./templates/**/*.html",
      "./gateway/templates/**/*.html",
      "./outputs/templates/**/*.html",
    ],
    options: {
      safelist: [],
    },
  },
  darkMode: false,
  variants: {
    extend: {},
  },
  plugins: [require("@tailwindcss/typography")],
};
