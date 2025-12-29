import { getAiWebSocketUrl } from '../api/ai-request'

/**
 * WebSocket 消息类型
 */
export type AiWsMessageType =
  | 'chunk' // 文本片段
  | 'segment' // 完整段落
  | 'tool_call' // 工具调用
  | 'tool_response' // 工具响应
  | 'title' // 对话标题
  | 'exit' // 结束
  | 'error' // 错误

/**
 * WebSocket 消息
 */
export interface AiWsMessage {
  type: AiWsMessageType
  content?: string
  tool_call_id?: string
  tool_name?: string
  tool_args?: string
  tool_result?: string
  title?: string
  error?: string
  /** 思考内容（think mode） */
  thinking?: string
}

/**
 * WebSocket 管理器配置
 */
export interface AiWsManagerOptions {
  /** 用户 ID */
  userId: string
  /** 应用 ID */
  appId?: string
  /** 是否使用思考模式 */
  useThinkLlm?: boolean
  /** 自动重连 */
  autoReconnect?: boolean
  /** 最大重连次数 */
  maxReconnectAttempts?: number
  /** 重连基础延迟（毫秒） */
  reconnectBaseDelay?: number
  /** 消息回调 */
  onMessage?: (message: AiWsMessage) => void
  /** 连接成功回调 */
  onConnect?: () => void
  /** 断开连接回调 */
  onDisconnect?: (code?: number, reason?: string) => void
  /** 错误回调 */
  onError?: (error: Event) => void
}

/**
 * AI WebSocket 管理器
 */
export class AiWsManager {
  private ws: WebSocket | null = null
  private options: AiWsManagerOptions
  private reconnectAttempts = 0
  private reconnectTimer: number | null = null
  private isManualClose = false
  private currentConversationId: string | null = null

  constructor(options: AiWsManagerOptions) {
    this.options = {
      appId: 'easy-accounts-agent',
      useThinkLlm: false,
      autoReconnect: true,
      maxReconnectAttempts: 5,
      reconnectBaseDelay: 1000,
      ...options,
    }
  }

  /**
   * 连接 WebSocket
   */
  connect(conversationId?: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.warn('WebSocket already connected')
      return
    }

    this.isManualClose = false
    this.currentConversationId = conversationId || null

    const baseUrl = getAiWebSocketUrl()
    const params = new URLSearchParams({
      user_id: this.options.userId,
      app_id: this.options.appId!,
      use_think_llm: String(this.options.useThinkLlm),
    })

    if (conversationId) {
      params.set('conversation_id', conversationId)
    }

    const url = `${baseUrl}/ws/chat?${params.toString()}`

    try {
      this.ws = new WebSocket(url)
      this.setupEventHandlers()
    } catch (error) {
      console.error('WebSocket connection error:', error)
      this.options.onError?.(error as Event)
    }
  }

  /**
   * 断开连接
   */
  disconnect(): void {
    this.isManualClose = true
    this.clearReconnectTimer()

    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  /**
   * 发送消息
   */
  send(message: string): boolean {
    if (this.ws?.readyState !== WebSocket.OPEN) {
      console.warn('WebSocket not connected')
      return false
    }

    try {
      this.ws.send(JSON.stringify({ content: message }))
      return true
    } catch (error) {
      console.error('WebSocket send error:', error)
      return false
    }
  }

  /**
   * 获取连接状态
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }

  /**
   * 获取当前对话 ID
   */
  getConversationId(): string | null {
    return this.currentConversationId
  }

  /**
   * 设置事件处理器
   */
  private setupEventHandlers(): void {
    if (!this.ws) return

    this.ws.onopen = () => {
      console.log('WebSocket connected')
      this.reconnectAttempts = 0
      this.options.onConnect?.()
    }

    this.ws.onclose = (event) => {
      console.log('WebSocket disconnected:', event.code, event.reason)
      this.options.onDisconnect?.(event.code, event.reason)

      if (!this.isManualClose && this.options.autoReconnect) {
        this.scheduleReconnect()
      }
    }

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      this.options.onError?.(error)
    }

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as AiWsMessage
        this.options.onMessage?.(message)
      } catch (error) {
        console.error('WebSocket message parse error:', error)
      }
    }
  }

  /**
   * 安排重连
   */
  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.options.maxReconnectAttempts!) {
      console.warn('Max reconnect attempts reached')
      return
    }

    // 指数退避
    const delay = this.options.reconnectBaseDelay! * Math.pow(2, this.reconnectAttempts)
    this.reconnectAttempts++

    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`)

    this.reconnectTimer = window.setTimeout(() => {
      this.connect(this.currentConversationId || undefined)
    }, delay)
  }

  /**
   * 清除重连定时器
   */
  private clearReconnectTimer(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
  }

  /**
   * 更新配置
   */
  updateOptions(options: Partial<AiWsManagerOptions>): void {
    this.options = { ...this.options, ...options }
  }
}

/**
 * 创建 WebSocket 管理器实例
 */
export function createAiWsManager(options: AiWsManagerOptions): AiWsManager {
  return new AiWsManager(options)
}
