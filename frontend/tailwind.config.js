/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      keyframes: {
        'float': {
          '0%, 100%': { transform: 'translateY(0) scale(1)' },
          '50%': { transform: 'translateY(-5px) scale(1.05)' }
        },
        'gradient-x': {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' }
        },
        'ripple-out': {
          '0%': { transform: 'scale(0)', opacity: '1' },
          '100%': { transform: 'scale(2.5)', opacity: '0' }
        },
        'ping-animation': {
          '75%, 100%': { transform: 'scale(2.5)', opacity: '0' }
        },
        'gradient-rotate': {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' }
        },
        'pulse-animation': {
          '0%, 100%': { transform: 'scale(1)', opacity: '0.8' },
          '50%': { transform: 'scale(2)', opacity: '0' }
        },
        'slide-down': {
          'from': { opacity: '0', transform: 'translateY(-20px)' },
          'to': { opacity: '1', transform: 'translateY(0)' }
        }
      },
      animation: {
        'float': 'float 3s ease-in-out infinite',
        'gradient-x': 'gradient-x 3s ease infinite',
        'ripple-out': 'ripple-out 0.8s cubic-bezier(0.34, 1.56, 0.64, 1)',
        'ping-custom': 'ping-animation 1.5s cubic-bezier(0, 0, 0.2, 1) infinite',
        'gradient-rotate': 'gradient-rotate 3s ease infinite',
        'pulse-custom': 'pulse-animation 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'slide-down': 'slide-down 0.3s ease-out'
      }
    }
  },
  plugins: []
}
