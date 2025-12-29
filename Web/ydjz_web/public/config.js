window.config = {
  // 使用相对路径，通过 nginx 代理
  apiBaseUrl: "/api",
  aiApiUrl: "/ai",
  get aiWebSocketUrl() {
    // 根据当前页面协议自动选择 ws 或 wss
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    // 返回基础 WebSocket URL，不包含 /ws 路径
    return `${protocol}//${host}`;
  }
};
