import { getAiRequest } from './ai-request'

/**
 * AI 消息类型
 */
export interface AiMessage {
  id: string
  role: 'user' | 'assistant' | 'tool'
  content: string
  created_at?: string
  /** 工具调用相关 */
  tool_calls?: AiToolCall[]
  tool_call_id?: string
  name?: string
  /** 思考内容 */
  thinking?: string
}

/**
 * 工具调用
 */
export interface AiToolCall {
  id: string
  type: 'function'
  function: {
    name: string
    arguments: string
  }
}

/**
 * 对话
 */
export interface AiConversation {
  id: string
  title: string
  created_at: string
  updated_at: string
}

/**
 * 对话消息列表响应
 */
export interface AiMessagesResponse {
  messages: AiMessage[]
  has_more: boolean
}

/**
 * AI API
 */
export const aiApi = {
  /**
   * 获取对话列表
   */
  getConversations() {
    return getAiRequest().get<AiConversation[]>('/api/v1/conversations')
  },

  /**
   * 创建新对话
   */
  createConversation() {
    return getAiRequest().post<AiConversation>('/api/v1/conversations')
  },

  /**
   * 删除对话
   */
  deleteConversation(conversationId: string) {
    return getAiRequest().delete(`/api/v1/conversations/${conversationId}`)
  },

  /**
   * 获取对话消息
   */
  getMessages(conversationId: string, limit = 50, before?: string) {
    const params: Record<string, string | number> = { limit }
    if (before) {
      params.before = before
    }
    return getAiRequest().get<AiMessagesResponse>(
      `/api/v1/conversations/${conversationId}/messages`,
      { params }
    )
  },

  /**
   * 更新对话标题
   */
  updateConversationTitle(conversationId: string, title: string) {
    return getAiRequest().patch(`/api/v1/conversations/${conversationId}`, {
      title,
    })
  },
}
