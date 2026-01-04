<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { showToast, showLoadingToast, closeToast } from 'vant'
import { aiApi, type AiStats } from '@shared/api/ai'
import { useSmartBack } from '@shared/composables/useSmartBack'
import { copyToClipboard } from '@shared/utils/clipboard'

const { smartBack } = useSmartBack()

// 数据
const loading = ref(false)
const stats = ref<AiStats | null>(null)

// 加载统计数据
async function loadStats() {
  loading.value = true
  showLoadingToast({ message: '加载中...', forbidClick: true, duration: 0 })
  try {
    const res = await aiApi.getStats()
    if (res.data.success) {
      stats.value = res.data.data
    }
  } catch (err) {
    console.error('获取 AI 统计失败', err)
    showToast('获取统计失败')
  } finally {
    loading.value = false
    closeToast()
  }
}

// 格式化数字（K/M）
function formatNumber(num: number): string {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M'
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num.toString()
}

// 计算各部分百分比
const tokenPercents = computed(() => {
  if (!stats.value) return { prompt: 0, completion: 0, reasoning: 0 }
  const total = stats.value.token.total_tokens || 1
  return {
    prompt: (stats.value.token.prompt_tokens / total) * 100,
    completion: (stats.value.token.completion_tokens / total) * 100,
    reasoning: (stats.value.token.reasoning_tokens / total) * 100,
  }
})

// MCP 状态文本
const mcpStatusText = computed(() => {
  if (!stats.value) return '未知'
  if (!stats.value.mcp.enabled) return '未启用'
  return `${stats.value.mcp.transport_mode.toUpperCase()} 模式`
})

// MCP 链接
const mcpUrl = computed(() => {
  if (!stats.value?.mcp.enabled) return ''

  const { protocol, hostname, port } = window.location
  const host = port ? `${hostname}:${port}` : hostname
  const token = localStorage.getItem('token') || ''

  // 根据传输模式生成对应路径
  const path = stats.value.mcp.transport_mode === 'sse' ? '/sse' : '/mcp'

  return `${protocol}//${host}${path}?token=${encodeURIComponent(token)}`
})

// 复制链接
async function copyMcpUrl() {
  if (!mcpUrl.value) return

  const success = await copyToClipboard(mcpUrl.value)
  showToast(success ? '链接已复制' : '复制失败')
}

// 返回
function onBack() {
  smartBack('/setting')
}

// 刷新
function onRefresh() {
  loadStats()
}

onMounted(() => {
  loadStats()
})
</script>

<template>
  <div class="ai-settings-page">
    <!-- 顶部导航 -->
    <div class="page-header">
      <div class="header-left" @click="onBack">
        <van-icon name="arrow-left" size="20" />
      </div>
      <div class="header-title">AI+ 设置</div>
      <div class="header-right" @click="onRefresh">
        <van-icon name="replay" size="20" />
      </div>
    </div>

    <div class="page-body">
      <template v-if="stats">
        <!-- Token 消耗统计 -->
        <div class="stats-card">
          <div class="card-header">
            <div class="card-icon token">
              <van-icon name="gold-coin-o" size="20" />
            </div>
            <div class="card-title">Token 消耗</div>
          </div>
          <div class="token-total">{{ formatNumber(stats.token.total_tokens) }}</div>

          <!-- 三色进度条 -->
          <div class="token-bar">
            <div
              class="bar-segment prompt"
              :style="{ width: tokenPercents.prompt + '%' }"
            ></div>
            <div
              class="bar-segment completion"
              :style="{ width: tokenPercents.completion + '%' }"
            ></div>
            <div
              class="bar-segment reasoning"
              :style="{ width: tokenPercents.reasoning + '%' }"
            ></div>
          </div>

          <!-- 图例 -->
          <div class="token-legend">
            <div class="legend-item">
              <span class="legend-dot prompt"></span>
              <span class="legend-label">输入</span>
              <span class="legend-value">{{ formatNumber(stats.token.prompt_tokens) }}</span>
            </div>
            <div class="legend-item">
              <span class="legend-dot completion"></span>
              <span class="legend-label">输出</span>
              <span class="legend-value">{{ formatNumber(stats.token.completion_tokens) }}</span>
            </div>
            <div class="legend-item">
              <span class="legend-dot reasoning"></span>
              <span class="legend-label">推理</span>
              <span class="legend-value">{{ formatNumber(stats.token.reasoning_tokens) }}</span>
            </div>
          </div>
        </div>

        <!-- 使用统计 -->
        <div class="stats-row">
          <div class="stats-card mini">
            <div class="mini-icon conversation">
              <van-icon name="chat-o" size="18" />
            </div>
            <div class="mini-content">
              <div class="mini-value">{{ stats.conversation_count }}</div>
              <div class="mini-label">对话</div>
            </div>
          </div>
          <div class="stats-card mini">
            <div class="mini-icon tool">
              <van-icon name="setting-o" size="18" />
            </div>
            <div class="mini-content">
              <div class="mini-value">{{ stats.tool_call_count }}</div>
              <div class="mini-label">工具调用</div>
            </div>
          </div>
        </div>

        <!-- MCP 状态 -->
        <div class="stats-card">
          <div class="mcp-row">
            <div class="mcp-left">
              <div class="card-icon mcp">
                <van-icon name="link-o" size="20" />
              </div>
              <div class="card-title">MCP 服务</div>
            </div>
            <div class="mcp-status">
              <span class="status-dot" :class="{ active: stats.mcp.enabled }"></span>
              <span class="status-text">{{ mcpStatusText }}</span>
            </div>
          </div>

          <!-- MCP 链接 -->
          <div v-if="mcpUrl" class="mcp-url-section">
            <div class="mcp-url-label">连接地址</div>
            <div class="mcp-url-row" @click="copyMcpUrl">
              <code class="mcp-url-text">{{ mcpUrl }}</code>
              <van-icon name="records" size="16" class="copy-icon" />
            </div>
          </div>
        </div>

        <!-- 使用说明 -->
        <div class="tips-card">
          <div class="tips-title">
            <van-icon name="info-o" size="16" />
            <span>使用说明</span>
          </div>
          <div class="tips-list">
            <div class="tip-item">
              <div class="tip-label">MCP 配置</div>
              <div class="tip-content">MCP 模式开关、SSE/Streamable HTTP 传输方式切换需在 docker-compose.yml 中修改。</div>
            </div>
            <div class="tip-item">
              <div class="tip-label">密钥安全</div>
              <div class="tip-content">LLM API Key 无法从前端修改，请在 docker-compose.yml 中配置。</div>
            </div>
            <div class="tip-item">
              <div class="tip-label">Token 消耗</div>
              <div class="tip-content">系统采用窗口滚动 + 上下文总结策略。建议每 3-5 轮问答清空对话，可最大程度利用缓存策略。</div>
            </div>
            <div class="tip-item">
              <div class="tip-label">MCP 链接</div>
              <div class="tip-content">链接有效期与登录过期时间一致（默认 30 分钟）。</div>
            </div>
          </div>
        </div>
      </template>

      <!-- 空状态 -->
      <van-empty v-else-if="!loading" description="暂无统计数据" />
    </div>
  </div>
