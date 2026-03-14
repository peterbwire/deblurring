/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#07111f",
        surface: "#0d1728",
        shell: "#111d30",
        stroke: "#24334c",
        accent: "#79d7ff",
        signal: "#9fffe0",
        caution: "#ffca6b",
      },
      fontFamily: {
        body: ['"Space Grotesk"', '"Aptos"', '"Segoe UI"', "sans-serif"],
        heading: ['"Sora"', '"Trebuchet MS"', '"Segoe UI"', "sans-serif"],
      },
      boxShadow: {
        panel: "0 24px 80px rgba(2, 12, 24, 0.45)",
        glow: "0 0 0 1px rgba(121, 215, 255, 0.18), 0 20px 80px rgba(23, 88, 132, 0.28)",
      },
      backgroundImage: {
        mesh: "radial-gradient(circle at top left, rgba(121, 215, 255, 0.18), transparent 34%), radial-gradient(circle at 85% 15%, rgba(159, 255, 224, 0.1), transparent 24%), linear-gradient(180deg, rgba(6, 14, 26, 0.96), rgba(7, 17, 31, 1))",
      },
    },
  },
  plugins: [],
};
