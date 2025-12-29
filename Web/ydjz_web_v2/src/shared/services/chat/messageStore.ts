/**
 * 消息存储管理器
 * 提供响应式的消息管理功能
 */
import { reactive, computed } from 'vue'
import { nanoid } from 'nanoid'
import { UnifiedMessage, type UnifiedMessageData } from './UnifiedMessage'

// WebSocket 消息类型定义
export interface WSMessage {
  type: 'chunk' | 'segment' | 'tool_call' | 'tool_response' | 'start' | 'exit' | 'error' | 'title' | 'question' | 'ping' | 'pong'
  conversation_id?: string
  text?: string
  status?: boolean
  object?: {
    content_type?: 'reasoning' | 'content'
    tool_name?: string
    tool_call_id?: string
    tool_arguments?: Record<string, unknown>
    tool_response?: string
    reasoning_content?: string
    questions?: string[]
  }
  agent?: {
    agent_id?: string
    agent_conversation_id?: string
  }
}

// HTTP 消息类型定义
export interface HTTPMessage {
  message_id?: string
  round_id?: string
  timestamp?: string
  token?: number
  role: 'user' | 'assistant' | 'tool' | 'agent'
  text?: {
    content?: string
    reasoning_content?: string
  }
  tool?: {
    tool_name?: string
    tool_call_id?: string
    tool_arguments?: Record<string, unknown>
    tool_result?: string
    tool_status?: number
    execution_time?: number
    completion_time?: string
  }
  sub_agent?: {
    agent_id?: string
    agent_conversation_id?: string
    agent_call_id?: string
    agent_input?: string
    agent_output?: string
    agent_status?: boolean
    execution_time?: number
    completion_time?: string
  }
}

// 消息处理结果
export interface MessageResult {
  action: 'create' | 'update' | 'exit' | 'error' | 'title' | 'questions' | 'sub_message'
  message?: UnifiedMessage
  conversationId?: string
  title?: string
  questions?: string[]
}

// 状态类型
interface MessageStoreState {
  mainMessages: UnifiedMessage[]
  agentMessageQueues: Record<string, UnifiedMessage[]>
  pendingMessages: Record<string, UnifiedMessage>
  currentConversationId: string
  isLoading: boolean
  streamingMessageId: string | null
}

class MessageStore {
  state: MessageStoreState

  constructor() {
    this.state = reactive({
      mainMessages: [],
      agentMessageQueues: {},
      pendingMessages: {},
      currentConversationId: '',
      isLoading: false,
      streamingMessageId: null
    })
  }

  // 计算属性 - 获取当前流式消息
  get streamingMessage(): UnifiedMessage | null {
    if (!this.state.streamingMessageId) return null
    return this.state.mainMessages.find(msg => msg.id === this.state.streamingMessageId) || null
  }

  // 计算属性 - 获取最新消息
  get latestMessage(): UnifiedMessage | undefined {
    return this.state.mainMessages[this.state.mainMessages.length - 1]
  }

  // 设置当前会话ID
  setConversationId(conversationId: string): void {
    this.state.currentConversationId = conversationId
  }

