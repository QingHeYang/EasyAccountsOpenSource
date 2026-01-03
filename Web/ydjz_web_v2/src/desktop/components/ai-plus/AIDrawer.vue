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
  CircleClose,
  Picture,
  CloseBold
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import MarkdownIt from 'markdown-it'
import { imageApi } from '@shared/api/image'
import { compressImageForAI } from '@shared/utils/image-compress'
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
import FlowEditor from '@desktop/components/flow/FlowEditor.vue'

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
  stopConversation,
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
const stopping = ref(false)

// 图片附件状态
const pendingAttachments = ref<Array<{ filename: string; previewUrl: string }>>([])
const isUploading = ref(false)
const isDragOver = ref(false)
const fileInputRef = ref<HTMLInputElement | null>(null)
const MAX_ATTACHMENTS = 3
const ALLOWED_TYPES = ['image/png', 'image/jpeg', 'image/jpg']

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

// FlowEditor 状态
const flowEditorVisible = ref(false)
const flowEditorId = ref<number | null>(null)

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
    // 提取附件文件名
    const attachments = pendingAttachments.value.map(a => a.filename)
    const success = sendChatMessage(content, attachments.length > 0 ? attachments : undefined)
    if (success) {
      inputText.value = ''
      pendingAttachments.value = [] // 清空附件
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

// 停止生成
async function handleStop() {
  if (stopping.value) return

  stopping.value = true
  try {
    const success = await stopConversation()
    if (success) {
      ElMessage.success('已停止生成')
    }
  } catch (error) {
    console.error('停止失败:', error)
    ElMessage.error('停止失败')
  } finally {
    stopping.value = false
  }
}

// 新建对话
function handleNewConversation() {
  newConversation()  // 会自动清除 localStorage 和消息
  reasoningExpanded.value = {}
  pendingAttachments.value = []
  ElMessage.success('已开启新对话')
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
    input.value = '' // 清空以便重复选择同一文件
  }
}

// 拖拽进入
function handleDragEnter(e: DragEvent) {
  e.preventDefault()
  isDragOver.value = true
}

// 拖拽离开
function handleDragLeave(e: DragEvent) {
  e.preventDefault()
  // 确保是离开整个区域，而不是进入子元素
  const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
  if (
    e.clientX < rect.left ||
    e.clientX > rect.right ||
    e.clientY < rect.top ||
    e.clientY > rect.bottom
  ) {
    isDragOver.value = false
  }
}

// 拖拽悬停
function handleDragOver(e: DragEvent) {
  e.preventDefault()
}

// 拖拽放下
async function handleDrop(e: DragEvent) {
  e.preventDefault()
  isDragOver.value = false

  const files = e.dataTransfer?.files
  if (files) {
    await processFiles(Array.from(files))
  }
}

// 粘贴图片
async function handlePaste(e: ClipboardEvent) {
  const items = e.clipboardData?.items
  if (!items) return

  const imageFiles: File[] = []
  for (const item of items) {
    if (item.type.startsWith('image/')) {
      const file = item.getAsFile()
      if (file) {
        imageFiles.push(file)
      }
    }
  }

  if (imageFiles.length > 0) {
    e.preventDefault() // 阻止默认粘贴行为
    await processFiles(imageFiles)
  }
}

// 处理文件列表
async function processFiles(files: File[]) {
  // 过滤出图片
  const imageFiles = files.filter(f => ALLOWED_TYPES.includes(f.type))

  if (imageFiles.length === 0) {
    ElMessage.warning('仅支持 PNG 和 JPG 格式')
    return
  }

  // 检查数量限制
  const remaining = MAX_ATTACHMENTS - pendingAttachments.value.length
  if (remaining <= 0) {
    ElMessage.warning(`最多添加 ${MAX_ATTACHMENTS} 张图片`)
    return
  }

  const filesToProcess = imageFiles.slice(0, remaining)
  if (imageFiles.length > remaining) {
    ElMessage.warning(`已选择前 ${remaining} 张图片`)
  }

  isUploading.value = true

  for (const file of filesToProcess) {
    try {
      // 压缩
      const compressed = await compressImageForAI(file)

      // 上传
      const res = await imageApi.upload(compressed)
      const fileName = res.data.data?.fileName
      if (fileName) {
        pendingAttachments.value.push({
          filename: fileName,
          previewUrl: imageApi.getUrl(fileName)
        })
      } else {
        ElMessage.error(`上传失败: ${file.name}`)
      }
    } catch (err) {
      console.error('图片处理失败:', err)
      ElMessage.error(`处理失败: ${file.name}`)
    }
  }

  isUploading.value = false
}

// 移除附件
function removeAttachment(index: number) {
  pendingAttachments.value.splice(index, 1)
}

