/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./static/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        'dark-bg': '#0a0e1a',
        'dark-card': '#111827',
        'cyber-blue': '#00f2ff',
        'cyber-purple': '#a855f7',
      },
    },
  },
  plugins: [],
}
