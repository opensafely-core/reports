import { fontFamily } from "tailwindcss/defaultTheme";
import tailwindTypography from "@tailwindcss/typography";
import tailwindForms from "@tailwindcss/forms";

/** @type {import('tailwindcss').Config} */
export default {
  content: ["./templates/**/*.html", "./assets/src/scripts/**/*.js"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Public Sans", ...fontFamily.sans],
      },
      colors: {
        oxford: {
          DEFAULT: "#002147",
          50: "#f1f7ff",
          100: "#cfe5ff",
          200: "#9ccaff",
          300: "#69afff",
          400: "#3693ff",
          500: "#0378ff",
          600: "#0058be",
          700: "#00397a",
          800: "#002147",
          900: "#001936",
        },
      },
    },
  },
  plugins: [tailwindTypography, tailwindForms],
};