</template>

<style scoped>
.ai-settings-page {
  min-height: 100vh;
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

.header-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.page-body {
  padding: 76px 16px 24px;
}

/* 卡片样式 */
.stats-card {
  background: var(--color-bg-card);
  border-radius: 16px;
  padding: 16px;
  margin-bottom: 12px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.card-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
}

.card-icon.token {
  background: rgba(250, 173, 20, 0.1);
  color: #faad14;
}

.card-icon.mcp {
  background: var(--color-transfer-bg);
  color: var(--color-transfer);
}

.card-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-secondary);
}

/* Token 统计 */
.token-total {
  font-size: 36px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 14px;
}

/* 三色进度条 */
.token-bar {
  display: flex;
  height: 8px;
  background: var(--color-border);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 14px;
}

.bar-segment {
  height: 100%;
  transition: width 0.3s ease;
}

.bar-segment.prompt {
  background: var(--color-transfer);
}

.bar-segment.completion {
  background: var(--color-income);
}

.bar-segment.reasoning {
  background: #faad14;
}

/* 图例 */
.token-legend {
  display: flex;
  gap: 16px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 2px;
}

.legend-dot.prompt {
  background: var(--color-transfer);
}

.legend-dot.completion {
  background: var(--color-income);
}

.legend-dot.reasoning {
  background: #faad14;
}

.legend-label {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.legend-value {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
}

/* 迷你卡片 */
.stats-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 12px;
}

.stats-card.mini {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 0;
}

.mini-icon {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  flex-shrink: 0;
}

.mini-icon.conversation {
  background: var(--color-transfer-bg);
  color: var(--color-transfer);
}

.mini-icon.tool {
  background: var(--color-income-bg);
  color: var(--color-income);
}

.mini-content {
  flex: 1;
}

.mini-value {
  font-size: 24px;
  font-weight: 600;
  color: var(--color-text-primary);
  line-height: 1.2;
}

.mini-label {
  font-size: 12px;
  color: var(--color-text-tertiary);
  margin-top: 2px;
}

/* MCP 状态 */
.mcp-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.mcp-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.mcp-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-text-tertiary);
}

.status-dot.active {
  background: var(--color-income);
}

.status-text {
  font-size: 14px;
  color: var(--color-text-secondary);
}

/* MCP 链接 */
.mcp-url-section {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid var(--color-border);
}

.mcp-url-label {
  font-size: 12px;
  color: var(--color-text-tertiary);
  margin-bottom: 8px;
}

.mcp-url-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: var(--color-bg-page);
  border-radius: 8px;
}

.mcp-url-row:active {
  opacity: 0.7;
}

.mcp-url-text {
  flex: 1;
  font-size: 12px;
  font-family: 'SF Mono', Monaco, Consolas, monospace;
  color: var(--color-text-secondary);
  word-break: break-all;
  line-height: 1.5;
}

.copy-icon {
  color: var(--color-transfer);
  flex-shrink: 0;
}

/* 使用说明 */
.tips-card {
  background: var(--color-bg-card);
  border-radius: 16px;
  padding: 16px;
}

.tips-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-secondary);
  margin-bottom: 12px;
}

.tips-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tip-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.tip-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.tip-content {
  font-size: 12px;
  line-height: 1.6;
  color: var(--color-text-tertiary);
}
</style>

<!-- 非 scoped 样式 -->
<style>
.ai-settings-page .page-header {
  background: rgba(245, 245, 245, 0.8);
}

html.dark .ai-settings-page .page-header {
  background: rgba(10, 10, 10, 0.8);
}

html.dark .ai-settings-page .stats-card {
  background: var(--color-bg-card);
}

html.dark .ai-settings-page .tips-card {
  background: var(--color-bg-card);
}

html.dark .ai-settings-page .mcp-url-row {
  background: var(--color-bg-container);
}

html.dark .ai-settings-page .card-icon.token {
  background: rgba(250, 173, 20, 0.15);
}
</style>
