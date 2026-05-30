/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        cosmos: {
          950: "#05080f",
          900: "#0a0e1a",
          800: "#111827",
          700: "#1f2937",
        },
        gold: {
          300: "#e5c97a",
          400: "#d4aa5f",
          500: "#c9963e",
        },
        violet: {
          muted: "#7c6b9b",
          light: "#a893cc",
        },
        cream: "#f0e8d0",
        "cream-dim": "#c8bfa8",
      },
      fontFamily: {
        sans: ["'Inter'", "system-ui", "sans-serif"],
        serif: ["'Playfair Display'", "Georgia", "serif"],
      },
      animation: {
        "fade-in": "fadeIn 0.3s ease-in-out",
        pulse: "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "spin-slow": "spin 3s linear infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0", transform: "translateY(4px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
};
