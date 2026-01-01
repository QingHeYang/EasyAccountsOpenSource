<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Sunny,
  Moon,
  Monitor,
  SwitchButton,
  CreditCard,
  Wallet,
  PriceTag,
  DocumentCopy,
  InfoFilled,
  ArrowRight,
  ArrowDown,
  ArrowUp,
  Close,
  MagicStick
} from '@element-plus/icons-vue'
import { useThemeStore } from '@shared/stores/theme'
import { homeApi, type VersionInfo } from '@shared/api/home'
import { aiApi, type AiHealthResponse } from '@shared/api/ai'
import logoUrl from '@shared/assets/logo.png'
import './styles.css'

// 子组件
import ActionManager from './ActionManager.vue'
import AccountManager from './AccountManager.vue'
import TypeManager from './TypeManager.vue'
import TemplateManager from './TemplateManager.vue'
import AiSettings from './AiSettings.vue'

const router = useRouter()
const themeStore = useThemeStore()

// AI 服务状态
const aiHealth = ref<AiHealthResponse | null>(null)
const aiServiceAvailable = computed(() => aiHealth.value !== null)
const aiConfigured = computed(() => aiHealth.value?.data?.llm?.configured === true)

// 主题相关
const themeOptions = [
  { value: 'light', label: '浅色', icon: Sunny },
  { value: 'dark', label: '深色', icon: Moon },
  { value: 'system', label: '跟随系统', icon: Monitor },
] as const

const currentTheme = computed({
  get: () => themeStore.mode,
  set: (val) => themeStore.set(val as 'light' | 'dark' | 'system')
})

// 关于弹窗
const showAbout = ref(false)
const showVersionDetail = ref(false)
const versions = ref<VersionInfo>({
  release: '',
  fontBranch: '',
  backendBranch: '',
  mysqlBranch: '',
  agentBranch: '',
  webhookBranch: '',
})

async function loadVersion() {
  try {
    const res = await homeApi.getVersion()
    versions.value = res.data.data
  } catch (err) {
    console.error('获取版本信息失败', err)
  }
}

function openAbout() {
  showAbout.value = true
  if (!versions.value.release) {
    loadVersion()
  }
}

