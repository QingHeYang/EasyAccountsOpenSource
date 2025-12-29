<script setup lang="ts">
import { ref, watch, nextTick, onUnmounted } from 'vue'
import { ChatLineSquare, Close, Loading } from '@element-plus/icons-vue'
import { useChatService, useMessageStore } from '@shared/services/chat'

const props = withDefaults(defineProps<{
  modelValue: boolean
}>(), {
  modelValue: false
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

// Chat 服务
const {
  connectionState,
  isStreaming,
  connect,
  disconnect,
  sendMessage: sendChatMessage,
  newConversation
} = useChatService()

// 消息存储
const { mainMessages } = useMessageStore()

// 输入框和消息容器引用
const inputText = ref('')
const messagesContainer = ref<HTMLElement | null>(null)

// 抽屉打开时连接 WebSocket
watch(() => props.modelValue, async (isOpen) => {
  if (isOpen && connectionState.value !== 'connected') {
    try {
      await connect()
      console.log('[AIDrawer] WebSocket 已连接')
    } catch (error) {
      console.error('[AIDrawer] WebSocket 连接失败', error)
    }
  }
}, { immediate: true })

// 消息变化时滚动到底部
watch(mainMessages, () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}, { deep: true })

// 组件卸载时断开连接
onUnmounted(() => {
  disconnect()
})

function close() {
  emit('update:modelValue', false)
}

function handleSend() {
  if (!inputText.value.trim() || isStreaming.value) return
  sendChatMessage(inputText.value)
  inputText.value = ''
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

function handleNewConversation() {
  newConversation()
}

// 获取连接状态文本
function getConnectionText() {
  switch (connectionState.value) {
    case 'connecting': return '连接中...'
    case 'connected': return '已连接'
    case 'error': return '连接失败'
    default: return '未连接'
  }
}
</script>

<template>
  <aside class="ai-drawer" :class="{ open: modelValue }">
    <div class="drawer-header">
      <div class="drawer-title">
        <el-icon :size="20"><ChatLineSquare /></el-icon>
        <span>AI 助手</span>
        <span class="connection-status" :class="connectionState">
          {{ getConnectionText() }}
        </span>
      </div>
      <div class="header-actions">
        <el-button text size="small" @click="handleNewConversation">新对话</el-button>
        <el-button :icon="Close" circle size="small" @click="close" />
      </div>
    </div>

    <div class="drawer-body" ref="messagesContainer">
      <!-- 消息列表 -->
      <div class="messages-list">
        <div
          v-for="msg in mainMessages"
          :key="msg.id"
          class="message-item"
          :class="msg.role"
        >
          <!-- 用户消息 -->
          <template v-if="msg.role === 'user'">
            <div class="message-bubble user-bubble">
              {{ msg.content.text }}
            </div>
          </template>

          <!-- AI 消息 -->
          <template v-else-if="msg.role === 'assistant'">
            <div class="message-bubble assistant-bubble">
              <div v-if="msg.content.reasoning" class="reasoning-text">
                <span class="reasoning-label">思考：</span>
                {{ msg.content.reasoning }}
              </div>
              <div class="content-text">
                {{ msg.content.text }}
                <span v-if="msg.content.isStreaming" class="typing-cursor">|</span>
              </div>
            </div>
          </template>

          <!-- 工具调用 -->
          <template v-else-if="msg.role === 'tool'">
            <div class="message-bubble tool-bubble">
              <div class="tool-header">
                <el-icon v-if="msg.tool.status === 'pending'" class="spin">
                  <Loading />
                </el-icon>
                <span class="tool-name">{{ msg.tool.name }}</span>
                <span class="tool-status" :class="msg.tool.status">
                  {{ msg.tool.status === 'pending' ? '执行中' : msg.tool.status === 'success' ? '成功' : '失败' }}
                </span>
              </div>
              <div v-if="msg.tool.result" class="tool-result">
                {{ msg.tool.result }}
              </div>
            </div>
          </template>

          <!-- 智能体调用 -->
          <template v-else-if="msg.role === 'agent'">
            <div class="message-bubble agent-bubble">
              <div class="agent-header">
                <el-icon v-if="msg.agent.status === 'pending'" class="spin">
                  <Loading />
                </el-icon>
                <span class="agent-name">子智能体: {{ msg.agent.agentId }}</span>
              </div>
              <div v-if="msg.agent.input" class="agent-input">
                输入: {{ msg.agent.input }}
              </div>
              <div v-if="msg.agent.output" class="agent-output">
                {{ msg.agent.output }}
              </div>
            </div>
          </template>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-if="mainMessages.length === 0" class="empty-hint">
        <p>开始和 AI 助手对话吧</p>
      </div>
    </div>

    <div class="drawer-footer">
      <el-input
        v-model="inputText"
        type="textarea"
        placeholder="输入消息..."
        :disabled="connectionState !== 'connected'"
        :autosize="{ minRows: 1, maxRows: 6 }"
        :maxlength="500"
        show-word-limit
        resize="none"
        @keydown="handleKeydown"
      />
      <el-button
        type="primary"
        :disabled="!inputText.trim() || connectionState !== 'connected'"
        :loading="isStreaming"
        @click="handleSend"
      >
        发送
      </el-button>
    </div>
  </aside>
</template>

<style scoped>
.ai-drawer {
  position: fixed;
  top: 0;
  right: -460px;
  width: 460px;
  height: 100vh;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-left: 1px solid rgba(0, 0, 0, 0.08);
  box-shadow: -4px 0 24px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  z-index: 200;
  transition: right 0.3s ease;
}

.ai-drawer.open {
  right: 0;
}

.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
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
  padding: 2px 8px;
  border-radius: 10px;
  margin-left: 4px;
}

.connection-status.disconnected {
  background: rgba(150, 150, 150, 0.15);
  color: #888;
}

.connection-status.connecting {
  background: rgba(250, 173, 20, 0.15);
  color: #d48806;
  animation: pulse 1.5s infinite;
}

.connection-status.connected {
  background: rgba(82, 196, 26, 0.15);
  color: #389e0d;
}

.connection-status.error {
  background: rgba(255, 77, 79, 0.15);
  color: #cf1322;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

/* 消息列表 */
.messages-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message-item {
  display: flex;
}

.message-item.user {
  justify-content: flex-end;
}

.message-item.assistant,
.message-item.tool,
.message-item.agent {
  justify-content: flex-start;
}

.message-bubble {
  max-width: 85%;
  padding: 12px 16px;
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
  background: var(--color-bg-page);
  color: var(--color-text-primary);
  border-bottom-left-radius: 4px;
}

.reasoning-text {
  font-size: 12px;
  color: var(--color-text-tertiary);
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 1px dashed rgba(0, 0, 0, 0.1);
}

.reasoning-label {
  font-weight: 500;
}

.typing-cursor {
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.tool-bubble,
.agent-bubble {
  background: var(--color-transfer-bg);
  border: 1px solid rgba(24, 144, 255, 0.2);
  border-bottom-left-radius: 4px;
}

.tool-header,
.agent-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.tool-name,
.agent-name {
  color: var(--color-transfer);
}

.tool-status {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 8px;
}

.tool-status.pending {
  background: rgba(250, 173, 20, 0.15);
  color: #d48806;
}

.tool-status.success {
  background: rgba(82, 196, 26, 0.15);
  color: #389e0d;
}

.tool-status.error {
  background: rgba(255, 77, 79, 0.15);
  color: #cf1322;
}

.tool-result,
.agent-input,
.agent-output {
  margin-top: 8px;
  font-size: 12px;
  color: var(--color-text-secondary);
  white-space: pre-wrap;
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 空状态 */
.empty-hint {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: var(--color-text-tertiary);
  text-align: center;
  font-size: 14px;
}

.drawer-footer {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
}

.drawer-footer .el-textarea {
  flex: 1;
}

.drawer-footer .el-button {
  flex-shrink: 0;
  height: 32px;
}
</style>

<style>
/* 暗色模式 */
html.dark .ai-drawer {
  background: rgba(30, 30, 30, 0.95);
  border-left-color: rgba(255, 255, 255, 0.1);
  box-shadow: -4px 0 24px rgba(0, 0, 0, 0.3);
}

html.dark .ai-drawer .drawer-header,
html.dark .ai-drawer .drawer-footer {
  border-color: rgba(255, 255, 255, 0.08);
}
</style>