  // 从HTTP数据创建消息
  createFromHTTP(httpMessage: HTTPMessage): UnifiedMessage {
    const msgData: UnifiedMessageData = {
      id: nanoid(),
      originalId: httpMessage.message_id,
      conversationId: this.state.currentConversationId,
      roundId: httpMessage.round_id,
      timestamp: httpMessage.timestamp,
      meta: {
        source: 'http',
        rawData: httpMessage,
        tokens: httpMessage.token || 0
      }
    }

    // 根据角色处理
    if (httpMessage.role === 'user') {
      msgData.role = 'user'
      msgData.messageType = 'text'
      msgData.content = {
        text: httpMessage.text?.content || '',
        reasoning: httpMessage.text?.reasoning_content || ''
      }
    } else if (httpMessage.role === 'assistant') {
      msgData.role = 'assistant'
      msgData.messageType = 'text'
      msgData.content = {
        text: httpMessage.text?.content || '',
        reasoning: httpMessage.text?.reasoning_content || ''
      }
    } else if (httpMessage.role === 'tool') {
      msgData.role = 'tool'
      msgData.messageType = 'tool'
      msgData.tool = {
        name: httpMessage.tool?.tool_name || '',
        callId: httpMessage.tool?.tool_call_id || '',
        arguments: httpMessage.tool?.tool_arguments || {},
        result: httpMessage.tool?.tool_result || '',
        status: httpMessage.tool?.tool_status === 1 ? 'success' : 'error',
        executionTime: httpMessage.tool?.execution_time || 0,
        completionTime: httpMessage.tool?.completion_time || ''
      }
    } else if (httpMessage.role === 'agent') {
      msgData.role = 'agent'
      msgData.messageType = 'agent'
      msgData.agent = {
        agentId: httpMessage.sub_agent?.agent_id || '',
        agentConversationId: httpMessage.sub_agent?.agent_conversation_id || '',
        agentCallId: httpMessage.sub_agent?.agent_call_id || '',
        input: httpMessage.sub_agent?.agent_input || '',
        output: httpMessage.sub_agent?.agent_output || '',
        status: httpMessage.sub_agent?.agent_status ? 'success' : 'error',
        executionTime: httpMessage.sub_agent?.execution_time || 0,
        completionTime: httpMessage.sub_agent?.completion_time || '',
        messages: []
      }
    }

    return reactive(new UnifiedMessage(msgData)) as UnifiedMessage
  }

  // 从HTTP数据批量添加消息
  loadHTTPMessages(httpMessages: HTTPMessage[]): void {
    this.state.isLoading = true

    // 清空现有消息
    this.state.mainMessages.length = 0

    // 如果消息列表不为空，反转数组（API返回的是倒序）
    const messages = httpMessages && httpMessages.length > 0
      ? [...httpMessages].reverse()
      : []

    // 批量转换并添加
    messages.forEach(httpMsg => {
      const msg = this.createFromHTTP(httpMsg)
      this.state.mainMessages.push(msg)
    })

    this.state.isLoading = false
  }

  // 处理WebSocket消息
  handleWebSocketMessage(wsMessage: WSMessage): MessageResult | null {
    const { agent } = wsMessage

    // 如果没有agent字段，处理主智能体消息
    if (!agent) {
      return this.handleMainAgentMessage(wsMessage)
    } else {
      // 处理子智能体消息
      return this.handleSubAgentMessage(wsMessage)
    }
  }

  // 处理主智能体消息
  private handleMainAgentMessage(wsMessage: WSMessage): MessageResult | null {
    const { type } = wsMessage

    switch (type) {
      case 'chunk':
        return this.handleChunk(wsMessage)
      case 'segment':
        return this.handleSegment(wsMessage)
      case 'tool_call':
        return this.handleToolCall(wsMessage)
      case 'tool_response':
        return this.handleToolResponse(wsMessage)
      case 'exit':
        return this.handleExit()
      case 'error':
        return this.handleError(wsMessage)
      case 'title':
        return this.handleTitle(wsMessage)
      case 'question':
        return this.handleQuestion(wsMessage)
      case 'ping':
      case 'pong':
        return null
      default:
        console.warn('Unknown message type:', type)
        return null
    }
  }

