<script setup lang="ts">
import { ref, watch, nextTick, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showLoadingToast, closeToast, showImagePreview } from 'vant'
import MarkdownIt from 'markdown-it'
import {
  useChatService,
  useMessageStore,
  type UnifiedMessage,
  // 工具助手
  getToolDisplayName,
  getToolExtraInfo,
  isToolNavigable,
  getToolNavigationParams
} from '@shared/services/chat'
import { setScreenParams } from '@shared/services/screenParams'
import { imageApi } from '@shared/api/image'
import { compressImageForAI } from '@shared/utils/image-compress'

const router = useRouter()

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
  loadHistoryMessages,
  getSavedConversationId
} = useChatService()

// 消息存储
const { mainMessages } = useMessageStore()

// 本地状态
const inputText = ref('')
const messagesContainer = ref<HTMLElement | null>(null)
const sending = ref(false)

// 图片附件状态
const pendingAttachments = ref<Array<{ filename: string; previewUrl: string }>>([])
const isUploading = ref(false)
const fileInputRef = ref<HTMLInputElement | null>(null)
const MAX_ATTACHMENTS = 3
const ALLOWED_TYPES = ['image/png', 'image/jpeg', 'image/jpg']

// 思维链展开状态
const reasoningExpanded = ref<Record<string, boolean>>({})

// 页面加载时连接
onMounted(async () => {
  try {
    showLoadingToast({ message: '连接中...', forbidClick: true, duration: 0 })
    const savedId = getSavedConversationId()
    await connect(savedId || undefined)

    if (savedId) {
      await loadHistoryMessages(savedId)
    }
    closeToast()
  } catch (error) {
    closeToast()
    showToast('连接失败')
    console.error('[AI] 连接失败', error)
  }
})

// 页面卸载时断开
onUnmounted(() => {
  disconnect()
})

// 消息变化时滚动到底部
watch(mainMessages, () => {
  scrollToBottom()
}, { deep: true })

// 滚动到底部
function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

// 返回
function goBack() {
  router.back()
}

// 发送消息
async function handleSend() {
  if (!inputText.value.trim() || sending.value || isStreaming.value) return

  const content = inputText.value.trim()
  sending.value = true

  try {
    const attachments = pendingAttachments.value.map(a => a.filename)
    const success = sendChatMessage(content, attachments.length > 0 ? attachments : undefined)
    if (success) {
      inputText.value = ''
      pendingAttachments.value = []
    } else {
      showToast('发送失败，请检查连接')
    }
  } finally {
    sending.value = false
  }
}

// 新建对话
function handleNewConversation() {
  newConversation()
  reasoningExpanded.value = {}
  pendingAttachments.value = []
  showToast('已开启新对话')
}

// ==================== 图片附件处理 ====================

// 点击添加图片
function handleClickAddImage() {
  fileInputRef.value?.click()
}

// 文件选择变化
async function handleFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files) {
    await processFiles(Array.from(input.files))
    input.value = ''
  }
}

// 处理文件列表
async function processFiles(files: File[]) {
  const imageFiles = files.filter(f => ALLOWED_TYPES.includes(f.type))

  if (imageFiles.length === 0) {
    showToast('仅支持 PNG 和 JPG')
    return
  }

  const remaining = MAX_ATTACHMENTS - pendingAttachments.value.length
  if (remaining <= 0) {
    showToast(`最多 ${MAX_ATTACHMENTS} 张图片`)
    return
  }

  const filesToProcess = imageFiles.slice(0, remaining)
  if (imageFiles.length > remaining) {
    showToast(`已选择前 ${remaining} 张`)
  }

  isUploading.value = true
  showLoadingToast({ message: '上传中...', forbidClick: true, duration: 0 })

  for (const file of filesToProcess) {
    try {
      const compressed = await compressImageForAI(file)
      const res = await imageApi.upload(compressed)
      const fileName = res.data.data?.fileName
      if (fileName) {
        pendingAttachments.value.push({
          filename: fileName,
          previewUrl: imageApi.getUrl(fileName)
        })
      } else {
        showToast('上传失败')
      }
    } catch (err) {
      console.error('图片处理失败:', err)
      showToast('处理失败')
    }
  }

  closeToast()
  isUploading.value = false
}

