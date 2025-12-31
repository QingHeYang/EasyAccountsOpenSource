/**
 * Chat 服务包导出
 */

export { UnifiedMessage } from './UnifiedMessage'
export type {
  MessageRole,
  MessageType,
  ToolStatus,
  StreamType,
  MessageContent,
  ToolInfo,
  AgentInfo,
  MessageMeta,
  UnifiedMessageData
} from './UnifiedMessage'

export { MessageStore, messageStore, useMessageStore } from './messageStore'
export type {
  WSMessage,
  HTTPMessage,
  MessageResult
} from './messageStore'

export { chatService, useChatService } from './chatService'
export type { ConnectionState, ChatConfig } from './chatService'

// 工具解析助手
export {
  toolNameMap,
  toolPrefixMap,
  nonClickableTools,
  navigableTools,
  parseToolData,
  getToolDisplayName,
  getToolExtraInfo,
  isToolClickable,
  isToolNavigable,
  getToolNavigationParams,
  formatToolJson
} from './toolHelper'
export type { FlowsNavigationParams, ToolNavigationResult } from './toolHelper'
