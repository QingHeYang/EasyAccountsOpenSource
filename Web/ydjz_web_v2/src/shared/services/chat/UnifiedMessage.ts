/**
 * 统一消息数据结构
 * 用于统一 HTTP 和 WebSocket 的消息格式
 */

export type MessageRole = 'user' | 'assistant' | 'tool' | 'agent'
export type MessageType = 'text' | 'tool' | 'agent'
export type ToolStatus = 'pending' | 'success' | 'error'
export type StreamType = 'content' | 'reasoning' | ''

export interface MessageContent {
  text: string
  reasoning: string
  isStreaming: boolean
  streamBuffer: string
  streamType: StreamType
  attachments: string[]  // 图片附件文件名列表
}

export interface ToolInfo {
  name: string
  callId: string
  arguments: Record<string, unknown>
  result: string
  status: ToolStatus
  executionTime: number
  completionTime: string
}

export interface AgentInfo {
  agentId: string
  agentConversationId: string
  agentCallId: string
  input: string
  output: string
  status: ToolStatus
  executionTime: number
  completionTime: string
  messages: UnifiedMessage[]
}

export interface MessageMeta {
  tokens: number
  source: 'http' | 'websocket' | 'user' | ''
  wsType: string
  rawData: unknown
}

export interface UnifiedMessageData {
  id?: string
  originalId?: string
  conversationId?: string
  roundId?: string
  timestamp?: string
  role?: MessageRole | ''
  messageType?: MessageType | ''
  content?: Partial<MessageContent>
  tool?: Partial<ToolInfo>
  agent?: Partial<AgentInfo>
  meta?: Partial<MessageMeta>
}

export class UnifiedMessage {
  // 基础标识
  id: string
  originalId: string
  conversationId: string
  roundId: string
  timestamp: string

  // 消息类型和角色
  role: MessageRole | ''
  messageType: MessageType | ''

  // 内容（主要用于 user/assistant 角色）
  content: MessageContent

  // 工具相关（role === 'tool'）
  tool: ToolInfo

  // 子智能体相关（role === 'agent'）
  agent: AgentInfo

  // 元数据
  meta: MessageMeta

  constructor(data: UnifiedMessageData = {}) {
    // 基础标识
    this.id = data.id || ''
    this.originalId = data.originalId || ''
    this.conversationId = data.conversationId || ''
    this.roundId = data.roundId || ''
    this.timestamp = data.timestamp || ''

    // 消息类型和角色
    this.role = data.role || ''
    this.messageType = data.messageType || ''

    // 内容
    this.content = {
      text: data.content?.text || '',
      reasoning: data.content?.reasoning || '',
      isStreaming: data.content?.isStreaming || false,
      streamBuffer: data.content?.streamBuffer || '',
      streamType: data.content?.streamType || '',
      attachments: data.content?.attachments || []
    }

    // 工具相关
    this.tool = {
      name: data.tool?.name || '',
      callId: data.tool?.callId || '',
      arguments: data.tool?.arguments || {},
      result: data.tool?.result || '',
      status: data.tool?.status || 'pending',
      executionTime: data.tool?.executionTime || 0,
      completionTime: data.tool?.completionTime || ''
    }

    // 子智能体相关
    this.agent = {
      agentId: data.agent?.agentId || '',
      agentConversationId: data.agent?.agentConversationId || '',
      agentCallId: data.agent?.agentCallId || '',
      input: data.agent?.input || '',
      output: data.agent?.output || '',
      status: data.agent?.status || 'pending',
      executionTime: data.agent?.executionTime || 0,
      completionTime: data.agent?.completionTime || '',
      messages: data.agent?.messages || []
    }

    // 元数据
    this.meta = {
      tokens: data.meta?.tokens || 0,
      source: data.meta?.source || '',
      wsType: data.meta?.wsType || '',
      rawData: data.meta?.rawData || null
    }
  }

  // 判断是否是流式消息
  get isStreaming(): boolean {
    return this.content.isStreaming
  }

  // 判断是否是工具消息
  get isToolMessage(): boolean {
    return this.role === 'tool'
  }

  // 判断是否是智能体消息
  get isAgentMessage(): boolean {
    return this.role === 'agent'
  }

  // 获取显示文本
  get displayText(): string {
    if (this.role === 'user' || this.role === 'assistant') {
      return this.content.text
    } else if (this.role === 'tool') {
      return this.tool.result || '执行中...'
    } else if (this.role === 'agent') {
      return this.agent.output || '处理中...'
    }
    return ''
  }
}
