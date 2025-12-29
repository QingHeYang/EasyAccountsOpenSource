/**
 * WebSocket 工具类
 */

export interface WebSocketOptions {
  reconnectInterval: number  // 重连间隔
  maxReconnectAttempts: number  // 最大重连次数
  heartbeatInterval: number  // 心跳间隔
}

type EventCallback = (data: unknown) => void

class WebSocketClient {
  private ws: WebSocket | null = null
  private baseURL: string | null = null
  private lastUrl: string | null = null
  private reconnectCount = 0
  private isReconnecting = false
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null
  private listeners = new Map<string, EventCallback[]>()
  private options: WebSocketOptions = {
    reconnectInterval: 5000,
    maxReconnectAttempts: 10,
    heartbeatInterval: 30000,
  }

  // 初始化 WebSocket 连接
  init(
    baseURL: string,
    path = '',
    params: Record<string, string> = {},
    options: Partial<WebSocketOptions> = {}
  ): Promise<void> {
    this.baseURL = baseURL
    this.options = { ...this.options, ...options }

    // 构建完整的 WebSocket URL
    let url = baseURL
    if (path) {
      url += path.startsWith('/') ? path : '/' + path
    }

    // 添加查询参数
    if (Object.keys(params).length > 0) {
      const queryString = new URLSearchParams(params).toString()
      url += url.includes('?') ? '&' + queryString : '?' + queryString
    }

    return this.connect(url)
  }

  connect(url: string): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.lastUrl = url
        this.ws = new WebSocket(url)

        const onOpen = () => {
          this.ws?.removeEventListener('open', onOpen)
          this.ws?.removeEventListener('error', onError)
          resolve()
        }

        const onError = (error: Event) => {
          this.ws?.removeEventListener('open', onOpen)
          this.ws?.removeEventListener('error', onError)
          reject(error)
        }

        this.ws.addEventListener('open', onOpen)
        this.ws.addEventListener('error', onError)

        this.setupEventListeners()
      } catch (error) {
        console.error('WebSocket连接失败:', error)
        reject(error)
      }
    })
  }

  private setupEventListeners(): void {
    if (!this.ws) return

    this.ws.onopen = (event) => {
      console.log('WebSocket连接已建立')
      this.reconnectCount = 0
      this.isReconnecting = false
      this.startHeartbeat()
      this.emit('open', event)
    }

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        this.emit('message', data)
      } catch {
        this.emit('message', event.data)
      }
    }

    this.ws.onclose = (event) => {
      console.log('WebSocket连接已关闭')
      this.stopHeartbeat()
      this.emit('close', event)

      if (!event.wasClean && !this.isReconnecting && this.reconnectCount < this.options.maxReconnectAttempts) {
        this.reconnect()
      }
    }

    this.ws.onerror = (error) => {
      console.error('WebSocket错误:', error)
      this.emit('error', error)
    }
  }

  send(data: unknown): boolean {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const message = typeof data === 'object' ? JSON.stringify(data) : String(data)
      this.ws.send(message)
      return true
    } else {
      console.warn('WebSocket未连接，无法发送消息')
      return false
    }
  }

  close(): void {
    this.stopHeartbeat()
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  private reconnect(): void {
    if (this.isReconnecting || this.reconnectCount >= this.options.maxReconnectAttempts) {
      return
    }

    this.isReconnecting = true
    this.reconnectCount++

    console.log(`尝试重连WebSocket (${this.reconnectCount}/${this.options.maxReconnectAttempts})`)

    setTimeout(() => {
      if (this.lastUrl) {
        this.connect(this.lastUrl)
      }
    }, this.options.reconnectInterval)
  }

  private startHeartbeat(): void {
    if (this.options.heartbeatInterval > 0) {
      this.heartbeatTimer = setInterval(() => {
        this.send({ type: 'ping' })
      }, this.options.heartbeatInterval)
    }
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  on(event: string, callback: EventCallback): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, [])
    }
    this.listeners.get(event)!.push(callback)
  }

  off(event: string, callback?: EventCallback): void {
    if (this.listeners.has(event)) {
      if (callback) {
        const callbacks = this.listeners.get(event)!
        const index = callbacks.indexOf(callback)
        if (index > -1) {
          callbacks.splice(index, 1)
        }
      } else {
        this.listeners.set(event, [])
      }
    }
  }

  private emit(event: string, data: unknown): void {
    if (this.listeners.has(event)) {
      this.listeners.get(event)!.forEach(callback => {
        try {
          callback(data)
        } catch (error) {
          console.error('WebSocket事件回调错误:', error)
        }
      })
    }
  }

  getReadyState(): number {
    return this.ws ? this.ws.readyState : WebSocket.CLOSED
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN
  }
}

// 创建 WebSocket 客户端实例
const wsClient = new WebSocketClient()

// 导出初始化函数和便捷方法
export function initWebSocket(
  baseURL: string,
  path?: string,
  params?: Record<string, string>,
  options?: Partial<WebSocketOptions>
): Promise<void> {
  return wsClient.init(baseURL, path, params, options)
}

// 导出便捷方法
export const send = (data: unknown) => wsClient.send(data)
export const close = () => wsClient.close()
export const on = (event: string, callback: EventCallback) => wsClient.on(event, callback)
export const off = (event: string, callback?: EventCallback) => wsClient.off(event, callback)
export const isConnected = () => wsClient.isConnected()

export default wsClient
