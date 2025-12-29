<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ChatLineSquare, Close, House, Filter, Plus, TrendCharts } from '@element-plus/icons-vue'

const router = useRouter()

// 对话框状态（从 localStorage 恢复）
const STORAGE_KEY = 'ai-bubble-open'
const isOpen = ref(false)

onMounted(() => {
  isOpen.value = localStorage.getItem(STORAGE_KEY) === 'true'
})

watch(isOpen, (val) => {
  localStorage.setItem(STORAGE_KEY, String(val))
})

const emit = defineEmits<{
  'open-editor': []
}>()

// 快捷操作
const shortcuts = [
  { icon: House, label: '总览', action: () => router.push('/board') },
  { icon: TrendCharts, label: '统计', action: () => router.push('/analysis') },
  { icon: Filter, label: '筛选', action: () => router.push('/flow') },
  { icon: Plus, label: '记账', action: () => emit('open-editor') },
]

function toggle() {
  isOpen.value = !isOpen.value
}

function close() {
  isOpen.value = false
}

function handleShortcut(action: () => void) {
  action()
  // 不关闭气泡，保持打开状态
}
</script>

<template>
  <div class="ai-bubble-container">
    <!-- 对话框 -->
    <Transition name="popup">
      <div v-show="isOpen" class="ai-popup">
        <!-- 头部 -->
        <div class="popup-header">
          <div class="popup-title">
            <el-icon :size="18"><ChatLineSquare /></el-icon>
            <span>AI 助手</span>
          </div>
          <el-button :icon="Close" circle size="small" @click="close" />
        </div>

        <!-- 对话区域 -->
        <div class="popup-body">
          <!-- 快捷操作 -->
          <div class="shortcuts-section">
            <div class="section-title">快捷操作</div>
            <div class="shortcuts-grid">
              <button
                v-for="item in shortcuts"
                :key="item.label"
                class="shortcut-btn"
                @click="handleShortcut(item.action)"
              >
                <el-icon :size="20"><component :is="item.icon" /></el-icon>
                <span>{{ item.label }}</span>
              </button>
            </div>
          </div>

          <div class="messages-area">
            <!-- 欢迎消息 -->
            <div class="message ai-message">
              <div class="message-avatar">AI</div>
              <div class="message-content">
                <p>你好！我是 AI 助手，可以帮你：</p>
                <ul>
                  <li>智能记账</li>
                  <li>分析消费</li>
                  <li>财务建议</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="popup-footer">
          <el-input
            placeholder="输入消息..."
            :suffix-icon="ChatLineSquare"
          />
        </div>
      </div>
    </Transition>

    <!-- 悬浮气泡按钮 -->
    <button class="bubble-btn" :class="{ active: isOpen }" @click="toggle">
      <Transition name="icon-switch" mode="out-in">
        <el-icon v-if="!isOpen" :size="26" key="chat"><ChatLineSquare /></el-icon>
        <el-icon v-else :size="26" key="close"><Close /></el-icon>
      </Transition>
    </button>
  </div>
</template>

<style scoped>
.ai-bubble-container {
  position: fixed;
  right: 24px;
  bottom: 24px;
  z-index: 1000;
}

/* 悬浮气泡按钮 */
.bubble-btn {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  border: none;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  cursor: pointer;
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.45);
  transition: transform 0.3s, box-shadow 0.3s, background 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.bubble-btn:hover {
  transform: scale(1.08);
  box-shadow: 0 6px 28px rgba(102, 126, 234, 0.55);
}

.bubble-btn.active {
  background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
}

/* 对话框 */
.ai-popup {
  position: absolute;
  bottom: 76px;
  right: 0;
  width: 380px;
  height: 520px;
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 头部 */
.popup-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

.popup-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
}

.popup-header .el-button {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: #fff;
}

.popup-header .el-button:hover {
  background: rgba(255, 255, 255, 0.3);
}

/* 对话区域 */
.popup-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: var(--color-bg-page);
}

/* 快捷操作 */
.shortcuts-section {
  margin-bottom: 16px;
}

.section-title {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-tertiary);
  margin-bottom: 10px;
}

.shortcuts-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}

.shortcut-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 12px 8px;
  border: none;
  border-radius: 12px;
  background: #fff;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.shortcut-btn:hover {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.shortcut-btn span {
  font-size: 12px;
  font-weight: 500;
}

.messages-area {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 消息样式 */
.message {
  display: flex;
  gap: 10px;
}

.ai-message {
  flex-direction: row;
}

.user-message {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.message-content {
  max-width: 260px;
  padding: 12px 14px;
  background: #fff;
  border-radius: 12px;
  border-top-left-radius: 4px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-text-primary);
}

.message-content p {
  margin: 0 0 8px 0;
}

.message-content ul {
  margin: 0;
  padding-left: 18px;
}

.message-content li {
  margin: 4px 0;
  color: var(--color-text-secondary);
}

.user-message .message-content {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border-radius: 12px;
  border-top-right-radius: 4px;
}

/* 输入区域 */
.popup-footer {
  padding: 12px 16px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
  background: #fff;
}

/* 动画 */
.popup-enter-active,
.popup-leave-active {
  transition: opacity 0.25s, transform 0.25s;
}

.popup-enter-from,
.popup-leave-to {
  opacity: 0;
  transform: translateY(16px) scale(0.95);
}

.icon-switch-enter-active,
.icon-switch-leave-active {
  transition: transform 0.2s, opacity 0.2s;
}

.icon-switch-enter-from {
  transform: rotate(-90deg) scale(0.5);
  opacity: 0;
}

.icon-switch-leave-to {
  transform: rotate(90deg) scale(0.5);
  opacity: 0;
}
</style>

<style>
/* 暗色模式 */
html.dark .ai-popup {
  background: rgba(35, 35, 35, 0.98);
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.4);
}

html.dark .ai-popup .popup-body {
  background: rgba(25, 25, 25, 0.9);
}

html.dark .ai-popup .popup-footer {
  background: rgba(40, 40, 40, 0.95);
  border-top-color: rgba(255, 255, 255, 0.08);
}

html.dark .ai-popup .message-content {
  background: rgba(50, 50, 50, 0.9);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
}

html.dark .ai-popup .shortcut-btn {
  background: rgba(50, 50, 50, 0.8);
  color: var(--color-text-secondary);
}

html.dark .ai-popup .shortcut-btn:hover {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}
</style>