  // 处理流式文本
  private handleChunk(wsMessage: WSMessage): MessageResult {
    let currentMsg = this.streamingMessage

    if (!currentMsg) {
      const msgData: UnifiedMessageData = {
        id: nanoid(),
        conversationId: wsMessage.conversation_id,
        timestamp: new Date().toISOString(),
        role: 'assistant',
        messageType: 'text',
        content: {
          text: '',
          reasoning: '',
          isStreaming: true,
          streamBuffer: ''
        },
        meta: {
          source: 'websocket',
          wsType: 'chunk'
        }
      }

      currentMsg = reactive(new UnifiedMessage(msgData)) as UnifiedMessage
      this.state.mainMessages.push(currentMsg)
      this.state.streamingMessageId = currentMsg.id
    }

    // 根据内容类型拼接
    const contentType = wsMessage.object?.content_type
    if (contentType === 'reasoning') {
      currentMsg.content.reasoning += wsMessage.text || ''
      currentMsg.content.streamType = 'reasoning'
    } else {
      currentMsg.content.text += wsMessage.text || ''
      currentMsg.content.streamType = 'content'
    }
    currentMsg.content.streamBuffer += wsMessage.text || ''

    return { action: 'update', message: currentMsg }
  }

  // 处理完整段落
  private handleSegment(wsMessage: WSMessage): MessageResult {
    let currentMsg = this.streamingMessage

    if (currentMsg) {
      currentMsg.content.text = wsMessage.text || ''
      currentMsg.content.reasoning = wsMessage.object?.reasoning_content || ''
      currentMsg.content.isStreaming = false
      currentMsg.content.streamBuffer = ''
      this.state.streamingMessageId = null
    } else {
      const msgData: UnifiedMessageData = {
        id: nanoid(),
        conversationId: wsMessage.conversation_id,
        timestamp: new Date().toISOString(),
        role: 'assistant',
        messageType: 'text',
        content: {
          text: wsMessage.text || '',
          reasoning: wsMessage.object?.reasoning_content || ''
        },
        meta: {
          source: 'websocket',
          wsType: 'segment'
        }
      }

      currentMsg = reactive(new UnifiedMessage(msgData)) as UnifiedMessage
      this.state.mainMessages.push(currentMsg)
    }

    return { action: 'update', message: currentMsg }
  }

  // 添加用户消息
  addUserMessage(text: string): UnifiedMessage {
    const msgData: UnifiedMessageData = {
      id: nanoid(),
      conversationId: this.state.currentConversationId,
      timestamp: new Date().toISOString(),
      role: 'user',
      messageType: 'text',
      content: { text },
      meta: { source: 'user' }
    }

    const msg = reactive(new UnifiedMessage(msgData)) as UnifiedMessage
    this.state.mainMessages.push(msg)
    return msg
  }

  // 处理工具调用
  private handleToolCall(wsMessage: WSMessage): MessageResult {
    const msgData: UnifiedMessageData = {
      id: nanoid(),
      conversationId: wsMessage.conversation_id,
      timestamp: new Date().toISOString(),
      role: 'tool',
      messageType: 'tool',
      tool: {
        name: wsMessage.object?.tool_name || '',
        callId: wsMessage.object?.tool_call_id || '',
        arguments: wsMessage.object?.tool_arguments || {},
        status: 'pending'
      },
      meta: {
        source: 'websocket',
        wsType: 'tool_call'
      }
    }

    const msg = reactive(new UnifiedMessage(msgData)) as UnifiedMessage
    this.state.pendingMessages[msg.tool.callId] = msg
    this.state.mainMessages.push(msg)

    return { action: 'create', message: msg }
  }

  // 更新工具响应
  private handleToolResponse(wsMessage: WSMessage): MessageResult | null {
    const callId = wsMessage.object?.tool_call_id || ''
    const pendingMsg = this.state.pendingMessages[callId]

    if (pendingMsg) {
      pendingMsg.tool.result = wsMessage.object?.tool_response || ''
      pendingMsg.tool.status = wsMessage.status ? 'success' : 'error'
      pendingMsg.tool.completionTime = new Date().toISOString()

      delete this.state.pendingMessages[callId]

      return { action: 'update', message: pendingMsg }
    }

    return null
  }

