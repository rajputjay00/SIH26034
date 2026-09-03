/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        nirikshan: {
          navy: '#0B2A4A',
          navyDark: '#071C33',
          blue: '#1769AA',
          blueLight: '#E8F1F9',
          saffron: '#F28C28',
          saffronLight: '#FEF3E9',
          green: '#2F8F6B',
          greenLight: '#EAF5F1',
          surface: '#FFFFFF',
          lightBg: '#F7F9FC',
          border: '#E5EAF0',
          text: '#0B2A4A',
          muted: '#5A6E85',
        },
        gov: {
          bg: '#F7F9FC',
          surface: '#FFFFFF',
          border: '#E5EAF0',
          navy: '#0B2A4A',
          primary: '#1769AA',
          text: '#0B2A4A',
          muted: '#5A6E85',
          saffron: '#F28C28',
          pastelBlue: '#E8F1F9',
          pastelGreen: '#EAF5F1',
          pastelAmber: '#FEF3E9',
          pastelLavender: '#F3E8FF',
          warning: '#DC2626',
          warningLight: '#FEE2E2',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      borderRadius: {
        gov: '6px',
        brand: '8px',
      },
      boxShadow: {
        subtle: '0 1px 3px rgba(11, 42, 74, 0.06), 0 1px 2px rgba(11, 42, 74, 0.04)',
        card: '0 4px 12px rgba(11, 42, 74, 0.05), 0 1px 3px rgba(11, 42, 74, 0.03)',
        elevated: '0 10px 25px -5px rgba(11, 42, 74, 0.08), 0 8px 10px -6px rgba(11, 42, 74, 0.04)',
      },
    },
  },
  plugins: [],
};
