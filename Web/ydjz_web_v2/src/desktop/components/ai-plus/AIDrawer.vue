<script setup lang="ts">
import { ref, watch, nextTick, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import {
  ChatLineSquare,
  Close,
  Loading,
  ArrowDown,
  ArrowRight,
  Refresh,
  DocumentCopy,
  CircleCheck,
  CircleClose
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import MarkdownIt from 'markdown-it'
import {
  useChatService,
  useMessageStore,
  type UnifiedMessage,
  // 工具助手
  getToolDisplayName,
  getToolExtraInfo,
  isToolClickable,
  isToolNavigable,
  getToolNavigationParams,
  formatToolJson,
  parseToolData
} from '@shared/services/chat'
import { setScreenParams } from '@shared/services/screenParams'

const props = withDefaults(defineProps<{
  modelValue: boolean
}>(), {
  modelValue: false
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

// Markdown 渲染器
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  breaks: true
})

// Chat 服务
const {
  connectionState,
  isStreaming,
  title,
  connect,
  disconnect,
  sendMessage: sendChatMessage,
  newConversation,
  loadConversation,
  loadHistoryMessages,
  getSavedConversationId
} = useChatService()

// 消息存储
const { mainMessages } = useMessageStore()

// 路由
const router = useRouter()

// 本地状态
const inputText = ref('')
const messagesContainer = ref<HTMLElement | null>(null)
const sending = ref(false)

// 思维链展开状态（记录每个消息ID是否展开）
const reasoningExpanded = ref<Record<string, boolean>>({})

// 工具详情弹窗
const toolDetailVisible = ref(false)
const currentToolDetail = ref<{
  name: string
  status: 'pending' | 'success' | 'error'
  arguments: Record<string, unknown>
  result: string
}>({
  name: '',
  status: 'pending',
  arguments: {},
  result: ''
})

// 抽屉打开时连接 WebSocket 并加载历史
watch(() => props.modelValue, async (isOpen) => {
  if (isOpen && connectionState.value !== 'connected') {
    try {
      const savedId = getSavedConversationId()
      await connect(savedId || undefined)
      console.log('[AIDrawer] WebSocket 已连接')

      // 如果有保存的会话 ID，加载历史消息
      if (savedId) {
        await loadHistoryMessages(savedId)
        console.log('[AIDrawer] 历史消息已加载')
      }
    } catch (error) {
      console.error('[AIDrawer] WebSocket 连接失败', error)
    }
  }
}, { immediate: true })

// 消息变化时滚动到底部
watch(mainMessages, () => {
  scrollToBottom()
}, { deep: true })

// 组件卸载时断开连接
onUnmounted(() => {
  disconnect()
})

// 滚动到底部
function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

// 关闭抽屉
function close() {
  emit('update:modelValue', false)
}

// 发送消息
async function handleSend() {
  if (!inputText.value.trim() || sending.value || isStreaming.value) return

  const content = inputText.value.trim()
  sending.value = true

  try {
    const success = sendChatMessage(content)
    if (success) {
      inputText.value = ''
    } else {
      ElMessage.error('发送失败，请检查连接状态')
    }
  } finally {
    sending.value = false
  }
}

// 键盘事件
function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

// 新建对话
function handleNewConversation() {
  newConversation()  // 会自动清除 localStorage 和消息
  reasoningExpanded.value = {}
  ElMessage.success('已开启新对话')
}

// 重新连接
async function handleReconnect() {
  if (connectionState.value === 'connecting') return

  try {
    disconnect()
    await connect()
    ElMessage.success('重连成功')
  } catch {
    ElMessage.error('重连失败')
  }
}

// 切换思维链展开
function toggleReasoning(msgId: string) {
  reasoningExpanded.value[msgId] = !reasoningExpanded.value[msgId]
}

// 判断思维链是否展开
function isReasoningExpanded(msgId: string): boolean {
  return reasoningExpanded.value[msgId] || false
}


// 处理工具点击
function handleToolClick(msg: UnifiedMessage) {
  const toolName = msg.tool.name

  // 不可点击的工具（且不可跳转）直接返回
  if (!isToolClickable(toolName)) return

  // 可跳转的工具
  if (isToolNavigable(toolName)) {
    navigateFromTool(msg)
    return
  }

  // 其他工具显示详情弹窗
  showToolDetail(msg)
}

// 从工具跳转到对应页面
function navigateFromTool(msg: UnifiedMessage) {
  const navResult = getToolNavigationParams(msg)

  if (!navResult) return

  if (navResult.type === 'flows' && navResult.params) {
    // 设置筛选参数
    setScreenParams(navResult.params)
    // 跳转到筛选页面（添加时间戳确保路由变化被检测）
    router.push(`${navResult.route}&_t=${Date.now()}`)
  }
}

// 显示工具详情
function showToolDetail(msg: UnifiedMessage) {
  currentToolDetail.value = {
    name: msg.tool.name,
    status: msg.tool.status,
    arguments: msg.tool.arguments,
    result: msg.tool.result
  }
  toolDetailVisible.value = true
}


// 复制文本
async function copyText(text: string) {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制')
  } catch {
    ElMessage.error('复制失败')
  }
}

// 渲染 Markdown
function renderMarkdown(text: string): string {
  if (!text) return ''
  let html = md.render(text)

  // 为表格添加滚动容器
  html = html.replace(/<table([^>]*)>/g, '<div class="table-wrapper"><table$1>')
  html = html.replace(/<\/table>/g, '</table></div>')

  return html
}

// 格式化时间
function formatTime(timestamp: string): string {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

// 获取连接状态
const connectionInfo = computed(() => {
  switch (connectionState.value) {
    case 'connecting':
      return { text: '连接中...', class: 'connecting', clickable: false }
    case 'connected':
      return { text: '已连接', class: 'connected', clickable: false }
    case 'error':
      return { text: '连接失败', class: 'error', clickable: true }
    default:
      return { text: '未连接', class: 'disconnected', clickable: true }
  }
})

// 判断是否可发送
const canSend = computed(() => {
  return inputText.value.trim() &&
    connectionState.value === 'connected' &&
    !sending.value &&
    !isStreaming.value
})
</script>

<template>
  <aside class="ai-drawer" :class="{ open: modelValue }">
    <!-- 头部 -->
    <div class="drawer-header">
      <div class="drawer-title">
        <el-icon :size="20"><ChatLineSquare /></el-icon>
        <span>AI 助手</span>
        <span
          class="connection-status"
          :class="connectionInfo.class"
          @click="connectionInfo.clickable && handleReconnect()"
        >
          {{ connectionInfo.text }}
        </span>
      </div>
      <div class="header-actions">
        <el-button text size="small" @click="handleNewConversation">
          <el-icon><Refresh /></el-icon>
          新对话
        </el-button>
        <el-button :icon="Close" circle size="small" @click="close" />
      </div>
    </div>

    <!-- 对话标题 -->
    <div v-if="title" class="conversation-title">
      {{ title }}
    </div>

    <!-- 消息列表 -->
    <div class="drawer-body" ref="messagesContainer">
      <div class="messages-list">
        <template v-for="msg in mainMessages" :key="msg.id">
          <!-- 用户消息 -->
          <div v-if="msg.role === 'user'" class="message-item user">
            <div class="message-bubble user-bubble">
              <div class="message-text">{{ msg.content.text }}</div>
            </div>
            <div class="message-time">{{ formatTime(msg.timestamp) }}</div>
          </div>

          <!-- AI 消息 -->
          <div v-else-if="msg.role === 'assistant'" class="message-item assistant">
            <div class="message-bubble assistant-bubble">
              <!-- 思维链（可折叠） -->
              <div v-if="msg.content.reasoning" class="reasoning-section">
                <div class="reasoning-header" @click="toggleReasoning(msg.id)">
                  <el-icon :size="14">
                    <component :is="isReasoningExpanded(msg.id) ? ArrowDown : ArrowRight" />
                  </el-icon>
                  <span class="reasoning-label">思考过程</span>
                </div>
                <div v-show="isReasoningExpanded(msg.id)" class="reasoning-content">
                  {{ msg.content.reasoning }}
                </div>
              </div>

              <!-- 正文内容 -->
              <div
                class="message-content markdown-body"
                v-html="renderMarkdown(msg.content.text)"
              ></div>

              <!-- 流式光标 -->
              <span v-if="msg.content.isStreaming" class="typing-cursor">|</span>

              <!-- 复制按钮 -->
              <div v-if="msg.content.text && !msg.content.isStreaming" class="message-actions">
                <el-button
                  text
                  size="small"
                  @click="copyText(msg.content.text)"
                >
                  <el-icon><DocumentCopy /></el-icon>
                </el-button>
              </div>
            </div>
            <div class="message-time">{{ formatTime(msg.timestamp) }}</div>
          </div>

          <!-- 工具调用 -->
          <div v-else-if="msg.role === 'tool'" class="message-item tool">
            <div
              class="message-bubble tool-bubble"
              :class="[msg.tool.status, { clickable: isToolClickable(msg.tool.name) }]"
              @click="handleToolClick(msg)"
            >
              <div class="tool-header">
                <el-icon v-if="msg.tool.status === 'pending'" class="spin" :size="14">
                  <Loading />
                </el-icon>
                <el-icon v-else-if="msg.tool.status === 'success'" :size="14" class="tool-icon success">
                  <CircleCheck />
                </el-icon>
                <el-icon v-else :size="14" class="tool-icon error">
                  <CircleClose />
                </el-icon>
                <span class="tool-name">{{ getToolDisplayName(msg) }}</span>
                <span v-if="getToolExtraInfo(msg)" class="tool-extra-info">{{ getToolExtraInfo(msg) }}</span>
                <span class="tool-status-text">
                  {{ msg.tool.status === 'pending' ? '执行中...' : msg.tool.status === 'success' ? '成功' : '失败' }}
                </span>
                <el-icon v-if="isToolClickable(msg.tool.name)" class="tool-arrow"><ArrowRight /></el-icon>
              </div>
            </div>
          </div>

          <!-- 子智能体 -->
          <div v-else-if="msg.role === 'agent'" class="message-item agent">
            <div class="message-bubble agent-bubble" :class="msg.agent.status">
              <div class="agent-header">
                <el-icon v-if="msg.agent.status === 'pending'" class="spin" :size="14">
                  <Loading />
                </el-icon>
                <span class="agent-label">子智能体</span>
                <span class="agent-id">{{ msg.agent.agentId }}</span>
              </div>
              <div v-if="msg.agent.input" class="agent-input">
                <span class="label">输入：</span>{{ msg.agent.input }}
              </div>
              <div v-if="msg.agent.output" class="agent-output">
                {{ msg.agent.output }}
              </div>
            </div>
          </div>
        </template>
      </div>

      <!-- 空状态 -->
      <div v-if="mainMessages.length === 0" class="empty-state">
        <div class="empty-icon">💬</div>
        <p class="empty-text">有什么可以帮你的吗？</p>
        <p class="empty-hint">输入问题开始对话</p>
      </div>
    </div>

    <!-- 底部输入区 -->
    <div class="drawer-footer">
      <div class="input-wrapper">
        <el-input
          v-model="inputText"
          type="textarea"
          placeholder="输入消息，Shift+Enter 换行"
          :disabled="connectionState !== 'connected'"
          :autosize="{ minRows: 1, maxRows: 6 }"
          :maxlength="500"
          show-word-limit
          resize="none"
          @keydown="handleKeydown"
        />
      </div>
      <el-button
        type="primary"
        :disabled="!canSend"
        :loading="sending || isStreaming"
        @click="handleSend"
      >
        {{ isStreaming ? '生成中' : '发送' }}
      </el-button>
    </div>

    <!-- 工具详情弹窗 -->
    <el-dialog
      v-model="toolDetailVisible"
      :title="`🔧 ${currentToolDetail.name}`"
      width="600px"
      class="tool-detail-dialog"
      append-to-body
    >
      <div class="tool-detail-content">
        <!-- 状态 -->
        <div class="detail-status" :class="currentToolDetail.status">
          <el-icon v-if="currentToolDetail.status === 'success'"><CircleCheck /></el-icon>
          <el-icon v-else-if="currentToolDetail.status === 'error'"><CircleClose /></el-icon>
          <el-icon v-else class="spin"><Loading /></el-icon>
          <span>
            {{ currentToolDetail.status === 'success' ? '执行成功' : currentToolDetail.status === 'error' ? '执行失败' : '执行中...' }}
          </span>
        </div>

        <!-- 调用参数 -->
        <div class="detail-section">
          <div class="section-title">
            <span>📥 调用参数</span>
            <el-button text size="small" @click="copyText(formatToolJson(currentToolDetail.arguments))">
              <el-icon><DocumentCopy /></el-icon>
            </el-button>
          </div>
          <div class="console-box">
            <pre class="console-text">{{ formatToolJson(currentToolDetail.arguments) }}</pre>
          </div>
        </div>

        <!-- 返回结果 -->
        <div class="detail-section">
          <div class="section-title">
            <span>📤 返回结果</span>
            <el-button text size="small" @click="copyText(currentToolDetail.result)">
              <el-icon><DocumentCopy /></el-icon>
            </el-button>
          </div>
          <div class="console-box">
            <pre class="console-text">{{ formatToolJson(currentToolDetail.result) }}</pre>
          </div>
        </div>
      </div>
    </el-dialog>
  </aside>
</template>

<style scoped>
/* ==================== 抽屉容器 ==================== */
.ai-drawer {
  position: fixed;
  top: 0;
  right: -480px;
  width: 480px;
  height: 100vh;
  background: var(--color-bg-card);
  border-left: 1px solid var(--color-border);
  box-shadow: -4px 0 24px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  z-index: 200;
  transition: right 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.ai-drawer.open {
  right: 0;
}

/* ==================== 头部 ==================== */
.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-bg-card);
}

.drawer-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 连接状态 */
.connection-status {
  font-size: 11px;
  font-weight: 500;
  padding: 3px 10px;
  border-radius: 12px;
  margin-left: 8px;
  transition: all 0.2s;
}

.connection-status.disconnected {
  background: rgba(150, 150, 150, 0.15);
  color: var(--color-text-tertiary);
  cursor: pointer;
}

.connection-status.disconnected:hover {
  background: rgba(150, 150, 150, 0.25);
}

.connection-status.connecting {
  background: var(--color-note-bg, rgba(250, 173, 20, 0.15));
  color: var(--color-note);
  animation: pulse 1.5s infinite;
}

.connection-status.connected {
  background: var(--color-income-bg);
  color: var(--color-income);
}

.connection-status.error {
  background: var(--color-expense-bg);
  color: var(--color-expense);
  cursor: pointer;
}

.connection-status.error:hover {
  background: rgba(245, 34, 45, 0.25);
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

/* 对话标题 */
.conversation-title {
  padding: 8px 20px;
  font-size: 13px;
  color: var(--color-text-secondary);
  background: var(--color-bg-page);
  border-bottom: 1px solid var(--color-border);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ==================== 消息列表 ==================== */
.drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.messages-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message-item {
  display: flex;
  flex-direction: column;
  max-width: 90%;
}

.message-item.user {
  align-self: flex-end;
  align-items: flex-end;
}

.message-item.assistant,
.message-item.tool,
.message-item.agent {
  align-self: flex-start;
  align-items: flex-start;
}

/* 消息气泡 */
.message-bubble {
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
  position: relative;
}

/* 用户气泡 */
.user-bubble {
  background: var(--color-transfer);
  color: #fff;
  border-bottom-right-radius: 4px;
}

/* AI 气泡 */
.assistant-bubble {
  background: var(--color-bg-page);
  color: var(--color-text-primary);
  border-bottom-left-radius: 4px;
}

/* 消息时间 */
.message-time {
  font-size: 11px;
  color: var(--color-text-tertiary);
  margin-top: 4px;
  padding: 0 4px;
}

/* ==================== 思维链 ==================== */
.reasoning-section {
  margin-bottom: 10px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  overflow: hidden;
}

.reasoning-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: rgba(24, 144, 255, 0.05);
  cursor: pointer;
  user-select: none;
  transition: background 0.2s;
}

.reasoning-header:hover {
  background: rgba(24, 144, 255, 0.1);
}

.reasoning-label {
  font-size: 12px;
  color: var(--color-transfer);
  font-weight: 500;
}

.reasoning-content {
  padding: 12px;
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.6;
  white-space: pre-wrap;
  border-top: 1px solid var(--color-border);
  background: rgba(24, 144, 255, 0.02);
}

/* ==================== Markdown 内容 ==================== */
.message-content {
  font-size: 14px;
  line-height: 1.7;
}

.message-content :deep(p) {
  margin: 0 0 8px 0;
}

.message-content :deep(p:last-child) {
  margin-bottom: 0;
}

.message-content :deep(code) {
  background: rgba(0, 0, 0, 0.06);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
}

.message-content :deep(pre) {
  background: var(--color-bg-page);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 12px;
  overflow-x: auto;
  margin: 8px 0;
}

.message-content :deep(pre code) {
  background: none;
  padding: 0;
}

.message-content :deep(ul),
.message-content :deep(ol) {
  padding-left: 20px;
  margin: 8px 0;
}

.message-content :deep(li) {
  margin: 4px 0;
}

.message-content :deep(blockquote) {
  border-left: 4px solid var(--color-transfer);
  background: rgba(24, 144, 255, 0.05);
  padding: 8px 12px;
  margin: 8px 0;
  color: var(--color-text-secondary);
}

.message-content :deep(.table-wrapper) {
  overflow-x: auto;
  margin: 8px 0;
  border-radius: 8px;
}

.message-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
  min-width: 300px;
}

.message-content :deep(th),
.message-content :deep(td) {
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  font-size: 13px;
}

.message-content :deep(th) {
  background: var(--color-bg-page);
  font-weight: 600;
}

/* 光标 */
.typing-cursor {
  animation: blink 1s infinite;
  color: var(--color-transfer);
  font-weight: bold;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

/* 消息操作 */
.message-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
  opacity: 0;
  transition: opacity 0.2s;
}

.assistant-bubble:hover .message-actions {
  opacity: 1;
}

/* ==================== 工具调用 ==================== */
.tool-bubble {
  background: var(--color-transfer-bg);
  border: 1px solid rgba(24, 144, 255, 0.2);
  border-bottom-left-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.tool-bubble:hover {
  background: rgba(24, 144, 255, 0.15);
}

.tool-bubble.success {
  border-color: rgba(82, 196, 26, 0.3);
}

.tool-bubble.error {
  border-color: rgba(245, 34, 45, 0.3);
}

.tool-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tool-name {
  font-weight: 500;
  color: var(--color-transfer);
}

.tool-extra-info {
  font-size: 12px;
  color: var(--color-text-primary);
  background: var(--color-transfer-bg);
  padding: 2px 8px;
  border-radius: 4px;
  margin-left: 4px;
}

.tool-status-text {
  font-size: 12px;
  color: var(--color-text-secondary);
  flex: 1;
}

.tool-bubble:not(.clickable) {
  cursor: default;
}

.tool-bubble:not(.clickable):hover {
  transform: none;
}

.tool-icon.success {
  color: var(--color-income);
}

.tool-icon.error {
  color: var(--color-expense);
}

.tool-arrow {
  color: var(--color-text-tertiary);
}

/* ==================== 子智能体 ==================== */
.agent-bubble {
  background: rgba(250, 173, 20, 0.1);
  border: 1px solid rgba(250, 173, 20, 0.2);
  border-bottom-left-radius: 4px;
}

.agent-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.agent-label {
  font-size: 12px;
  color: var(--color-note);
  font-weight: 500;
}

.agent-id {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.agent-input,
.agent-output {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin-top: 6px;
}

.agent-input .label {
  color: var(--color-text-tertiary);
}

/* ==================== 空状态 ==================== */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-text {
  font-size: 16px;
  color: var(--color-text-primary);
  margin: 0 0 8px 0;
}

.empty-hint {
  font-size: 13px;
  color: var(--color-text-tertiary);
  margin: 0;
}

/* ==================== 底部输入区 ==================== */
.drawer-footer {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid var(--color-border);
  background: var(--color-bg-card);
}

.input-wrapper {
  flex: 1;
}

.drawer-footer .el-button {
  flex-shrink: 0;
  height: 36px;
  min-width: 72px;
}

/* ==================== 旋转动画 ==================== */
.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* ==================== 工具详情弹窗 ==================== */
.tool-detail-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.detail-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;
  padding: 12px 16px;
  border-radius: 8px;
}

.detail-status.success {
  background: var(--color-income-bg);
  color: var(--color-income);
}

.detail-status.error {
  background: var(--color-expense-bg);
  color: var(--color-expense);
}

.detail-status.pending {
  background: rgba(250, 173, 20, 0.1);
  color: var(--color-note);
}

.detail-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.section-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.console-box {
  background: #1a1a1a;
  border-radius: 8px;
  padding: 0;
  max-height: 200px;
  overflow: auto;
}

.console-text {
  color: #00ff88;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
  line-height: 1.5;
  margin: 0;
  padding: 16px;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>

<!-- 暗色模式全局样式 -->
<style>
/* 抽屉暗色模式 */
html.dark .ai-drawer {
  background: var(--color-bg-card);
  border-left-color: var(--color-border);
  box-shadow: -4px 0 24px rgba(0, 0, 0, 0.4);
}

html.dark .drawer-header,
html.dark .drawer-footer {
  background: var(--color-bg-card);
  border-color: var(--color-border);
}

html.dark .conversation-title {
  background: var(--color-bg-container);
  border-color: var(--color-border);
}

/* 气泡暗色模式 */
html.dark .user-bubble {
  background: var(--color-transfer);
}

html.dark .assistant-bubble {
  background: var(--color-bg-container);
}

html.dark .tool-bubble {
  background: var(--color-transfer-bg);
}

html.dark .agent-bubble {
  background: rgba(255, 212, 59, 0.1);
}

/* 思维链暗色模式 */
html.dark .reasoning-section {
  border-color: var(--color-border);
}

html.dark .reasoning-header {
  background: rgba(116, 192, 252, 0.1);
}

html.dark .reasoning-header:hover {
  background: rgba(116, 192, 252, 0.15);
}

html.dark .reasoning-content {
  background: rgba(116, 192, 252, 0.05);
  border-color: var(--color-border);
}

/* Markdown 暗色模式 */
html.dark .message-content :deep(code) {
  background: rgba(255, 255, 255, 0.1);
}

html.dark .message-content :deep(pre) {
  background: var(--color-bg-container);
  border-color: var(--color-border);
}

html.dark .message-content :deep(blockquote) {
  background: rgba(116, 192, 252, 0.1);
}

html.dark .message-content :deep(th) {
  background: var(--color-bg-container);
}

html.dark .message-content :deep(th),
html.dark .message-content :deep(td) {
  border-color: var(--color-border);
}

/* 工具详情弹窗暗色模式 */
html.dark .tool-detail-dialog .el-dialog {
  background: var(--color-bg-card);
}

html.dark .tool-detail-dialog .el-dialog__header {
  border-bottom-color: var(--color-border);
}

html.dark .tool-detail-dialog .el-dialog__title {
  color: var(--color-text-primary);
}

html.dark .console-box {
  background: #0d0d0d;
}
</style>