// 退出登录
function onLogout() {
  ElMessageBox.confirm('确定要退出登录吗？', '退出登录', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(() => {
    localStorage.removeItem('token')
    ElMessage.success('已退出登录')
    router.push('/auth?mode=1')
  }).catch(() => {})
}

// 数据管理项（不含 AI，AI 单独处理）
const dataItems = [
  { key: 'action', title: '收支管理', desc: '管理收入和支出类型', icon: CreditCard },
  { key: 'account', title: '账户管理', desc: '管理银行卡、现金等账户', icon: Wallet },
  { key: 'type', title: '分类管理', desc: '管理收支分类', icon: PriceTag },
  { key: 'template', title: '快记模板', desc: '快速记账模板', icon: DocumentCopy },
]

// AI 设置项
const aiItem = { key: 'ai', title: 'AI+ 设置', desc: 'Token 统计与 MCP 状态', icon: MagicStick }

// 检测 AI 服务
async function checkAiService() {
  aiHealth.value = await aiApi.checkHealth()
}

// 子组件抽屉状态
const showActionDrawer = ref(false)
const showAccountDrawer = ref(false)
const showTypeDrawer = ref(false)
const showTemplateDrawer = ref(false)
const showAiDrawer = ref(false)

function openDrawer(key: string) {
  if (key === 'action') {
    showActionDrawer.value = true
  } else if (key === 'account') {
    showAccountDrawer.value = true
  } else if (key === 'type') {
    showTypeDrawer.value = true
  } else if (key === 'template') {
    showTemplateDrawer.value = true
  } else if (key === 'ai') {
    // AI 配置未完成时显示提示
    if (!aiConfigured.value) {
      const missing = aiHealth.value?.data?.llm?.missing || []
      ElMessageBox.alert(
        `<div class="ai-config-dialog">
          <div class="dialog-icon">
            <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M12 9v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <p class="dialog-title">AI 服务未完成配置</p>
          <p class="dialog-desc">请在 <code>docker-compose.yml</code> 的 AI 容器中配置以下环境变量：</p>
          <div class="missing-list">
            ${missing.map(m => `<div class="missing-item"><code>${m}</code></div>`).join('')}
          </div>
          <div class="config-example">
            <div class="example-title">配置说明</div>
            <div class="config-fields">
              <div class="config-field">
                <code>LLM_EASY_ACCOUNTS_API_KEY</code>
                <span>LLM 服务的 API 密钥</span>
              </div>
              <div class="config-field">
                <code>LLM_EASY_ACCOUNTS_URL</code>
                <span>LLM 服务的 API 地址（OpenAI 兼容格式）</span>
              </div>
              <div class="config-field">
                <code>LLM_EASY_ACCOUNTS_MODEL</code>
                <span>使用的模型名称</span>
              </div>
            </div>
            <div class="example-title" style="margin-top: 12px;">配置示例</div>
            <pre>- LLM_EASY_ACCOUNTS_API_KEY=sk-your-key
- LLM_EASY_ACCOUNTS_URL=https://api.openai.com/v1
- LLM_EASY_ACCOUNTS_MODEL=gpt-3.5-turbo</pre>
          </div>
        </div>`,
        '',
        {
          dangerouslyUseHTMLString: true,
          confirmButtonText: '知道了',
          customClass: 'ai-config-message-box',
          showClose: false,
        }
      )
      return
    }
    showAiDrawer.value = true
  }
}

onMounted(() => {
  loadVersion()
  checkAiService()
})
</script>

<template>
  <div class="setting-page">
    <h1 class="page-title">设置</h1>

    <div class="setting-content">
      <!-- 数据管理 -->
      <div class="setting-section">
        <h2 class="section-title">数据管理</h2>
        <div class="data-grid">
          <div
            v-for="item in dataItems"
            :key="item.key"
            class="data-card"
            @click="openDrawer(item.key)"
          >
            <div class="card-icon">
              <el-icon :size="24"><component :is="item.icon" /></el-icon>
            </div>
            <div class="card-info">
              <div class="card-title">{{ item.title }}</div>
              <div class="card-desc">{{ item.desc }}</div>
            </div>
            <el-icon class="card-arrow"><ArrowRight /></el-icon>
          </div>
          <!-- AI 设置卡片 (仅在 AI 服务可用时显示) -->
          <div
            v-if="aiServiceAvailable"
            class="data-card"
            :class="{ 'ai-unconfigured': !aiConfigured }"
            @click="openDrawer('ai')"
          >
            <div class="card-icon ai-icon">
              <el-icon :size="24"><component :is="aiItem.icon" /></el-icon>
            </div>
            <div class="card-info">
              <div class="card-title">
                {{ aiItem.title }}
                <el-tag v-if="!aiConfigured" size="small" type="warning" style="margin-left: 8px;">未配置</el-tag>
              </div>
              <div class="card-desc">{{ aiItem.desc }}</div>
            </div>
            <el-icon class="card-arrow"><ArrowRight /></el-icon>
          </div>
        </div>
      </div>

      <!-- 外观设置 -->
      <div class="setting-section">
        <h2 class="section-title">外观</h2>
        <div class="appearance-card">
          <div class="appearance-label">
            <el-icon :size="20"><Monitor /></el-icon>
            <span>主题模式</span>
          </div>
          <el-radio-group v-model="currentTheme" class="theme-radio-group">
            <el-radio-button
              v-for="opt in themeOptions"
              :key="opt.value"
              :value="opt.value"
            >
              <el-icon><component :is="opt.icon" /></el-icon>
              <span>{{ opt.label }}</span>
            </el-radio-button>
          </el-radio-group>
        </div>
      </div>

      <!-- 其他 -->
      <div class="setting-section">
        <h2 class="section-title">其他</h2>
        <div class="other-actions">
          <el-button size="large" @click="openAbout">
            <el-icon><InfoFilled /></el-icon>
            <span>关于</span>
          </el-button>
          <el-button size="large" type="danger" plain @click="onLogout">
            <el-icon><SwitchButton /></el-icon>
            <span>退出登录</span>
          </el-button>
        </div>
      </div>
    </div>

    <!-- 关于弹窗 -->
    <el-dialog
      v-model="showAbout"
      width="400"
      :show-close="false"
      class="about-dialog"
    >
      <div class="about-content">
        <!-- 关闭按钮 -->
        <div class="about-close" @click="showAbout = false">
          <el-icon :size="18"><Close /></el-icon>
        </div>
        <!-- 顶部装饰背景 -->
        <div class="about-bg"></div>

        <!-- Logo -->
        <div class="about-logo-wrapper">
          <img :src="logoUrl" alt="Logo" class="about-logo" />
        </div>

        <!-- 应用名称 -->
        <div class="about-name">EasyAccounts</div>

        <!-- 副标题 -->
        <div class="about-slogan">认真生活, 好好记账</div>

        <!-- 版本标签（可点击展开） -->
        <div class="about-version-tag" @click="showVersionDetail = !showVersionDetail">
          <span class="version-label">Version</span>
          <span class="version-value">{{ versions.release || '...' }}</span>
          <el-icon class="version-arrow"><component :is="showVersionDetail ? ArrowUp : ArrowDown" /></el-icon>
        </div>

        <!-- 版本详情 -->
        <div v-if="showVersionDetail" class="version-detail">
          <div class="version-item">
            <span class="item-label">前端</span>
            <span class="item-value">{{ versions.fontBranch || '-' }}</span>
          </div>
          <div class="version-item">
            <span class="item-label">后端</span>
            <span class="item-value">{{ versions.backendBranch || '-' }}</span>
          </div>
          <div class="version-item">
            <span class="item-label">数据库</span>
            <span class="item-value">{{ versions.mysqlBranch || '-' }}</span>
          </div>
          <div class="version-item">
            <span class="item-label">AI Agent</span>
            <span class="item-value">{{ versions.agentBranch || '-' }}</span>
          </div>
          <div class="version-item">
            <span class="item-label">WebHook</span>
            <span class="item-value">{{ versions.webhookBranch || '-' }}</span>
          </div>
        </div>

        <!-- 分隔线 -->
        <el-divider />

        <!-- 开发者信息 -->
        <a
          href="https://github.com/QingHeYang/EasyAccounts"
          target="_blank"
          class="developer-card"
        >
          <img
            src="https://avatars.githubusercontent.com/u/19968251?u=5bc82e5f642e80a6aa51c9eb10389932db38135f&v=4&size=64"
            alt="Avatar"
            class="developer-avatar"
          />
          <div class="developer-info">
            <div class="developer-name">QingHeYang</div>
            <div class="developer-role">Developer</div>
          </div>
          <el-icon class="developer-arrow"><ArrowRight /></el-icon>
        </a>

        <!-- 底部 -->
        <div class="about-footer">Made with care</div>
      </div>
    </el-dialog>

    <!-- 底部 Powered by -->
    <div class="powered-by">
      Powered by <a href="https://github.com/QingHeYang/EasyAccounts" target="_blank">EasyAccounts</a>
    </div>

    <!-- 子组件抽屉 -->
    <ActionManager v-model:visible="showActionDrawer" />
    <AccountManager v-model:visible="showAccountDrawer" />
    <TypeManager v-model:visible="showTypeDrawer" />
    <TemplateManager v-model:visible="showTemplateDrawer" />
    <AiSettings v-model:visible="showAiDrawer" />
  </div>
</template>

<style scoped>
.setting-page {
  padding: 20px;
  min-height: calc(100vh - 112px);
  display: flex;
  flex-direction: column;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 24px 0;
}

.setting-content {
  max-width: 800px;
}

/* Section */
.setting-section {
  margin-bottom: 32px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0 0 16px 4px;
}

/* 数据管理卡片网格 */
.data-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.data-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.data-card:hover {
  background: rgba(255, 255, 255, 0.95);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.card-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-transfer);
  border-radius: 12px;
  color: #fff;
}