  // 处理子智能体消息
  private handleSubAgentMessage(wsMessage: WSMessage): MessageResult | null {
    const { type, agent } = wsMessage
    const agentConvId = agent?.agent_conversation_id || ''

    // 确保子队列存在
    if (!this.state.agentMessageQueues[agentConvId]) {
      this.state.agentMessageQueues[agentConvId] = reactive([])
    }

    if (type === 'start') {
      const msgData: UnifiedMessageData = {
        id: nanoid(),
        conversationId: wsMessage.conversation_id,
        timestamp: new Date().toISOString(),
        role: 'agent',
        messageType: 'agent',
        agent: {
          agentId: agent?.agent_id || '',
          agentConversationId: agentConvId,
          input: wsMessage.text || '',
          status: 'pending'
        },
        meta: {
          source: 'websocket',
          wsType: 'start'
        }
      }

      const msg = reactive(new UnifiedMessage(msgData)) as UnifiedMessage
      this.state.pendingMessages[agentConvId] = msg
      this.state.mainMessages.push(msg)

      return { action: 'create', message: msg }
    } else if (type === 'exit') {
      const pendingMsg = this.state.pendingMessages[agentConvId]
      if (pendingMsg) {
        pendingMsg.agent.output = wsMessage.text || '调用完成'
        pendingMsg.agent.status = 'success'
        pendingMsg.agent.completionTime = new Date().toISOString()
        pendingMsg.agent.messages = [...this.state.agentMessageQueues[agentConvId]]

        delete this.state.pendingMessages[agentConvId]
        return { action: 'update', message: pendingMsg }
      }
    } else {
      // 其他子智能体消息
      if (type === 'tool_call') {
        const subMsg = this.createSubAgentMessage(wsMessage)
        this.state.pendingMessages[subMsg.tool.callId] = subMsg
        this.state.agentMessageQueues[agentConvId].push(subMsg)
        return { action: 'sub_message', conversationId: agentConvId, message: subMsg }
      } else if (type === 'tool_response') {
        const callId = wsMessage.object?.tool_call_id || ''
        const pendingMsg = this.state.pendingMessages[callId]

        if (pendingMsg) {
          pendingMsg.tool.result = wsMessage.object?.tool_response || ''
          pendingMsg.tool.status = wsMessage.status ? 'success' : 'error'
          pendingMsg.tool.completionTime = new Date().toISOString()

          delete this.state.pendingMessages[callId]
          return { action: 'sub_message', conversationId: agentConvId, message: pendingMsg }
        } else {
          const subMsg = this.createSubAgentMessage(wsMessage)
          this.state.agentMessageQueues[agentConvId].push(subMsg)
          return { action: 'sub_message', conversationId: agentConvId, message: subMsg }
        }
      } else {
        const subMsg = this.createSubAgentMessage(wsMessage)
        this.state.agentMessageQueues[agentConvId].push(subMsg)
        return { action: 'sub_message', conversationId: agentConvId, message: subMsg }
      }
    }

    return null
  }

  // 创建子智能体消息
  private createSubAgentMessage(wsMessage: WSMessage): UnifiedMessage {
    const msgData: UnifiedMessageData = {
      id: nanoid(),
      conversationId: wsMessage.agent?.agent_conversation_id || '',
      timestamp: new Date().toISOString(),
      meta: {
        source: 'websocket',
        rawData: wsMessage,
        wsType: wsMessage.type
      }
    }

    if (wsMessage.type === 'chunk' || wsMessage.type === 'segment') {
      msgData.role = 'assistant'
      msgData.messageType = 'text'
      msgData.content = {
        text: wsMessage.text || '',
        reasoning: wsMessage.object?.reasoning_content || ''
      }
    } else if (wsMessage.type === 'tool_call') {
      msgData.role = 'tool'
      msgData.messageType = 'tool'
      msgData.tool = {
        name: wsMessage.object?.tool_name || '',
        callId: wsMessage.object?.tool_call_id || '',
        arguments: wsMessage.object?.tool_arguments || {},
        status: 'pending'
      }
    } else if (wsMessage.type === 'tool_response') {
      msgData.role = 'tool'
      msgData.messageType = 'tool'
      msgData.tool = {
        name: wsMessage.object?.tool_name || '',
        callId: wsMessage.object?.tool_call_id || '',
        result: wsMessage.object?.tool_response || '',
        status: wsMessage.status ? 'success' : 'error',
        completionTime: new Date().toISOString()
      }
    }

    return reactive(new UnifiedMessage(msgData)) as UnifiedMessage
  }

