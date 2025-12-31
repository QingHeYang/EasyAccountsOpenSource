import { getAiRequest } from './ai-request'

// ==================== 通用响应类型 ====================

/**
 * AI API 通用响应
 */
export interface AiApiResponse<T = unknown> {
  success: boolean
  message: string
  code: number
  data: T
  timestamp: number
}

// ==================== 消息相关类型 ====================

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

// ==================== 对话相关类型 ====================

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
  title?: string
  has_more?: boolean
}

// ==================== 统计相关类型 ====================

/**
 * Token 统计
 */
export interface AiTokenStats {
  total_tokens: number
  prompt_tokens: number
  completion_tokens: number
  reasoning_tokens: number
}

/**
 * MCP 配置
 */
export interface AiMcpConfig {
  enabled: boolean
  transport_mode: string
}

/**
 * AI 统计数据
 */
export interface AiStats {
  token: AiTokenStats
  conversation_count: number
  tool_call_count: number
  mcp: AiMcpConfig
}

// ==================== 健康检查相关类型 ====================

/**
 * LLM 配置状态
 */
export interface AiLlmStatus {
  configured: boolean
  model: string | null
  missing: string[] | null
}

/**
 * 健康检查响应数据
 */
export interface AiHealthData {
  status: 'healthy' | 'degraded'
  service: string
  llm: AiLlmStatus
}

/**
 * 健康检查响应
 */
export interface AiHealthResponse {
  code: number
  message: string
  data: AiHealthData
}

/**
 * AI API
 */
export const aiApi = {
  // ==================== 对话相关 ====================

  /**
   * 获取对话列表
   */
  getConversations() {
    return getAiRequest().get<AiApiResponse<AiConversation[]>>('/api/v1/conversations')
  },

  /**
   * 创建新对话
   */
  createConversation() {
    return getAiRequest().post<AiApiResponse<AiConversation>>('/api/v1/conversations')
  },

  /**
   * 删除对话
   */
  deleteConversation(conversationId: string) {
    return getAiRequest().delete<AiApiResponse>(`/api/v1/conversations/${conversationId}`)
  },

  /**
   * 更新对话标题
   */
  updateConversationTitle(conversationId: string, title: string) {
    return getAiRequest().patch<AiApiResponse>(`/api/v1/conversations/${conversationId}`, {
      title,
    })
  },

  /**
   * 停止对话生成
   * @param conversationId 会话ID
   * @param cascade 是否级联停止子Agent（默认true）
   */
  stopConversation(conversationId: string, cascade = true) {
    return getAiRequest().post<AiApiResponse<{ conversation_id: string; stopped: boolean; cascade: boolean }>>(
      `/api/v1/conversations/stop/${conversationId}`,
      null,
      { params: { cascade } }
    )
  },

  // ==================== 消息相关 ====================

  /**
   * 获取对话消息
   */
  getMessages(conversationId: string, limit = 50, before?: string) {
    const params: Record<string, string | number> = { limit }
    if (before) {
      params.before = before
    }
    return getAiRequest().get<AiApiResponse<AiMessagesResponse>>(
      `/api/v1/conversations/${conversationId}/messages`,
      { params }
    )
  },

  // ==================== 配置/统计相关 ====================

  /**
   * 获取 AI 统计数据
   */
  getStats() {
    return getAiRequest().get<AiApiResponse<AiStats>>('/api/v1/config/stats')
  },

  // ==================== 健康检查 ====================

  /**
   * 检查 AI 服务健康状态
   * 使用原生 fetch 避免 axios 全局错误处理
   */
  async checkHealth(timeout = 5000): Promise<AiHealthResponse | null> {
    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), timeout)

      const baseUrl = window.config?.aiApiUrl || '/ai-api'
      const response = await fetch(`${baseUrl}/health`, {
        method: 'GET',
        signal: controller.signal,
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        return null
      }

      return await response.json()
    } catch {
      // 静默处理，返回 null 表示服务不可用
      return null
    }
  },
}
