module.exports = {
  root: true,
  env: {
    node: true,
    es2021: true // 新增现代环境
  },
  extends: [
    'plugin:vue/vue3-essential', // 明确指定 Vue3
    'eslint:recommended',
    '@vue/eslint-config-prettier/skip-formatting' // 新格式
  ],
  parserOptions: {
    ecmaVersion: 'latest',
    parser: '@babel/eslint-parser', // 使用新解析器
    requireConfigFile: false,       // 无需额外配置-
    sourceType: 'module'
  },
  rules: {
    'no-console': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
    'no-debugger': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
    'vue/multi-word-component-names': 'off' // 关闭 Vue3 组件名警告
  },
  // 删除 overrides 部分（除非有特殊需求）
}