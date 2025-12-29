/**
 * Chat 服务
 * 管理 WebSocket 连接和消息通信
 */
import { ref, computed, type Ref, type ComputedRef } from 'vue'
import { nanoid } from 'nanoid'
import { messageStore, type WSMessage } from './messageStore'

// 连接状态
export type ConnectionState = 'disconnected' | 'connecting' | 'connected' | 'error'

// 连接配置
export interface ChatConfig {
  userId: string
  appId: string
  useThinkLlm: boolean
}

// 默认配置
const DEFAULT_CONFIG: ChatConfig = {
  userId: 'user_67ce21d6-a11c-4340-851b-7a8949906aa3',
  appId: 'easy-accounts-agent',
  useThinkLlm: false
}

class ChatService {
  private ws: WebSocket | null = null
  private config: ChatConfig = { ...DEFAULT_CONFIG }
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectInterval = 3000

  // 响应式状态
  private _connectionState: Ref<ConnectionState> = ref('disconnected')
  private _conversationId: Ref<string> = ref('')
  private _title: Ref<string> = ref('')
  private _questions: Ref<string[]> = ref([])
  private _isStreaming: Ref<boolean> = ref(false)

  // 回调
  private onTitleUpdate?: (title: string) => void
  private onQuestionsUpdate?: (questions: string[]) => void
  private onError?: (error: string) => void

  // Getters
  get connectionState(): ComputedRef<ConnectionState> {
    return computed(() => this._connectionState.value)
  }

  get conversationId(): ComputedRef<string> {
    return computed(() => this._conversationId.value)
  }

  get title(): ComputedRef<string> {
    return computed(() => this._title.value)
  }

  get questions(): ComputedRef<string[]> {
    return computed(() => this._questions.value)
  }

  get isStreaming(): ComputedRef<boolean> {
    return computed(() => this._isStreaming.value)
  }

  get isConnected(): boolean {
    return this._connectionState.value === 'connected'
  }

  // 配置
  setConfig(config: Partial<ChatConfig>): void {
    this.config = { ...this.config, ...config }
  }

  // 设置回调
  setCallbacks(callbacks: {
    onTitleUpdate?: (title: string) => void
    onQuestionsUpdate?: (questions: string[]) => void
    onError?: (error: string) => void
  }): void {
    this.onTitleUpdate = callbacks.onTitleUpdate
    this.onQuestionsUpdate = callbacks.onQuestionsUpdate
    this.onError = callbacks.onError
  }

  // 连接 WebSocket
  connect(conversationId?: string): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        resolve()
        return
      }

      this._connectionState.value = 'connecting'

      // 生成或使用现有会话 ID
      this._conversationId.value = conversationId || nanoid()
      messageStore.setConversationId(this._conversationId.value)

      // 构建 WebSocket URL（直接连接后端）
      const baseUrl = 'ws://www.lllama.cn:10676'
      const wsUrl = `${baseUrl}/ws/chat?user_id=${this.config.userId}&agent_id=${this.config.appId}`

      try {
        this.ws = new WebSocket(wsUrl)

        this.ws.onopen = () => {
          console.log('[ChatService] WebSocket 已连接')
          this._connectionState.value = 'connected'
          this.reconnectAttempts = 0
          resolve()
        }

        this.ws.onmessage = (event) => {
          this.handleMessage(event.data)
        }

        this.ws.onclose = (event) => {
          console.log('[ChatService] WebSocket 已关闭', event.code, event.reason)
          this._connectionState.value = 'disconnected'
          this._isStreaming.value = false

          // 非正常关闭时尝试重连
          if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.scheduleReconnect()
          }
        }

        this.ws.onerror = (error) => {
          console.error('[ChatService] WebSocket 错误', error)
          this._connectionState.value = 'error'
          reject(error)
        }
      } catch (error) {
        console.error('[ChatService] 连接失败', error)
        this._connectionState.value = 'error'
        reject(error)
      }
    })
  }

  // 断开连接
  disconnect(): void {
    this.clearReconnectTimer()
    if (this.ws) {
      this.ws.close(1000, 'User disconnect')
      this.ws = null
    }
    this._connectionState.value = 'disconnected'
    this._isStreaming.value = false
  }

  // 发送消息
  sendMessage(content: string): boolean {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn('[ChatService] WebSocket 未连接，无法发送消息')
      return false
    }

    if (!content.trim()) {
      return false
    }

    // 添加用户消息到 store
    messageStore.addUserMessage(content)

    // 发送到服务器
    const message = {
      conversation_id: this._conversationId.value,
      content: content
    }

    this.ws.send(JSON.stringify(message))
    this._isStreaming.value = true

    return true
  }

  // 停止生成
  stopGeneration(): void {
    messageStore.stopStreaming()
    this._isStreaming.value = false
  }

  // 新建对话
  newConversation(): void {
    messageStore.clearMessages()
    this._conversationId.value = nanoid()
    this._title.value = ''
    this._questions.value = []
    messageStore.setConversationId(this._conversationId.value)
  }

  // 加载历史对话
  loadConversation(conversationId: string): void {
    this._conversationId.value = conversationId
    messageStore.setConversationId(conversationId)
    // 可以在这里添加 HTTP 请求加载历史消息
  }

  // 处理接收到的消息
  private handleMessage(data: string): void {
    try {
      const message: WSMessage = JSON.parse(data)

      // 处理心跳
      if (message.type === 'ping') {
        this.ws?.send(JSON.stringify({ type: 'pong' }))
        return
      }

      // 交给 messageStore 处理
      const result = messageStore.handleWebSocketMessage(message)

      if (result) {
        switch (result.action) {
          case 'exit':
            this._isStreaming.value = false
            break
          case 'title':
            if (result.title) {
              this._title.value = result.title
              this.onTitleUpdate?.(result.title)
            }
            break
          case 'questions':
            if (result.questions) {
              this._questions.value = result.questions
              this.onQuestionsUpdate?.(result.questions)
            }
            break
          case 'error':
            this._isStreaming.value = false
            if (result.message) {
              this.onError?.(result.message.content.text)
            }
            break
        }
      }
    } catch (error) {
      console.error('[ChatService] 消息解析失败', error, data)
    }
  }

  // 计划重连
  private scheduleReconnect(): void {
    this.clearReconnectTimer()
    this.reconnectAttempts++

    console.log(`[ChatService] ${this.reconnectInterval}ms 后尝试重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts})`)

    this.reconnectTimer = setTimeout(() => {
      this.connect(this._conversationId.value).catch(error => {
        console.error('[ChatService] 重连失败', error)
      })
    }, this.reconnectInterval)
  }

  // 清除重连计时器
  private clearReconnectTimer(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
  }
}

// 创建单例
export const chatService = new ChatService()

// Composable for components
export function useChatService() {
  return {
    // 状态
    connectionState: chatService.connectionState,
    conversationId: chatService.conversationId,
    title: chatService.title,
    questions: chatService.questions,
    isStreaming: chatService.isStreaming,
    isConnected: computed(() => chatService.isConnected),

    // 方法
    setConfig: (config: Partial<ChatConfig>) => chatService.setConfig(config),
    setCallbacks: (callbacks: Parameters<typeof chatService.setCallbacks>[0]) =>
      chatService.setCallbacks(callbacks),
    connect: (conversationId?: string) => chatService.connect(conversationId),
    disconnect: () => chatService.disconnect(),
    sendMessage: (content: string) => chatService.sendMessage(content),
    stopGeneration: () => chatService.stopGeneration(),
    newConversation: () => chatService.newConversation(),
    loadConversation: (id: string) => chatService.loadConversation(id)
  }
}
