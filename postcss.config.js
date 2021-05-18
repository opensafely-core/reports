module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
    cssnano: {
      preset: [
        "default",
        {
          colormin: false,
          discardComments: { removeAll: true },
        },
      ],
    },
  },
};
