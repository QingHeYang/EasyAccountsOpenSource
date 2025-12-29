class AIWebSocketManager {
  constructor() {
    this.websocket = null;
    this.isConnected = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000;
    this.messageCallbacks = new Set();
    this.connectCallbacks = new Set();
    this.disconnectCallbacks = new Set();
    this.errorCallbacks = new Set();
  }

  connect(userId = 'user_67ce21d6-a11c-4340-851b-7a8949906aa3', agentId = 'easy-accounts-agent', useThinkLlm = false) {
    if (this.isConnected || this.websocket) {
      return;
    }

    try {
      // 从localStorage获取token
      const token = localStorage.getItem('token') || '';
      // 格式化为 Authorization=xxx
      const toolTokens = token ? `Authorization=${token}` : '';
      
      const baseUrl = window.config?.aiWebSocketUrl || 'ws://localhost:8001';
      const wsUrl = `${baseUrl}/ws/chat?user_id=${userId}&agent_id=${agentId}&use_think_llm=${useThinkLlm}&tool_tokens=${encodeURIComponent(toolTokens)}`;
      console.log('连接WebSocket:', wsUrl);
      this.websocket = new WebSocket(wsUrl);

      this.websocket.onopen = (event) => {
        console.log('AI WebSocket连接成功:', event);
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.connectCallbacks.forEach(callback => callback(event));
      };

      this.websocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.messageCallbacks.forEach(callback => callback(data));
        } catch (error) {
          console.error('解析WebSocket消息失败:', error);
          this.messageCallbacks.forEach(callback => callback(event.data));
        }
      };

      this.websocket.onclose = (event) => {
        console.log('AI WebSocket连接关闭:', event);
        this.isConnected = false;
        this.websocket = null;
        this.disconnectCallbacks.forEach(callback => callback(event));
        
        // 自动重连
        if (this.reconnectAttempts < this.maxReconnectAttempts && !event.wasClean) {
          this.scheduleReconnect();
        }
      };

      this.websocket.onerror = (error) => {
        console.error('AI WebSocket错误:', error);
        this.errorCallbacks.forEach(callback => callback(error));
      };

    } catch (error) {
      console.error('创建WebSocket连接失败:', error);
      this.errorCallbacks.forEach(callback => callback(error));
    }
  }

  scheduleReconnect() {
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts);
    console.log(`将在${delay}ms后重连WebSocket，第${this.reconnectAttempts + 1}次尝试`);
    
    setTimeout(() => {
      this.reconnectAttempts++;
      this.connect();
    }, delay);
  }

  disconnect() {
    if (this.websocket) {
      this.websocket.close(1000, '主动断开连接');
      this.websocket = null;
      this.isConnected = false;
    }
  }

  send(message) {
    if (this.isConnected && this.websocket) {
      const data = typeof message === 'string' ? message : JSON.stringify(message);
      this.websocket.send(data);
      return true;
    } else {
      console.warn('WebSocket未连接，无法发送消息:', message);
      return false;
    }
  }

  onMessage(callback) {
    this.messageCallbacks.add(callback);
    return () => this.messageCallbacks.delete(callback);
  }

  onConnect(callback) {
    this.connectCallbacks.add(callback);
    return () => this.connectCallbacks.delete(callback);
  }

  onDisconnect(callback) {
    this.disconnectCallbacks.add(callback);
    return () => this.disconnectCallbacks.delete(callback);
  }

  onError(callback) {
    this.errorCallbacks.add(callback);
    return () => this.errorCallbacks.delete(callback);
  }

  getConnectionStatus() {
    return {
      isConnected: this.isConnected,
      reconnectAttempts: this.reconnectAttempts,
      websocket: this.websocket
    };
  }
}

// 创建全局实例
const aiWebSocketManager = new AIWebSocketManager();

export default aiWebSocketManager;