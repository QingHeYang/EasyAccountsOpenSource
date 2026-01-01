window.config = {
  // 后端 API 基础路径
  apiBaseUrl: "/api",
  // AI 服务基础路径
  aiApiUrl: "/ai",
  // WebSocket URL（自动根据协议选择 ws/wss）
  get wsBaseUrl() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${window.location.host}`;
  }
};
