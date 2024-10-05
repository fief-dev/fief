const { babel } = require('@rollup/plugin-babel');
const { nodeResolve } = require('@rollup/plugin-node-resolve');
const terser = require('@rollup/plugin-terser');
const postcss = require('rollup-plugin-postcss');
const autoprefixer = require('autoprefixer');
const tailwindcss = require('tailwindcss');
const colors = require('tailwindcss/colors');
const plugin = require('tailwindcss/plugin');

const tailwindConfig = {
  theme: {
    extend: {
      boxShadow: {
        DEFAULT: '0 1px 3px 0 rgba(0, 0, 0, 0.08), 0 1px 2px 0 rgba(0, 0, 0, 0.02)',
        md: '0 4px 6px -1px rgba(0, 0, 0, 0.08), 0 2px 4px -1px rgba(0, 0, 0, 0.02)',
        lg: '0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -2px rgba(0, 0, 0, 0.01)',
        xl: '0 20px 25px -5px rgba(0, 0, 0, 0.08), 0 10px 10px -5px rgba(0, 0, 0, 0.01)',
      },
      colors: {
        'primary-50': 'var(--color-primary-50)',
        'primary-100': 'var(--color-primary-100)',
        'primary-200': 'var(--color-primary-200)',
        'primary-300': 'var(--color-primary-300)',
        'primary-400': 'var(--color-primary-400)',
        'primary-500': 'var(--color-primary-500)',
        'primary-600': 'var(--color-primary-600)',
        'primary-700': 'var(--color-primary-700)',
        'primary-800': 'var(--color-primary-800)',
        'primary-900': 'var(--color-primary-900)',
        'primary': 'var(--color-primary-500)',
        'primary-hover': 'var(--color-primary-600)',
        'primary-light': 'var(--color-primary-300)',
        accent: 'var(--color-accent)',
        light: 'var(--color-light)',
        'light-hover': 'var(--color-light-hover)',
        gray: colors.slate,
        'light-blue': colors.sky,
        red: colors.rose,
      },
      outline: {
        blue: '2px solid rgba(0, 112, 244, 0.5)',
      },
      fontFamily: {
        inter: ['Inter', 'sans-serif'],
      },
      fontSize: {
        xs: ['0.75rem', { lineHeight: '1.5' }],
        sm: ['0.875rem', { lineHeight: '1.5715' }],
        base: ['1rem', { lineHeight: '1.5', letterSpacing: '-0.01em' }],
        lg: ['1.125rem', { lineHeight: '1.5', letterSpacing: '-0.01em' }],
        xl: ['1.25rem', { lineHeight: '1.5', letterSpacing: '-0.01em' }],
        '2xl': ['1.5rem', { lineHeight: '1.33', letterSpacing: '-0.01em' }],
        '3xl': ['1.88rem', { lineHeight: '1.33', letterSpacing: '-0.01em' }],
        '4xl': ['2.25rem', { lineHeight: '1.25', letterSpacing: '-0.02em' }],
        '5xl': ['3rem', { lineHeight: '1.25', letterSpacing: '-0.02em' }],
        '6xl': ['3.75rem', { lineHeight: '1.2', letterSpacing: '-0.02em' }],
      },
      screens: {
        xs: '480px',
      },
      borderWidth: {
        3: '3px',
      },
      minWidth: {
        36: '9rem',
        44: '11rem',
        56: '14rem',
        60: '15rem',
        72: '18rem',
        80: '20rem',
      },
      maxWidth: {
        '8xl': '88rem',
        '9xl': '96rem',
      },
      zIndex: {
        60: '60',
      },
    },
  },
  plugins: [
    // eslint-disable-next-line global-require
    require('@tailwindcss/forms'),
    // add custom variant for expanding sidebar
    plugin(({ addVariant, e }) => {
      addVariant('sidebar-expanded', ({ modifySelectors, separator }) => {
        modifySelectors(({ className }) => `.sidebar-expanded .${e(`sidebar-expanded${separator}${className}`)}`);
      });
    }),
  ],
}

module.exports = [
  {
    input: './styles/globals.scss',
    output: {
      file: './fief/static/admin.css'
    },
    plugins: [
      postcss({
        plugins: [
          tailwindcss({
            config: {
              ...tailwindConfig,
              content: [
                './fief/templates/admin/**/*.html',
                './fief/templates/macros/**/*.html',
              ],
            },
          }),
          autoprefixer(),
        ],
        extract: true,
        minimize: true,
      }),
    ],
  },
  {
    input: './styles/globals.scss',
    output: {
      file: './fief/static/auth.css'
    },
    plugins: [
      postcss({
        plugins: [
          tailwindcss({
            config: {
              ...tailwindConfig,
              content: [
                './fief/templates/auth/**/*.html',
                './fief/templates/macros/**/*.html',
              ],
            },
          }),
          autoprefixer(),
        ],
        extract: true,
        minimize: true,
      }),
    ],
  },
  {
    input: './js/code-editor.mjs',
    output: {
      file: './fief/static/code-editor.bundle.js',
      format: 'iife',
    },
    plugins: [
      nodeResolve(),
      babel({
        babelHelpers: 'runtime',
        plugins: [
          ['@babel/plugin-transform-runtime', { useESModules: false }]
        ],
      }),
      terser(),
    ],
  },
  {
    input: './node_modules/htmx.org/dist/htmx.js',
    output: {
      file: './fief/static/htmx.bundle.js',
      format: 'iife',
    },
  },
    {
    input: './node_modules/hyperscript.org/src/_hyperscript.js',
    output: {
      file: './fief/static/hyperscript.bundle.js',
      format: 'iife',
    },
  },  
];
