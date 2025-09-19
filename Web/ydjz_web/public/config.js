window.config = {
  //apiBaseUrl: "http://192.168.50.226:10670",
  apiBaseUrl: "${API_BASE_URL}",
  // AI服务使用apiBaseUrl的主机，端口改为10680
  get aiApiUrl() {
    const url = new URL(this.apiBaseUrl);
    url.port = '10680';
    return url.toString();
  },
  get aiWebSocketUrl() {
    const url = new URL(this.apiBaseUrl);
    url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
    url.port = '10680';
    return url.toString();
  }
};
