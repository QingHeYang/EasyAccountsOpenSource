/**
 * 运行时配置
 * 此文件在构建时不会被打包，可以在部署后修改
 *
 * 使用方式：在 HTML 中引入此脚本，然后通过 window.config 访问配置
 *
 * 环境变量替换：
 * - ${API_BASE_URL} 会在部署时被替换为实际的 API 地址
 */
window.config = {
  // 主 API 地址（记账服务，端口 10672）
  apiBaseUrl: '${API_BASE_URL}',

  /**
   * AI API 地址（AI 服务，端口 10680）
   * 根据 apiBaseUrl 动态计算
   */
  get aiApiUrl() {
    // 开发环境使用代理
    if (this.apiBaseUrl === '${API_BASE_URL}' || !this.apiBaseUrl) {
      return '/ai-api'
    }
    try {
      const url = new URL(this.apiBaseUrl)
      url.port = '10680'
      return url.toString().replace(/\/$/, '')
    } catch {
      return '/ai-api'
    }
  },

  /**
   * AI WebSocket 地址
   * 根据 apiBaseUrl 动态计算，自动处理 http/https 协议转换
   */
  get aiWebSocketUrl() {
    // 开发环境
    if (this.apiBaseUrl === '${API_BASE_URL}' || !this.apiBaseUrl) {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      return `${protocol}//${window.location.host}/ai-api`
    }
    try {
      const url = new URL(this.apiBaseUrl)
      url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
      url.port = '10680'
      return url.toString().replace(/\/$/, '')
    } catch {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      return `${protocol}//${window.location.host}/ai-api`
    }
  },
}