// 图片预览状态
const imagePreviewVisible = ref(false)
const imagePreviewList = ref<string[]>([])
const imagePreviewIndex = ref(0)

// 预览图片
function previewImage(url: string, urls?: string[]) {
  if (urls && urls.length > 0) {
    imagePreviewList.value = urls
    imagePreviewIndex.value = urls.indexOf(url)
  } else {
    imagePreviewList.value = [url]
    imagePreviewIndex.value = 0
  }
  imagePreviewVisible.value = true
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
  // 流式生成时不允许点击（避免断开 websocket）
  if (isStreaming.value) return

  const toolName = msg.tool.name

  // 不可点击的工具（且不可跳转）直接返回
  if (!isToolClickable(toolName)) return

  // 工具未完成时不允许跳转
  if (isToolNavigable(toolName) && msg.tool.status !== 'success') return

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
  } else if (navResult.type === 'flow' && navResult.flowParams) {
    // 打开流水编辑器
    flowEditorId.value = navResult.flowParams.flowId
    flowEditorVisible.value = true
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
              <!-- 思维链（可折叠） -->
              <div
                v-if="msg.content.reasoning"
                class="reasoning-card"
                :class="{
                  expanded: isReasoningExpanded(msg.id) || !msg.content.text,
                  'reasoning-only': !msg.content.text && !msg.content.isStreaming
                }"
              >
                <div class="reasoning-header" @click="msg.content.text && toggleReasoning(msg.id)">
                  <el-icon v-if="msg.content.text" :size="12" class="reasoning-toggle">
                    <component :is="isReasoningExpanded(msg.id) ? ArrowDown : ArrowRight" />
                  </el-icon>
                  <span class="reasoning-label">
                    {{ msg.content.isStreaming && msg.content.streamType === 'reasoning' ? '思考中' : '思考过程' }}
                  </span>
                  <span v-if="msg.content.isStreaming && msg.content.streamType === 'reasoning'" class="thinking-indicator">
                    <span class="dot"></span>
                    <span class="dot"></span>
                    <span class="dot"></span>
                  </span>
                </div>
                <div
                  v-show="isReasoningExpanded(msg.id) || !msg.content.text"
                  class="reasoning-body"
                >
                  <div class="reasoning-text">{{ msg.content.reasoning }}</div>
                </div>
              </div>

              <!-- 正文内容 -->
              <div
                v-if="msg.content.text || (msg.content.isStreaming && msg.content.streamType === 'content')"
                class="message-content markdown-body"
                v-html="renderMarkdown(msg.content.text)"
              ></div>

              <!-- 流式光标 -->
              <span v-if="msg.content.isStreaming" class="typing-cursor">|</span>

              <!-- 复制按钮 -->
              <div v-if="(msg.content.text || msg.content.reasoning) && !msg.content.isStreaming" class="message-actions">
                <el-button
                  text
                  size="small"
                  @click="copyText(msg.content.text || msg.content.reasoning)"
                  title="复制内容"
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
              class="tool-card"
              :class="[
                msg.tool.status,
                {
                  clickable: isToolClickable(msg.tool.name) && !isStreaming,
                  navigable: isToolNavigable(msg.tool.name) && msg.tool.status === 'success' && !isStreaming
                }
              ]"
              @click="handleToolClick(msg)"
            >
              <el-icon v-if="msg.tool.status === 'pending'" class="tool-icon spin" :size="14">
                <Loading />
              </el-icon>
              <el-icon v-else-if="msg.tool.status === 'success'" class="tool-icon success" :size="14">
                <CircleCheck />
              </el-icon>
              <el-icon v-else class="tool-icon error" :size="14">
                <CircleClose />
              </el-icon>
              <span class="tool-name">{{ getToolDisplayName(msg) }}</span>
              <span v-if="getToolExtraInfo(msg)" class="tool-extra">{{ getToolExtraInfo(msg) }}</span>
              <el-icon v-if="isToolNavigable(msg.tool.name) && msg.tool.status === 'success' && !isStreaming" class="tool-arrow" :size="12"><ArrowRight /></el-icon>
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
    <div
      class="drawer-footer"
      :class="{ 'drag-over': isDragOver }"
      @dragenter="handleDragEnter"
      @dragleave="handleDragLeave"
      @dragover="handleDragOver"
      @drop="handleDrop"
    >
      <!-- 拖拽提示遮罩 -->
      <div v-if="isDragOver" class="drag-overlay">
        <el-icon :size="32"><Picture /></el-icon>
        <span>松开添加图片</span>
      </div>

      <!-- 图片预览区 -->
      <div v-if="pendingAttachments.length > 0" class="attachments-preview">
        <div
          v-for="(att, index) in pendingAttachments"
          :key="att.filename"
          class="attachment-item"
        >
          <img
            :src="att.previewUrl"
            :alt="att.filename"
            class="attachment-thumb"
            @click="previewImage(att.previewUrl, pendingAttachments.map(a => a.previewUrl))"
          />
          <div class="attachment-remove" @click="removeAttachment(index)">
            <el-icon :size="12"><CloseBold /></el-icon>
          </div>
        </div>
        <!-- 添加更多按钮 -->
        <div
          v-if="pendingAttachments.length < MAX_ATTACHMENTS"
          class="attachment-add"
          @click="handleClickAddImage"
        >
          <el-icon :size="16"><Picture /></el-icon>
        </div>
      </div>

      <!-- 输入框 -->
      <div class="input-wrapper">
        <el-input
          v-model="inputText"
          type="textarea"
          placeholder="输入消息，Ctrl+V 粘贴图片，可拖入图片"
          :disabled="connectionState !== 'connected'"
          :autosize="{ minRows: 3, maxRows: 8 }"
          :maxlength="500"
          show-word-limit
          resize="none"
          @keydown="handleKeydown"
          @paste="handlePaste"
        />
      </div>

      <!-- 操作栏 -->
      <div class="input-actions">
        <div class="actions-left">
          <span class="input-hint">Shift + Enter 换行</span>
        </div>
        <div class="actions-right">
          <!-- 添加图片按钮 -->
          <el-tooltip content="添加图片 (最多3张)" placement="top">
            <el-button
              class="action-btn"
              :icon="Picture"
              :disabled="isUploading || pendingAttachments.length >= MAX_ATTACHMENTS"
              @click="handleClickAddImage"
            />
          </el-tooltip>
          <!-- 停止按钮（生成中显示） -->
          <el-button
            v-if="isStreaming"
            type="danger"
            class="stop-btn"
            :loading="stopping"
            @click="handleStop"
          >
            {{ stopping ? '停止中' : '停止' }}
          </el-button>
          <!-- 发送按钮 -->
          <el-button
            v-else
            type="primary"
            class="send-btn"
            :disabled="!canSend"
            :loading="sending || isUploading"
            @click="handleSend"
          >
            {{ isUploading ? '上传中' : '发送' }}
          </el-button>
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

    <!-- 图片预览 -->
    <el-image-viewer
      v-if="imagePreviewVisible"
      :url-list="imagePreviewList"
      :initial-index="imagePreviewIndex"
      @close="imagePreviewVisible = false"
    />

    <!-- 流水编辑器 -->
    <FlowEditor
      v-model:visible="flowEditorVisible"
      :flow-id="flowEditorId"
    />
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

