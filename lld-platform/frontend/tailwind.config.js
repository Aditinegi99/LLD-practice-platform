/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        ink: {
          950: '#0D1216',
          900: '#10161B',
          800: '#171F26',
          700: '#212B33',
          600: '#2A343D',
        },
        paper: {
          100: '#E8EDF1',
          300: '#8B9AA6',
        },
        blue: {
          line: '#3D6E8C',
          glow: '#6FA9C9',
        },
        amber: {
          DEFAULT: '#E8A33D',
          dim: '#B9812F',
        },
        good: '#5FAE7B',
        warn: '#D97A4C',
        bad: '#C0564F',
      },
      fontFamily: {
        display: ['"Space Grotesk"', 'sans-serif'],
        body: ['"Inter"', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'monospace'],
      },
      backgroundImage: {
        blueprint: `linear-gradient(rgba(61,110,140,0.10) 1px, transparent 1px), linear-gradient(90deg, rgba(61,110,140,0.10) 1px, transparent 1px)`,
      },
      backgroundSize: {
        grid: '28px 28px',
      },
    },
  },
  plugins: [],
}
