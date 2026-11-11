/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#12263a",
        navy: { 700: "#0b3a5b", 800: "#082c46", 900: "#061f33" },
        // Okabe-Ito colour-blind-safe palette
        oi: {
          blue: "#0072B2", orange: "#E69F00", sky: "#56B4E9", green: "#009E73",
          yellow: "#F0E442", red: "#D55E00", pink: "#CC79A7",
        },
      },
      fontFamily: { sans: ["Inter", "system-ui", "Segoe UI", "Roboto", "Helvetica", "Arial", "sans-serif"] },
    },
  },
  plugins: [],
};
