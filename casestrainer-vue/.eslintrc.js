module.exports = {
  root: true,
  env: {
    node: true
  },
  extends: [
    'plugin:vue/vue3-essential',
    'eslint:recommended'
  ],
  parserOptions: {
    parser: '@babel/eslint-parser',
    requireConfigFile: false
  },
  rules: {
    'no-console': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
    'no-debugger': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
    // Disable rules that might be causing issues
    'vue/no-unused-components': 'off',
    'vue/multi-word-component-names': 'off',
    'vue/no-unused-vars': 'off',
    'no-unused-vars': 'off'
  }
}
