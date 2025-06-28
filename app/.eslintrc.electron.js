module.exports = {
  env: {
    node: true,
    es2021: true,
  },
  extends: [
    'eslint:recommended'
  ],
  parserOptions: {
    ecmaVersion: 12,
    sourceType: 'script', // CommonJS, no ES modules
  },
  rules: {
    'no-console': 'off',
    'no-unused-vars': ['error', { 
      'varsIgnorePattern': '^_',
      'argsIgnorePattern': '^_'
    }],
    'prefer-const': 'warn',
    'no-var': 'error',
  },
  globals: {
    __dirname: 'readonly',
    __filename: 'readonly',
    process: 'readonly',
    Buffer: 'readonly',
    global: 'readonly',
  }
}; 