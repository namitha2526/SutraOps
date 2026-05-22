/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // High fidelity enterprise slate & indigo accent configurations
        brand: {
          50: '#f5f7fa',
          100: '#eaeef4',
          200: '#d0dbe7',
          300: '#a7bed3',
          400: '#789cb9',
          500: '#567fa1',
          600: '#436685',
          700: '#37526c',
          800: '#30465a',
          900: '#2b3c4f',
          950: '#1b2633',
        },
        slate: {
          950: '#0b0f19',  # Deep custom obsidian background color
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
      animation: {
        'pulse-subtle': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      }
    },
  },
  plugins: [],
}