/* ==================== 思维链卡片 ==================== */
.reasoning-card {
  margin-bottom: 10px;
  border-radius: 8px;
  overflow: hidden;
  background: rgba(24, 144, 255, 0.06);
  border: 1px solid rgba(24, 144, 255, 0.15);
}

.reasoning-card.reasoning-only {
  background: rgba(24, 144, 255, 0.04);
  border: none;
}

.reasoning-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  cursor: pointer;
  user-select: none;
  transition: background 0.2s;
}

.reasoning-card:not(.reasoning-only) .reasoning-header:hover {
  background: rgba(24, 144, 255, 0.08);
}

.reasoning-label {
  font-size: 12px;
  color: var(--color-transfer);
  font-weight: 500;
  flex: 1;
}

.reasoning-toggle {
  color: var(--color-transfer);
}

/* 思考中动画指示器 */
.thinking-indicator {
  display: flex;
  gap: 3px;
}

.thinking-indicator .dot {
  width: 4px;
  height: 4px;
  background: var(--color-transfer);
  border-radius: 50%;
  animation: thinking-dots 1.4s ease-in-out infinite;
}

.thinking-indicator .dot:nth-child(2) {
  animation-delay: 0.2s;
}

.thinking-indicator .dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes thinking-dots {
  0%, 80%, 100% { opacity: 0.4; }
  40% { opacity: 1; }
}

.reasoning-body {
  border-top: 1px solid rgba(24, 144, 255, 0.1);
}

.reasoning-text {
  padding: 10px 12px;
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.6;
  white-space: pre-wrap;
  max-height: 250px;
  overflow-y: auto;
}

.reasoning-card.reasoning-only .reasoning-header {
  display: none;
}

.reasoning-card.reasoning-only .reasoning-body {
  border: none;
}