// 移除附件
function removeAttachment(index: number) {
  pendingAttachments.value.splice(index, 1)
}

// 预览图片
function previewImage(url: string, urls?: string[]) {
  if (urls && urls.length > 0) {
    showImagePreview({
      images: urls,
      startPosition: urls.indexOf(url)
    })
  } else {
    showImagePreview([url])
  }
}

// 重新连接
async function handleReconnect() {
  if (connectionState.value === 'connecting') return

  try {
    showLoadingToast({ message: '重连中...', forbidClick: true, duration: 0 })
    disconnect()
    await connect()
    closeToast()
    showToast('重连成功')
  } catch {
    closeToast()
    showToast('重连失败')
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

// 连接状态
const connectionInfo = computed(() => {
  switch (connectionState.value) {
    case 'connecting':
      return { text: '连接中', class: 'connecting' }
    case 'connected':
      return { text: '已连接', class: 'connected' }
    case 'error':
      return { text: '连接失败', class: 'error' }
    default:
      return { text: '未连接', class: 'disconnected' }
  }
})

// 是否可发送
const canSend = computed(() => {
  return inputText.value.trim() &&
    connectionState.value === 'connected' &&
    !sending.value &&
    !isStreaming.value
})

// 复制文本
async function copyText(text: string) {
  try {
    await navigator.clipboard.writeText(text)
    showToast('已复制')
  } catch {
    showToast('复制失败')
  }
}

// 处理工具点击
function handleToolClick(msg: UnifiedMessage) {
  const toolName = msg.tool?.name || ''

  // 只有可跳转的工具才处理
  if (!isToolNavigable(toolName)) {
    return
  }

  const navResult = getToolNavigationParams(msg)
  if (!navResult) return

  if (navResult.type === 'flows' && navResult.params) {
    // 设置筛选参数
    setScreenParams(navResult.params, 'ai')
    // 跳转到筛选页面（移动端路由）
    router.push('/screen')
  }
}
</script>

<template>
  <div class="ai-page">
    <!-- 顶部导航 -->
    <div class="page-header">
      <div class="header-left" @click="goBack">
        <van-icon name="arrow-left" size="20" />
      </div>
      <div class="header-center">
        <div class="header-title">{{ title || 'AI 助手' }}</div>
        <span
          class="connection-tag"
          :class="connectionInfo.class"
          @click="connectionInfo.class === 'error' || connectionInfo.class === 'disconnected' ? handleReconnect() : null"
        >
          {{ connectionInfo.text }}
        </span>
      </div>
      <div class="header-right" @click="handleNewConversation">
        <van-icon name="add-o" size="20" />
      </div>
    </div>

    <!-- 消息列表 -->
    <div class="message-container" ref="messagesContainer">
      <div class="message-list">
        <template v-for="msg in mainMessages" :key="msg.id">
          <!-- 用户消息 -->
          <div v-if="msg.role === 'user'" class="message-item user">
            <div class="message-bubble user-bubble">
              <!-- 附件图片 -->
              <div v-if="msg.content.attachments?.length" class="message-images">
                <img
                  v-for="filename in msg.content.attachments"
                  :key="filename"
                  :src="imageApi.getUrl(filename)"
                  class="message-image"
                  @click="previewImage(imageApi.getUrl(filename), msg.content.attachments!.map(f => imageApi.getUrl(f)))"
                />
              </div>
              <div class="message-text">{{ msg.content.text }}</div>
            </div>
            <div class="message-time">{{ formatTime(msg.timestamp) }}</div>
          </div>

          <!-- AI 消息 -->
          <div v-else-if="msg.role === 'assistant'" class="message-item assistant">
            <div class="message-bubble assistant-bubble">
              <!-- 思维链 -->
              <div v-if="msg.content.reasoning" class="reasoning-section">
                <div class="reasoning-header" @click="toggleReasoning(msg.id)">
                  <van-icon :name="isReasoningExpanded(msg.id) ? 'arrow-down' : 'arrow'" size="12" />
                  <span class="reasoning-label">思考过程</span>
                </div>
                <div v-show="isReasoningExpanded(msg.id)" class="reasoning-content">
                  {{ msg.content.reasoning }}
                </div>
              </div>

              <!-- 正文 -->
              <div
                class="message-content markdown-body"
                v-html="renderMarkdown(msg.content.text)"
              ></div>

              <!-- 流式光标 -->
              <span v-if="msg.content.isStreaming" class="typing-cursor">|</span>

              <!-- 复制按钮 -->
              <div v-if="msg.content.text && !msg.content.isStreaming" class="message-actions">
                <van-icon name="notes-o" size="16" @click="copyText(msg.content.text)" />
              </div>
            </div>
            <div class="message-time">{{ formatTime(msg.timestamp) }}</div>
          </div>

          <!-- 工具调用 -->
          <div v-else-if="msg.role === 'tool'" class="message-item tool">
            <div
              class="tool-card"
              :class="[msg.tool.status, { navigable: isToolNavigable(msg.tool?.name || '') }]"
              @click="handleToolClick(msg)"
            >
              <div class="tool-status-dot" :class="msg.tool.status">
                <van-loading v-if="msg.tool.status === 'pending'" size="12" color="var(--color-transfer)" />
              </div>
              <div class="tool-info">
                <span class="tool-name">{{ getToolDisplayName(msg) }}</span>
                <span v-if="getToolExtraInfo(msg)" class="tool-extra">{{ getToolExtraInfo(msg) }}</span>
              </div>
              <van-icon
                v-if="isToolNavigable(msg.tool?.name || '') && msg.tool.status === 'success'"
                name="arrow"
                size="14"
                class="tool-arrow"
              />
            </div>
          </div>

          <!-- 子智能体 -->
          <div v-else-if="msg.role === 'agent'" class="message-item agent">
            <div class="agent-card" :class="msg.agent.status">
              <div class="agent-header">
                <div class="agent-status-dot" :class="msg.agent.status">
                  <van-loading v-if="msg.agent.status === 'pending'" size="12" color="#faad14" />
                </div>
                <span class="agent-name">{{ msg.agent.agentId }}</span>
              </div>
              <div v-if="msg.agent.input" class="agent-detail">{{ msg.agent.input }}</div>
              <div v-if="msg.agent.output" class="agent-detail output">{{ msg.agent.output }}</div>
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
    <div class="input-bar">
      <!-- 图片预览区 -->
      <div v-if="pendingAttachments.length > 0" class="attachments-preview">
        <div
          v-for="(att, index) in pendingAttachments"
          :key="att.filename"
          class="attachment-item"
        >
          <img :src="att.previewUrl" :alt="att.filename" class="attachment-thumb" />
          <div class="attachment-remove" @click="removeAttachment(index)">
            <van-icon name="cross" size="10" />
          </div>
        </div>
        <div
          v-if="pendingAttachments.length < MAX_ATTACHMENTS"
          class="attachment-add"
          @click="handleClickAddImage"
        >
          <van-icon name="plus" size="16" />
        </div>
      </div>

      <!-- 输入行 -->
      <div class="input-row">
        <!-- 添加图片按钮 -->
        <div
          v-if="pendingAttachments.length === 0"
          class="add-image-btn"
          :class="{ disabled: isUploading }"
          @click="handleClickAddImage"
        >
          <van-icon name="photo-o" size="22" />
        </div>

        <div class="input-wrapper">
          <van-field
            v-model="inputText"
            type="textarea"
            placeholder="输入消息..."
            :disabled="connectionState !== 'connected'"
            :autosize="{ minHeight: 24, maxHeight: 100 }"
            maxlength="500"
            @keypress.enter.prevent="handleSend"
          />
        </div>

        <div
          class="send-btn"
          :class="{ disabled: !canSend, loading: sending || isStreaming || isUploading }"
          @click="handleSend"
        >
          <van-loading v-if="sending || isStreaming || isUploading" size="18" color="#fff" />
          <van-icon v-else name="guide-o" size="20" />
        </div>
      </div>

      <!-- 隐藏的文件选择器 -->
      <input
        ref="fileInputRef"
        type="file"
        accept="image/png,image/jpeg,image/jpg"
        multiple
        style="display: none"
        @change="handleFileChange"
      />
    </div>
  </div>
</template>

<style scoped>
.ai-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--color-bg-page);
}

