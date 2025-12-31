/**
 * Chat 服务
 * 管理 WebSocket 连接和消息通信
 */
import { ref, computed, type Ref, type ComputedRef } from 'vue'
import { messageStore, type WSMessage, type HTTPMessage } from './messageStore'
import { aiApi } from '../../api/ai'

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

      // 使用现有会话 ID（新对话时不设置，等服务端返回）
      this._conversationId.value = conversationId || ''
      messageStore.setConversationId(this._conversationId.value)

      // 构建 WebSocket URL（直接连接后端）
      const baseUrl = 'ws://localhost:8001'

      // 从 localStorage 获取 token，用于工具调用认证
      const token = localStorage.getItem('token') || ''
      const toolTokens = token ? `Authorization=${token}` : ''

      const wsUrl = `${baseUrl}/ws/chat?user_id=${this.config.userId}&agent_id=${this.config.appId}&use_think_llm=${this.config.useThinkLlm}&tool_tokens=${encodeURIComponent(toolTokens)}`

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
  sendMessage(content: string, attachments?: string[]): boolean {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn('[ChatService] WebSocket 未连接，无法发送消息')
      return false
    }

    if (!content.trim()) {
      return false
    }

    // 添加用户消息到 store
    messageStore.addUserMessage(content, attachments)

    // 发送到服务器
    const message: {
      conversation_id: string
      content: string
      use_think_llm: boolean
      attachments?: Array<{ filename: string }>
    } = {
      conversation_id: this._conversationId.value,
      content: content,
      use_think_llm: this.config.useThinkLlm
    }

    // 添加附件（如果有）
    if (attachments && attachments.length > 0) {
      message.attachments = attachments.map(filename => ({ filename }))
    }

    this.ws.send(JSON.stringify(message))
    this._isStreaming.value = true

    return true
  }

  // 停止生成（仅本地状态）
  stopGeneration(): void {
    messageStore.stopStreaming()
    this._isStreaming.value = false
  }

  // 停止对话（调用后端接口 + 断开重连）
  async stopConversation(): Promise<boolean> {
    const conversationId = this._conversationId.value
    if (!conversationId) {
      console.warn('[ChatService] 没有会话ID，无法停止')
      return false
    }

    try {
      // 1. 调用后端停止接口
      const response = await aiApi.stopConversation(conversationId, true)

      if (response.data?.success || response.data?.data?.stopped) {
        console.log('[ChatService] 停止成功，断开重连 WebSocket')

        // 2. 停止本地流式状态
        this.stopGeneration()

        // 3. 断开 WebSocket
        this.disconnect()

        // 4. 重新连接（保持当前会话）
        await this.connect(conversationId)

        return true
      } else {
        console.warn('[ChatService] 停止失败', response.data)
        return false
      }
    } catch (error) {
      console.error('[ChatService] 停止请求失败', error)
      // 即使请求失败，也尝试断开重连
      this.stopGeneration()
      this.disconnect()
      await this.connect(conversationId)
      return false
    }
  }

  // 新建对话
  newConversation(): void {
    messageStore.clearMessages()
    this._conversationId.value = ''  // 新对话不设置 ID，等服务端返回
    this._title.value = ''
    this._questions.value = []
    messageStore.setConversationId(this._conversationId.value)
    // 清除本地存储的会话 ID
    localStorage.removeItem('ai_conversation_id')
  }

  // 保存会话 ID 到本地
  private saveConversationId(conversationId: string): void {
    if (conversationId) {
      localStorage.setItem('ai_conversation_id', conversationId)
    }
  }

  // 获取本地保存的会话 ID
  getSavedConversationId(): string | null {
    return localStorage.getItem('ai_conversation_id')
  }

  // 加载历史对话
  async loadConversation(conversationId: string): Promise<void> {
    this._conversationId.value = conversationId
    messageStore.setConversationId(conversationId)
    this.saveConversationId(conversationId)

    // 加载历史消息
    await this.loadHistoryMessages(conversationId)
  }

  // 加载历史消息
  async loadHistoryMessages(conversationId: string): Promise<void> {
    if (!conversationId) return

    try {
      const response = await aiApi.getMessages(conversationId)

      if (response.data?.success && response.data.data?.messages) {
        // 转换消息类型（AiMessage -> HTTPMessage）
        messageStore.loadHTTPMessages(response.data.data.messages as unknown as HTTPMessage[])
        // 更新标题（忽略"未命名会话"）
        if (response.data.data.title && response.data.data.title !== '未命名会话') {
          this._title.value = response.data.data.title
        }
      }
    } catch (error) {
      console.error('[ChatService] 加载历史消息失败', error)
      // 如果是 404，说明会话不存在，清除本地存储
      if ((error as { response?: { status?: number } }).response?.status === 404) {
        localStorage.removeItem('ai_conversation_id')
        this._conversationId.value = ''
      }
    }
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

      // 更新并保存会话 ID（服务端可能返回新的会话 ID）
      if (message.conversation_id && message.conversation_id !== this._conversationId.value) {
        this._conversationId.value = message.conversation_id
        messageStore.setConversationId(message.conversation_id)
        this.saveConversationId(message.conversation_id)
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
    sendMessage: (content: string, attachments?: string[]) => chatService.sendMessage(content, attachments),
    stopGeneration: () => chatService.stopGeneration(),
    stopConversation: () => chatService.stopConversation(),
    newConversation: () => chatService.newConversation(),
    loadConversation: (id: string) => chatService.loadConversation(id),
    loadHistoryMessages: (id: string) => chatService.loadHistoryMessages(id),
    getSavedConversationId: () => chatService.getSavedConversationId()
  }
}
