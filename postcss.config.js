const purgecss = require("@fullhuman/postcss-purgecss");
const autoprefixer = require("autoprefixer");
const cssnano = require("cssnano");

module.exports = {
  plugins: [
    purgecss({
      content: [
        "./templates/*.html",
        "./gateway/templates/**/*.html",
        "./outputs/templates/**/*.html",
      ],
      safelist: ["show", "hide"],
    }),
    autoprefixer(),
    cssnano({
      preset: [
        "default",
        {
          colormin: false,
          discardComments: { removeAll: true },
        },
      ],
    }),
  ],
};