/* 顶部导航 */
.page-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 50;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.header-left,
.header-right {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: var(--color-bg-card);
  color: var(--color-text-primary);
}

.header-left:active,
.header-right:active {
  opacity: 0.7;
}

.header-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.header-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.connection-tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
}

.connection-tag.connected {
  background: var(--color-income-bg);
  color: var(--color-income);
}

.connection-tag.connecting {
  background: rgba(250, 173, 20, 0.15);
  color: #faad14;
}

.connection-tag.error,
.connection-tag.disconnected {
  background: var(--color-expense-bg);
  color: var(--color-expense);
}

/* 消息容器 */
.message-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  padding-top: 88px;
  padding-bottom: 100px;
}

.message-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.message-item {
  display: flex;
  flex-direction: column;
  max-width: 85%;
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

/* 气泡 */
.message-bubble {
  padding: 12px 14px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
}

.user-bubble {
  background: var(--color-transfer);
  color: #fff;
  border-bottom-right-radius: 4px;
}

.assistant-bubble {
  background: var(--color-bg-card);
  color: var(--color-text-primary);
  border-bottom-left-radius: 4px;
}

.message-time {
  font-size: 10px;
  color: var(--color-text-tertiary);
  margin-top: 4px;
  padding: 0 4px;
}

/* 思维链 */
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
  padding: 8px 10px;
  background: rgba(24, 144, 255, 0.05);
  cursor: pointer;
}

