const defaultTheme = require("tailwindcss/defaultTheme");

module.exports = {
  mode: "jit",
  purge: {
    enabled: true,
    layers: ["components", "utilities"],
    content: [
      "./templates/**/*.html",
      "./gateway/templates/**/*.html",
      "./reports/templates/**/*.html",
    ],
    options: {
      safelist: [],
    },
  },
  darkMode: false,
  theme: {
    extend: {
      fontFamily: {
        sans: ["Public Sans", ...defaultTheme.fontFamily.sans],
      },
      typography: (theme) => ({
        DEFAULT: {
          css: {
            color: theme("colors.gray.800"),
            "h1, h2, h3, h4, h5, h6": {
              color: theme("colors.gray.800"),
            },
            "ul > li::before": {
              "background-color": theme("colors.gray.800"),
            },
            pre: {
              "background-color": theme("colors.gray.50"),
              color: theme("colors.gray.700"),
            },
            "thead th": {
              "text-align": "left",
            },
            a: {
              "font-weight": 600,
            },
            "a:hover": {
              color: theme("colors.blue.900"),
              "text-decoration": "underline",
            },
            'code::before': {
              content: ''
            },
            'code::after': {
              content: ''
            }
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
