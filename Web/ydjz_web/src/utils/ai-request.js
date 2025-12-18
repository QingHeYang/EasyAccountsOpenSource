import axios from 'axios';

class AIHttpService {
  constructor() {
    this.client = null;
    this.initClient();
  }

  initClient() {
    const baseURL = window.config?.aiApiUrl || 'http://localhost:10672';
    
    this.client = axios.create({
      baseURL: baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
    });

    // 请求拦截器
    this.client.interceptors.request.use(
      (config) => {
        console.log('AI HTTP请求:', config.method?.toUpperCase(), config.url, config.data);
        return config;
      },
      (error) => {
        console.error('AI HTTP请求错误:', error);
        return Promise.reject(error);
      }
    );

    // 响应拦截器
    this.client.interceptors.response.use(
      (response) => {
        console.log('AI HTTP响应:', response.status, response.data);
        return response;
      },
      (error) => {
        console.error('AI HTTP响应错误:', error.response?.status, error.message);
        
        // 统一错误处理
        const errorMsg = this.handleError(error);
        return Promise.reject(new Error(errorMsg));
      }
    );
  }

  handleError(error) {
    if (error.response) {
      // 服务器返回错误状态码
      const { status, data } = error.response;
      switch (status) {
        case 400:
          return `请求参数错误: ${data?.message || '参数不正确'}`;
        case 401:
          return 'AI服务认证失败';
        case 403:
          return 'AI服务访问被拒绝';
        case 404:
          return 'AI服务接口不存在';
        case 429:
          return 'AI服务请求过于频繁，请稍后再试';
        case 500:
          return 'AI服务内部错误';
        case 503:
          return 'AI服务暂时不可用';
        default:
          return `AI服务错误 (${status}): ${data?.message || '未知错误'}`;
      }
    } else if (error.request) {
      // 网络错误
      return 'AI服务连接失败，请检查网络或服务状态';
    } else {
      // 其他错误
      return `AI服务请求失败: ${error.message}`;
    }
  }

  // GET请求
  async get(url, params = {}) {
    const response = await this.client.get(url, { params });
    return response.data;
  }

  // POST请求
  async post(url, data = {}) {
    const response = await this.client.post(url, data);
    return response.data;
  }

  // PUT请求
  async put(url, data = {}) {
    const response = await this.client.put(url, data);
    return response.data;
  }

  // DELETE请求
  async delete(url) {
    const response = await this.client.delete(url);
    return response.data;
  }

  // 流式请求（用于流式AI对话）
  async stream(url, data = {}, onMessage = () => {}) {
    const response = await this.client.post(url, data, {
      responseType: 'stream',
      headers: {
        'Accept': 'text/event-stream',
        'Cache-Control': 'no-cache'
      }
    });

    const reader = response.data.getReader();
    const decoder = new TextDecoder();

    // eslint-disable-next-line no-constant-condition
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const parsedData = JSON.parse(line.slice(6));
            onMessage(parsedData);
          } catch (e) {
            console.warn('解析流数据失败:', line);
          }
        }
      }
    }
  }

  // 检查AI服务健康状态
  async checkHealth() {
    try {
      const response = await this.get('/health');
      return {
        status: 'healthy',
        data: response
      };
    } catch (error) {
      return {
        status: 'unhealthy',
        error: error.message
      };
    }
  }

  // 更新配置
  updateConfig(aiApiUrl) {
    if (aiApiUrl) {
      this.client.defaults.baseURL = aiApiUrl;
    }
  }
}

// 创建全局AI HTTP服务实例
const aiHttpService = new AIHttpService();

export default aiHttpService;