.reasoning-label {
  font-size: 12px;
  color: var(--color-transfer);
  font-weight: 500;
}

.reasoning-content {
  padding: 10px;
  font-size: 12px;
  color: var(--color-text-secondary);
  line-height: 1.5;
  white-space: pre-wrap;
  border-top: 1px solid var(--color-border);
  background: rgba(24, 144, 255, 0.02);
}

/* Markdown */
.message-content {
  font-size: 14px;
  line-height: 1.6;
}

.message-content :deep(p) {
  margin: 0 0 8px 0;
}

.message-content :deep(p:last-child) {
  margin-bottom: 0;
}

.message-content :deep(code) {
  background: rgba(0, 0, 0, 0.06);
  padding: 2px 4px;
  border-radius: 4px;
  font-size: 12px;
}

.message-content :deep(pre) {
  background: var(--color-bg-page);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 10px;
  overflow-x: auto;
  margin: 8px 0;
}

.message-content :deep(pre code) {
  background: none;
  padding: 0;
}

.message-content :deep(ul),
.message-content :deep(ol) {
  padding-left: 18px;
  margin: 8px 0;
}

.message-content :deep(.table-wrapper) {
  overflow-x: auto;
  margin: 8px 0;
}

.message-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
  font-size: 12px;
}

.message-content :deep(th),
.message-content :deep(td) {
  padding: 6px 10px;
  border: 1px solid var(--color-border);
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
  margin-top: 6px;
  color: var(--color-text-tertiary);
}

/* 工具调用 */
.tool-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: var(--color-bg-card);
  border-radius: 12px;
  border: 1px solid var(--color-border);
}

.tool-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-text-tertiary);
  flex-shrink: 0;
}

.tool-status-dot.pending {
  width: auto;
  height: auto;
  background: transparent;
}

.tool-status-dot.success {
  background: var(--color-income);
}

.tool-status-dot.error {
  background: var(--color-expense);
}

