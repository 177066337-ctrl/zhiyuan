/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#edf6ff",
          100: "#d7ebff",
          500: "#2575d7",
          600: "#145fb4",
          700: "#114c8f",
        },
        accent: {
          500: "#1f8d67",
          600: "#187052",
        },
      },
      boxShadow: {
        soft: "0 10px 30px rgba(17, 76, 143, 0.08)",
      },
      maxWidth: {
        container: "1200px",
      },
    },
  },
  plugins: [],
};
