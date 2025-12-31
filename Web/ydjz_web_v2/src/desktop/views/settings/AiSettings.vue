<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Close, Refresh, Coin, ChatDotRound, SetUp, Connection, CopyDocument, InfoFilled } from '@element-plus/icons-vue'
import { aiApi, type AiStats } from '@shared/api/ai'

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
}>()

// 抽屉状态
const drawerVisible = ref(false)

// 数据
const loading = ref(false)
const stats = ref<AiStats | null>(null)

// 监听外部 visible 变化
watch(() => props.visible, (val) => {
  drawerVisible.value = val
  if (val) {
    loadStats()
  }
})

// 监听内部 drawer 变化同步到外部
watch(drawerVisible, (val) => {
  emit('update:visible', val)
})

// 加载统计数据
async function loadStats() {
  loading.value = true
  try {
    const res = await aiApi.getStats()
    if (res.data.success) {
      stats.value = res.data.data
    }
  } catch (err) {
    console.error('获取 AI 统计失败', err)
    ElMessage.error('获取 AI 统计失败')
  } finally {
    loading.value = false
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

  try {
    await navigator.clipboard.writeText(mcpUrl.value)
    ElMessage.success('链接已复制')
  } catch {
    ElMessage.error('复制失败')
  }
}

// 刷新数据
function onRefresh() {
  loadStats()
}
</script>

<template>
  <el-drawer
    v-model="drawerVisible"
    direction="rtl"
    size="420px"
    :with-header="false"
    class="ai-settings-drawer"
  >
    <div class="drawer-container">
      <!-- Header -->
      <div class="drawer-header">
        <h2 class="drawer-title">AI+</h2>
        <div class="header-actions">
          <el-button text circle :loading="loading" @click="onRefresh">
            <el-icon :size="16"><Refresh /></el-icon>
          </el-button>
          <el-button text circle @click="drawerVisible = false">
            <el-icon :size="16"><Close /></el-icon>
          </el-button>
        </div>
      </div>

      <!-- Content -->
      <div v-loading="loading" class="drawer-body">
        <template v-if="stats">
          <!-- Token 使用统计 -->
          <div class="stats-card">
            <div class="card-header">
              <div class="card-icon">
                <el-icon :size="20"><Coin /></el-icon>
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
                <el-icon :size="18"><ChatDotRound /></el-icon>
              </div>
              <div class="mini-content">
                <div class="mini-value">{{ stats.conversation_count }}</div>
                <div class="mini-label">对话</div>
              </div>
            </div>
            <div class="stats-card mini">
              <div class="mini-icon tool">
                <el-icon :size="18"><SetUp /></el-icon>
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
                  <el-icon :size="20"><Connection /></el-icon>
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
              <div class="mcp-url-row">
                <code class="mcp-url-text">{{ mcpUrl }}</code>
                <el-button text size="small" @click="copyMcpUrl">
                  <el-icon :size="14"><CopyDocument /></el-icon>
                </el-button>
              </div>
            </div>
          </div>

          <!-- 使用说明 -->
          <div class="tips-section">
            <div class="tips-title">
              <el-icon :size="16"><InfoFilled /></el-icon>
              <span>使用说明</span>
            </div>
            <div class="tips-list">
              <div class="tip-item">
                <div class="tip-label">MCP 配置</div>
                <div class="tip-content">MCP 模式开关、SSE/Streamable HTTP 传输方式切换需在 <code>docker-compose.yml</code> 中修改。</div>
              </div>
              <div class="tip-item">
                <div class="tip-label">密钥安全</div>
                <div class="tip-content">LLM API Key 无法从前端修改，为保障密钥安全，请在 <code>docker-compose.yml</code> 中配置。</div>
              </div>
              <div class="tip-item">
                <div class="tip-label">Token 消耗</div>
                <div class="tip-content">Token 消耗量相对较小，系统采用<strong>窗口滚动 + 上下文总结</strong>策略。建议每 3-5 轮问答清空对话，可最大程度利用缓存策略；超过 10 轮问答成本会相对较高。后续策略可能调整，但 AI 并非本项目核心功能。</div>
              </div>
              <div class="tip-item">
                <div class="tip-label">MCP 链接</div>
                <div class="tip-content">链接有效期与登录过期时间一致（默认 30 分钟）。若需长期使用 MCP，建议将 <code>EXPIRED_TIME</code> 设置为较大值，或设置 <code>ENABLE_LOGIN=false</code> 关闭登录验证。<span class="tip-future">后续版本将优化此问题。</span></div>
              </div>
            </div>
          </div>
        </template>

        <!-- 空状态 -->
        <el-empty v-else-if="!loading" description="暂无统计数据" />
      </div>
    </div>
  </el-drawer>
</template>

<style scoped>
.drawer-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--color-bg-card);
}

.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--color-border-light);
  flex-shrink: 0;
}

.drawer-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.drawer-body {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background: var(--color-bg-page);
}

/* 卡片样式 - 参考 AccountManager */
.stats-card {
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border-radius: 14px;
  padding: 16px 18px;
  margin-bottom: 12px;
  border: 1.5px solid rgba(0, 0, 0, 0.04);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
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
  background: var(--color-note-bg, rgba(250, 173, 20, 0.1));
  color: var(--color-note);
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
  background: var(--color-border-light);
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
  background: var(--color-note);
}

/* 图例 */
.token-legend {
  display: flex;
  gap: 20px;
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
  background: var(--color-note);
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
  border-top: 1px solid var(--color-border-light);
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
}

.mcp-url-text {
  flex: 1;
  font-size: 12px;
  font-family: 'SF Mono', Monaco, Consolas, monospace;
  color: var(--color-text-secondary);
  background: var(--color-bg-page);
  padding: 8px 12px;
  border-radius: 6px;
  word-break: break-all;
  line-height: 1.5;
}

/* 使用说明 */
.tips-section {
  margin-top: 16px;
  padding: 16px;
  background: rgba(0, 0, 0, 0.02);
  border-radius: 12px;
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

.tip-content code {
  background: rgba(0, 0, 0, 0.06);
  padding: 1px 5px;
  border-radius: 3px;
  font-size: 11px;
  color: var(--color-text-secondary);
}

.tip-content strong {
  color: var(--color-text-secondary);
}

.tip-future {
  color: var(--color-transfer);
  font-size: 11px;
  margin-left: 4px;
}
</style>

<style>
/* 抽屉全局样式 */
.ai-settings-drawer .el-drawer__body {
  padding: 0;
}

/* 暗色模式 */
html.dark .stats-card {
  background: rgba(40, 40, 40, 0.6);
  border-color: rgba(255, 255, 255, 0.06);
}

html.dark .card-icon {
  background: rgba(250, 173, 20, 0.15);
}

html.dark .card-icon.mcp {
  background: var(--color-transfer-bg);
}

html.dark .mini-icon.conversation {
  background: var(--color-transfer-bg);
}

html.dark .mini-icon.tool {
  background: var(--color-income-bg);
}

html.dark .mcp-url-text {
  background: rgba(0, 0, 0, 0.3);
}

html.dark .tips-section {
  background: rgba(255, 255, 255, 0.03);
}

html.dark .tip-content code {
  background: rgba(255, 255, 255, 0.1);
}
</style>