.tool-info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.tool-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.tool-extra {
  font-size: 11px;
  color: var(--color-text-secondary);
  background: var(--color-bg-page);
  padding: 2px 8px;
  border-radius: 6px;
}

.tool-card.navigable {
  cursor: pointer;
}

.tool-card.navigable:active {
  background: var(--color-bg-active);
}

.tool-arrow {
  color: var(--color-text-tertiary);
  flex-shrink: 0;
}

/* 子智能体 */
.agent-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px 14px;
  background: var(--color-bg-card);
  border-radius: 12px;
  border: 1px solid var(--color-border);
}

.agent-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.agent-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #faad14;
  flex-shrink: 0;
}

.agent-status-dot.pending {
  width: auto;
  height: auto;
  background: transparent;
}

.agent-status-dot.success {
  background: var(--color-income);
}

.agent-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.agent-detail {
  font-size: 12px;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

.agent-detail.output {
  color: var(--color-text-primary);
}

/* 空状态 */
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

/* 底部输入区 */
.input-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 12px 16px;
  padding-bottom: calc(12px + env(safe-area-inset-bottom));
  background: var(--color-bg-card);
  border-top: 1px solid var(--color-border);
}

/* 图片预览区 */
.attachments-preview {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.attachment-item {
  position: relative;
  width: 52px;
  height: 52px;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

.attachment-thumb {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.attachment-remove {
  position: absolute;
  top: -2px;
  right: -2px;
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-expense);
  border-radius: 50%;
  color: #fff;
}

.attachment-add {
  width: 52px;
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px dashed var(--color-border);
  border-radius: 8px;
  color: var(--color-text-tertiary);
}

.attachment-add:active {
  border-color: var(--color-transfer);
  color: var(--color-transfer);
}

/* 输入行 */
.input-row {
  display: flex;
  align-items: flex-end;
  gap: 10px;
}

.add-image-btn {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-secondary);
  flex-shrink: 0;
}

.add-image-btn:active {
  color: var(--color-transfer);
}

.add-image-btn.disabled {
  opacity: 0.5;
  pointer-events: none;
}

.input-wrapper {
  flex: 1;
  background: var(--color-bg-page);
  border-radius: 20px;
  border: 1px solid var(--color-border);
  overflow: hidden;
}

.input-wrapper :deep(.van-field) {
  background: transparent;
  padding: 10px 16px;
}

.input-wrapper :deep(.van-field__control) {
  min-height: 24px;
  line-height: 1.5;
}

.send-btn {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-transfer);
  border-radius: 12px;
  color: #fff;
  flex-shrink: 0;
  transition: opacity 0.2s;
}

.send-btn:active {
  opacity: 0.8;
}

.send-btn.disabled {
  background: var(--color-text-quaternary);
  pointer-events: none;
}

.send-btn.loading {
  pointer-events: none;
}

/* 消息中的图片 */
.message-images {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 8px;
}

.message-image {
  max-width: 160px;
  max-height: 120px;
  border-radius: 8px;
}
</style>

<!-- 非 scoped 样式 -->
<style>
.ai-page .page-header {
  background: rgba(245, 245, 245, 0.8);
}

html.dark .ai-page .page-header {
  background: rgba(10, 10, 10, 0.8);
}

html.dark .ai-page .assistant-bubble {
  background: var(--color-bg-container);
}

html.dark .ai-page .reasoning-header {
  background: rgba(116, 192, 252, 0.1);
}

html.dark .ai-page .reasoning-content {
  background: rgba(116, 192, 252, 0.05);
}

html.dark .ai-page .message-content :deep(code) {
  background: rgba(255, 255, 255, 0.1);
}

html.dark .ai-page .tool-card {
  background: var(--color-bg-card);
  border-color: var(--color-border);
}

html.dark .ai-page .agent-card {
  background: var(--color-bg-card);
  border-color: var(--color-border);
}

html.dark .ai-page .input-wrapper {
  background: var(--color-bg-container);
  border-color: var(--color-border);
}

html.dark .ai-page .input-bar {
  background: var(--color-bg-card);
  border-color: var(--color-border);
}
</style>