.reasoning-card.reasoning-only .reasoning-text {
  padding: 0;
  color: var(--color-text-primary);
  font-size: 14px;
  max-height: none;
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

/* ==================== 工具调用卡片 ==================== */
.tool-card {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: var(--color-bg-page);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  font-size: 13px;
  transition: all 0.2s;
}

.tool-card.clickable {
  cursor: pointer;
}

.tool-card.clickable:hover {
  border-color: var(--color-transfer);
  background: var(--color-transfer-bg);
}

.tool-card:not(.clickable) {
  cursor: default;
}

.tool-card .tool-icon {
  flex-shrink: 0;
}

.tool-card .tool-icon.success {
  color: var(--color-income);
}

.tool-card .tool-icon.error {
  color: var(--color-expense);
}

.tool-card .tool-name {
  color: var(--color-text-primary);
  font-weight: 500;
}

.tool-card .tool-extra {
  color: var(--color-text-secondary);
  font-size: 12px;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tool-card .tool-arrow {
  color: var(--color-text-tertiary);
  margin-left: 4px;
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
  flex-direction: column;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid var(--color-border);
  background: var(--color-bg-card);
  position: relative;
  transition: all 0.2s;
}

.drawer-footer.drag-over {
  background: var(--color-transfer-bg);
}

/* 拖拽提示遮罩 */
.drag-overlay {
  position: absolute;
  inset: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: rgba(24, 144, 255, 0.08);
  border: 2px dashed var(--color-transfer);
  border-radius: 12px;
  z-index: 10;
  color: var(--color-transfer);
  font-size: 14px;
  font-weight: 500;
  pointer-events: none;
}

/* 图片预览区 */
.attachments-preview {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  padding: 8px 12px;
  background: var(--color-bg-page);
  border-radius: 8px;
}

.attachment-item {
  position: relative;
  width: 56px;
  height: 56px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.attachment-thumb {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 8px;
  cursor: pointer;
}

.attachment-remove {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.6);
  border-radius: 50%;
  color: #fff;
  cursor: pointer;
  opacity: 0;
  transition: all 0.2s;
}

.attachment-item:hover .attachment-remove {
  opacity: 1;
}

.attachment-remove:hover {
  background: var(--color-expense);
}

.attachment-add {
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px dashed var(--color-border);
  border-radius: 8px;
  color: var(--color-text-tertiary);
  cursor: pointer;
  transition: all 0.2s;
}

.attachment-add:hover {
  border-color: var(--color-transfer);
  color: var(--color-transfer);
  background: var(--color-transfer-bg);
}

/* 输入框容器 */
.input-wrapper {
  width: 100%;
}

.input-wrapper :deep(.el-textarea__inner) {
  padding: 12px 14px;
  font-size: 14px;
  line-height: 1.6;
  border-radius: 12px;
  background: var(--color-bg-page);
  border: 1px solid var(--color-border);
  transition: all 0.2s;
}

.input-wrapper :deep(.el-textarea__inner:focus) {
  border-color: var(--color-transfer);
  background: var(--color-bg-card);
  box-shadow: 0 0 0 3px var(--color-transfer-bg);
}

.input-wrapper :deep(.el-input__count) {
  background: transparent;
  font-size: 11px;
  color: var(--color-text-tertiary);
}

/* 操作栏 */
.input-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.actions-left {
  display: flex;
  align-items: center;
}

.input-hint {
  font-size: 11px;
  color: var(--color-text-tertiary);
}

.actions-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.action-btn {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  border: 1px solid var(--color-border);
  background: var(--color-bg-page);
  color: var(--color-text-secondary);
  transition: all 0.2s;
}

.action-btn:hover:not(:disabled) {
  border-color: var(--color-transfer);
  color: var(--color-transfer);
  background: var(--color-transfer-bg);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.send-btn,
.stop-btn {
  height: 36px;
  min-width: 80px;
  border-radius: 10px;
  font-weight: 500;
}

/* ==================== 消息中的图片 ==================== */
.message-images {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 8px;
}

.message-image {
  max-width: 200px;
  max-height: 150px;
  border-radius: 8px;
  cursor: pointer;
  transition: transform 0.2s;
}

.message-image:hover {
  transform: scale(1.02);
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
html.dark .reasoning-card {
  background: rgba(116, 192, 252, 0.08);
  border-color: rgba(116, 192, 252, 0.2);
}

html.dark .reasoning-card.reasoning-only {
  background: rgba(116, 192, 252, 0.06);
}

html.dark .reasoning-card:not(.reasoning-only) .reasoning-header:hover {
  background: rgba(116, 192, 252, 0.12);
}

html.dark .reasoning-body {
  border-color: rgba(116, 192, 252, 0.15);
}

/* 工具卡片暗色模式 */
html.dark .tool-card {
  background: var(--color-bg-container);
  border-color: var(--color-border);
}

html.dark .tool-card.clickable:hover {
  background: var(--color-transfer-bg);
  border-color: var(--color-transfer);
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