.card-info {
  flex: 1;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.card-desc {
  margin-top: 4px;
  font-size: 13px;
  color: var(--color-text-tertiary);
}

.card-arrow {
  color: var(--color-text-tertiary);
}

/* AI 卡片特殊样式 */
.card-icon.ai-icon {
  background: var(--color-transfer);
}

.data-card.ai-unconfigured {
  opacity: 0.7;
}

.data-card.ai-unconfigured .card-icon.ai-icon {
  background: var(--color-text-tertiary);
}

/* 外观设置 */
.appearance-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.appearance-label {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 16px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.theme-radio-group {
  display: flex;
  gap: 8px;
}

.theme-radio-group :deep(.el-radio-button__inner) {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  border-radius: 10px !important;
  border: none !important;
  box-shadow: none !important;
}

.theme-radio-group :deep(.el-radio-button:first-child .el-radio-button__inner) {
  border-radius: 10px !important;
}

.theme-radio-group :deep(.el-radio-button:last-child .el-radio-button__inner) {
  border-radius: 10px !important;
}

/* 其他操作 */
.other-actions {
  display: flex;
  gap: 12px;
}

.other-actions .el-button {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 关于弹窗内容 */
.about-content {
  position: relative;
  text-align: center;
}

.about-close {
  position: absolute;
  top: -12px;
  right: -12px;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  cursor: pointer;
  color: var(--color-text-tertiary);
  transition: all 0.2s;
  z-index: 10;
}

.about-close:hover {
  color: var(--color-text-primary);
  background: var(--color-bg-active, #f0f0f0);
}

.about-bg {
  position: absolute;
  top: -40px;
  left: 50%;
  transform: translateX(-50%);
  width: 200px;
  height: 200px;
  background: linear-gradient(135deg, var(--color-transfer) 0%, var(--color-income) 100%);
  border-radius: 50%;
  opacity: 0.15;
  filter: blur(40px);
  pointer-events: none;
}

.about-logo-wrapper {
  position: relative;
  display: inline-flex;
  padding: 16px;
  background: var(--color-bg-page);
  border-radius: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.about-logo {
  width: 64px;
  height: 64px;
}

.about-name {
  margin-top: 20px;
  font-size: 24px;
  font-weight: 700;
  color: var(--color-text-primary);
}

.about-slogan {
  margin-top: 8px;
  font-size: 14px;
  color: var(--color-text-secondary);
}

.about-version-tag {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
  padding: 8px 16px;
  background: var(--color-bg-page);
  border-radius: 20px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s;
}

.about-version-tag:hover {
  background: var(--color-border);
}

.version-label {
  color: var(--color-text-tertiary);
}

.version-value {
  color: var(--color-transfer);
  font-weight: 600;
}

.version-arrow {
  color: var(--color-text-tertiary);
  font-size: 12px;
  margin-left: 2px;
}

/* 版本详情 */
.version-detail {
  margin-top: 16px;
  padding: 12px 16px;
  background: var(--color-bg-page);
  border-radius: 12px;
  text-align: left;
  width: 100%;
}

.version-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}

.version-item:not(:last-child) {
  border-bottom: 1px solid var(--color-border-light);
}

.version-item .item-label {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.version-item .item-value {
  font-size: 13px;
  color: var(--color-text-primary);
  font-weight: 500;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

.developer-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: var(--color-bg-page);
  border-radius: 12px;
  text-decoration: none;
  transition: background 0.2s;
}

.developer-card:hover {
  background: var(--color-bg-active, #f5f5f5);
}

.developer-avatar {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  object-fit: cover;
}

.developer-info {
  flex: 1;
  text-align: left;
}

.developer-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.developer-role {
  margin-top: 2px;
  font-size: 13px;
  color: var(--color-text-tertiary);
}

.developer-arrow {
  color: var(--color-text-tertiary);
}

.about-footer {
  margin-top: 20px;
  font-size: 13px;
  color: var(--color-text-tertiary);
}

/* Powered by */
.powered-by {
  margin-top: auto;
  padding-top: 48px;
  text-align: center;
  font-size: 13px;
  color: var(--color-text-tertiary);
  padding-bottom: 12px;
}

.powered-by a {
  color: var(--color-transfer);
  text-decoration: none;
  font-weight: 500;
}

.powered-by a:hover {
  text-decoration: underline;
}
</style>

<style>
/* 关于弹窗样式覆盖 */
.about-dialog .el-dialog__header {
  display: none !important;
}

.about-dialog .el-dialog__body {
  padding: 24px;
}

.about-dialog .el-dialog {
  border-radius: 20px;
  overflow: hidden;
}

/* 暗色模式 */
html.dark .data-card {
  background: rgba(40, 40, 40, 0.6);
  border-color: rgba(255, 255, 255, 0.1);
}

html.dark .data-card:hover {
  background: rgba(50, 50, 50, 0.8);
}

html.dark .appearance-card {
  background: rgba(40, 40, 40, 0.6);
  border-color: rgba(255, 255, 255, 0.1);
}

html.dark .developer-card:hover {
  background: rgba(60, 60, 60, 0.6);
}

html.dark .about-close {
  color: var(--color-text-tertiary);
}

html.dark .about-close:hover {
  background: rgba(255, 255, 255, 0.1);
  color: var(--color-text-secondary);
}

/* 暗色模式下的卡片图标 */
html.dark .card-icon {
  background: var(--color-transfer);
}

html.dark .data-card.ai-unconfigured .card-icon.ai-icon {
  background: var(--color-text-quaternary);
}

/* AI 配置对话框样式 */
.ai-config-message-box .el-message-box__header {
  display: none;
}

.ai-config-message-box .el-message-box__content {
  padding: 0;
}

.ai-config-message-box .el-message-box__btns {
  padding: 16px 24px 24px;
}

.ai-config-message-box .el-message-box {
  border-radius: 16px;
  overflow: hidden;
  width: 480px;
  max-width: 90vw;
}

.ai-config-dialog {
  text-align: center;
  padding: 32px 24px 16px;
}

.ai-config-dialog .dialog-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 72px;
  height: 72px;
  background: linear-gradient(135deg, rgba(250, 173, 20, 0.15) 0%, rgba(250, 140, 22, 0.15) 100%);
  border-radius: 50%;
  margin-bottom: 20px;
  color: #faad14;
}

.ai-config-dialog .dialog-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 8px 0;
}

.ai-config-dialog .dialog-desc {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin: 0 0 16px 0;
}

.ai-config-dialog .dialog-desc code {
  background: rgba(0, 0, 0, 0.06);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
}

.ai-config-dialog .missing-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 20px;
}

.ai-config-dialog .missing-item {
  background: rgba(245, 34, 45, 0.08);
  border: 1px solid rgba(245, 34, 45, 0.2);
  border-radius: 8px;
  padding: 10px 16px;
}

.ai-config-dialog .missing-item code {
  color: #f5222d;
  font-size: 13px;
  font-weight: 500;
}

.ai-config-dialog .config-example {
  background: var(--color-bg-page, #f5f5f5);
  border-radius: 12px;
  padding: 16px;
  text-align: left;
}

.ai-config-dialog .example-title {
  font-size: 12px;
  color: var(--color-text-tertiary);
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.ai-config-dialog .config-example pre {
  margin: 0;
  font-size: 12px;
  line-height: 1.6;
  color: var(--color-text-secondary);
  white-space: pre-wrap;
  word-break: break-all;
}

.ai-config-dialog .config-fields {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 8px;
}

.ai-config-dialog .config-field {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 13px;
  text-align: left;
}

.ai-config-dialog .config-field code {
  flex-shrink: 0;
  background: rgba(102, 126, 234, 0.1);
  color: #667eea;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.ai-config-dialog .config-field span {
  color: var(--color-text-secondary);
  line-height: 1.4;
}

/* 暗色模式 */
html.dark .ai-config-dialog .dialog-desc code {
  background: rgba(255, 255, 255, 0.1);
}

html.dark .ai-config-dialog .missing-item {
  background: rgba(245, 34, 45, 0.15);
  border-color: rgba(245, 34, 45, 0.3);
}

html.dark .ai-config-dialog .config-example {
  background: rgba(0, 0, 0, 0.2);
}
</style>