  // 处理退出消息
  private handleExit(): MessageResult {
    this.state.streamingMessageId = null
    return { action: 'exit' }
  }

  // 处理错误消息
  private handleError(wsMessage: WSMessage): MessageResult {
    const msgData: UnifiedMessageData = {
      id: nanoid(),
      conversationId: wsMessage.conversation_id,
      timestamp: new Date().toISOString(),
      role: 'assistant',
      messageType: 'text',
      content: {
        text: `错误：${wsMessage.text || '未知错误'}`
      },
      meta: {
        source: 'websocket',
        wsType: 'error',
        rawData: wsMessage
      }
    }

    const msg = reactive(new UnifiedMessage(msgData)) as UnifiedMessage
    this.state.mainMessages.push(msg)

    return { action: 'error', message: msg }
  }

  // 处理标题更新
  private handleTitle(wsMessage: WSMessage): MessageResult {
    return { action: 'title', title: wsMessage.text || '' }
  }

  // 处理问题建议
  private handleQuestion(wsMessage: WSMessage): MessageResult {
    return { action: 'questions', questions: wsMessage.object?.questions || [] }
  }

  // 清空消息
  clearMessages(): void {
    this.state.mainMessages.length = 0
    Object.keys(this.state.agentMessageQueues).forEach(key => {
      delete this.state.agentMessageQueues[key]
    })
    Object.keys(this.state.pendingMessages).forEach(key => {
      delete this.state.pendingMessages[key]
    })
    this.state.streamingMessageId = null
    this.state.currentConversationId = ''
  }

  // 停止流式输出
  stopStreaming(): void {
    if (this.state.streamingMessageId) {
      const streamingMsg = this.state.mainMessages.find(msg => msg.id === this.state.streamingMessageId)
      if (streamingMsg && streamingMsg.content) {
        streamingMsg.content.isStreaming = false
        streamingMsg.content.streamType = ''
      }
      this.state.streamingMessageId = null
    }
  }

  // 导出响应式的 getter
  get mainMessages(): UnifiedMessage[] {
    return this.state.mainMessages
  }

  get agentQueues(): Record<string, UnifiedMessage[]> {
    return this.state.agentMessageQueues
  }

  getAgentMessages(agentConvId: string): UnifiedMessage[] {
    return this.state.agentMessageQueues[agentConvId] || []
  }
}

// 导出类以便创建新实例
export { MessageStore }

// 创建单例
export const messageStore = new MessageStore()

// 在组件中使用的 composable
export function useMessageStore() {
  return {
    // 响应式状态
    mainMessages: computed(() => messageStore.mainMessages),
    streamingMessage: computed(() => messageStore.streamingMessage),
    latestMessage: computed(() => messageStore.latestMessage),
    isLoading: computed(() => messageStore.state.isLoading),

    // 方法
    setConversationId: (id: string) => messageStore.setConversationId(id),
    loadHTTPMessages: (messages: HTTPMessage[]) => messageStore.loadHTTPMessages(messages),
    addUserMessage: (text: string) => messageStore.addUserMessage(text),
    handleWebSocketMessage: (msg: WSMessage) => messageStore.handleWebSocketMessage(msg),
    clearMessages: () => messageStore.clearMessages(),
    stopStreaming: () => messageStore.stopStreaming(),
    getAgentMessages: (id: string) => messageStore.getAgentMessages(id)
  }
}
