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
  theme: {
    extend: {
      typography: (theme) => ({
        DEFAULT: {
          css: {
            color: theme('colors.gray.800'),
            'h1, h2, h3, h4, h5, h6': {
              color: theme('colors.gray.800'),
            },
            'ul > li::before': {
              'background-color': theme('colors.gray.800')
            },
            'pre': {
              'background-color': theme('colors.gray.50'),
              'color': theme('colors.gray.700')
            },
            'thead th': {
              'text-align': 'left'
            },
          },
        },
      }),
    },
  },
  variants: {
    extend: {},
  },
  plugins: [require("@tailwindcss/typography")],
};
