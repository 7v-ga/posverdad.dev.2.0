// apps/web/eslint.config.js
import js from '@eslint/js'
import globalsLib from 'globals'
import nextPlugin from '@next/eslint-plugin-next'
import reactHooks from 'eslint-plugin-react-hooks'
import tseslint from 'typescript-eslint'

export default [
  // Ignorar artefactos
  {
    ignores: [
      'node_modules/**',
      '.next/**',
      'out/**',
      'build/**',
      'coverage/**',
      'dist/**',
      'next-env.d.ts',
    ],
  },

  // Reglas base JS (ESLint oficial)
  js.configs.recommended,

  // Reglas TS "no type-aware" (no requieren project/tsconfig)
  ...tseslint.configs.recommended,

  // Capa de proyecto: globals, Next y React Hooks
  {
    languageOptions: {
      globals: {
        ...globalsLib.browser,
        ...globalsLib.node,
      },
    },
    plugins: {
      '@next/next': nextPlugin,
      'react-hooks': reactHooks,
    },
    rules: {
      // Next
      ...nextPlugin.configs.recommended.rules,
      '@next/next/no-img-element': 'off',

      // React
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'warn',

      // Estéticas comúnmente ruidosas
      'react/no-unescaped-entities': 'off',
    },
  },
]
