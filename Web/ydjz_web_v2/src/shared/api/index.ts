// 请求工具
export { setupRequest, getRequest, ApiError, isAuthError, isHandledError } from './request'
export type { RequestOptions } from './request'

// AI 请求工具
export { setupAiRequest, getAiRequest, getAiWebSocketUrl } from './ai-request'
export type { AiRequestOptions } from './ai-request'

// API 模块
export { authApi } from './auth'
export { accountApi } from './account'
export { actionApi } from './action'
export { typeApi } from './type'
export { flowApi } from './flow'
export { homeApi } from './home'
export { screenApi } from './screen'
export { tagApi } from './tag'
export { templateApi } from './template'
export { imageApi } from './image'
export { analysisApi } from './analysis'
export { aiApi } from './ai'
export { backupApi } from './backup'

// 类型导出
export type { LoginParams, LoginResult } from './auth'
export type { Account, AccountParams, AddAccountParams, UpdateAccountParams } from './account'
export type { Action, ActionParams, ActionHandle } from './action'
export type { Type, TypeWithChildren, TypeParams } from './type'
export type { Flow, FlowDetail, FlowListResult, FlowTypeDto, FlowParams, AddFlowParams, FlowHandle } from './flow'
export type { HomeInfo, HomeAccount, HomeMonthDetail, VersionInfo, UpdateInfo, AuthConfig, BackupConfig, SystemConfig } from './home'
export type { ScreenFlowParams } from './screen'
export type { Tag, TagParams } from './tag'
export type { Template, TemplateParams } from './template'
export type { UploadImageResult } from './image'
export type {
  AnalysisTypeItem,
  AnalysisTypeListResult,
  AnalysisTypeListParams,
  MonthData,
  YearData,
  AnalysisTypeMonthResult,
  AnalysisTypeMonthParams,
} from './analysis'
export type {
  AiMessage,
  AiToolCall,
  AiConversation,
  AiMessagesResponse,
} from './ai'
