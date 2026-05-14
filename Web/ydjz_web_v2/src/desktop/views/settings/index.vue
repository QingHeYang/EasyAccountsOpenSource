<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowRight, Close } from '@element-plus/icons-vue'
import {
  ArrowLeftRight,
  Wallet,
  Tags,
  Layers2,
  AlarmClock,
  Sparkles,
  Settings,
  FolderOpen,
  Info,
  Newspaper,
  LogOut,
} from 'lucide-vue-next'
import { homeApi, type VersionInfo, type UpdateInfo, type AuthConfig, type BackupConfig } from '@shared/api/home'
import { aiApi, type AiHealthResponse } from '@shared/api/ai'
import logoUrl from '@shared/assets/logo.png'
import MarkdownIt from 'markdown-it'

const md = new MarkdownIt()
import './styles.css'

// 子组件
import ActionManager from './ActionManager.vue'
import AccountManager from './AccountManager.vue'
import TypeManager from './TypeManager.vue'
import TemplateManager from './TemplateManager.vue'
import AiSettings from './AiSettings.vue'
import SystemSettings from './SystemSettings.vue'
import BackupManager from './BackupManager.vue'
import NoticeDrawer from './NoticeDrawer.vue'
import ScheduledFlowManager from './ScheduledFlowManager.vue'

const router = useRouter()

// AI 服务状态
const aiHealth = ref<AiHealthResponse | null>(null)
const aiServiceAvailable = computed(() => aiHealth.value !== null)
const aiConfigured = computed(() => aiHealth.value?.data?.llm?.configured === true)

// 关于弹窗
const showAbout = ref(false)
const versions = ref<VersionInfo>({
  release: '',
  versionCode: 0,
  fontBranch: '',
  backendBranch: '',
  mysqlBranch: '',
  agentBranch: '',
})
const authConfig = ref<AuthConfig | null>(null)
const backupConfig = ref<BackupConfig | null>(null)
const updateInfo = ref<UpdateInfo | null>(null)

// 是否有更新
const hasUpdate = computed(() => updateInfo.value !== null)

// 更新详情弹窗
const showUpdateDialog = ref(false)

// 渲染 changelog 为 HTML
const changelogHtml = computed(() => {
  if (!updateInfo.value?.changelog) return ''
  return md.render(updateInfo.value.changelog)
})

// 系统设置抽屉
const showSystemSettings = ref(false)

// 公告抽屉
const showNoticeDrawer = ref(false)
const noticeDrawerRef = ref<InstanceType<typeof NoticeDrawer> | null>(null)

// 是否有未读公告
const hasUnreadNotice = computed(() => noticeDrawerRef.value?.hasUnread ?? false)

async function loadSystemConfig() {
  try {
    const res = await homeApi.getSystemConfig()
    versions.value = res.data.data.versions
    authConfig.value = res.data.data.auth
    backupConfig.value = res.data.data.backup
    updateInfo.value = res.data.data.update
    // 如果不需要认证，清除 token
    if (authConfig.value && !authConfig.value.enable) {
      localStorage.removeItem('token')
    }
  } catch (err) {
    console.error('获取系统配置失败', err)
  }
}

// 是否显示退出登录（需要认证才显示）
const showLogout = computed(() => authConfig.value?.enable !== false)

function openAbout() {
  showAbout.value = true
  if (!versions.value.release) {
    loadSystemConfig()
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

// 数据管理项
const dataItems = [
  { key: 'action', title: '收支管理', desc: '管理收入和支出类型', icon: ArrowLeftRight },
  { key: 'account', title: '账户管理', desc: '管理银行卡、现金等账户', icon: Wallet },
  { key: 'type', title: '分类管理', desc: '管理收支分类', icon: Tags },
  { key: 'template', title: '快记模板', desc: '快速记账预填模板', icon: Layers2 },
  { key: 'scheduledFlow', title: '定时记账', desc: '周期性自动生成真实流水', icon: AlarmClock },
]

// 系统管理项
const systemItems = [
  { key: 'ai', title: 'AI+ 设置', desc: 'Token 统计与 MCP 状态', icon: Sparkles },
  { key: 'systemSettings', title: '系统设置', desc: '鉴权 / 邮件 / 提醒 / 备份 / 版本', icon: Settings },
]

// 检测 AI 服务
async function checkAiService() {
  aiHealth.value = await aiApi.checkHealth()
}

// 子组件抽屉状态
const showActionDrawer = ref(false)
const showAccountDrawer = ref(false)
const showTypeDrawer = ref(false)
const showTemplateDrawer = ref(false)
const showScheduledFlowDrawer = ref(false)
const showAiDrawer = ref(false)
const showBackupDrawer = ref(false)

function openDrawer(key: string) {
  if (key === 'action') {
    showActionDrawer.value = true
  } else if (key === 'account') {
    showAccountDrawer.value = true
  } else if (key === 'type') {
    showTypeDrawer.value = true
  } else if (key === 'template') {
    showTemplateDrawer.value = true
  } else if (key === 'scheduledFlow') {
    showScheduledFlowDrawer.value = true
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
  } else if (key === 'systemSettings') {
    showSystemSettings.value = true
  } else if (key === 'backup') {
    showBackupDrawer.value = true
  }
}

// ScheduledFlowManager ref，用于从通知中心跳转时打开指定规则
const scheduledFlowRef = ref<InstanceType<typeof ScheduledFlowManager> | null>(null)

async function openScheduledRuleById(ruleId: number) {
  showScheduledFlowDrawer.value = true
  await nextTick()
  scheduledFlowRef.value?.openRuleById(ruleId)
}

function handleOpenScheduledRuleEvent(e: Event) {
  const ruleId = (e as CustomEvent).detail?.ruleId
  if (ruleId) openScheduledRuleById(Number(ruleId))
}

onMounted(() => {
  loadSystemConfig()
  checkAiService()

  // 通知跳转：首次进入设置页时读 sessionStorage
  const stored = sessionStorage.getItem('pendingOpenScheduledRule')
  if (stored) {
    sessionStorage.removeItem('pendingOpenScheduledRule')
    openScheduledRuleById(Number(stored))
  }
  // 已在设置页内时用全局事件触发
  window.addEventListener('open-scheduled-rule', handleOpenScheduledRuleEvent)
})

onUnmounted(() => {
  window.removeEventListener('open-scheduled-rule', handleOpenScheduledRuleEvent)
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
              <component :is="item.icon" :size="24" :stroke-width="1.75" />
            </div>
            <div class="card-info">
              <div class="card-title">{{ item.title }}</div>
              <div class="card-desc">{{ item.desc }}</div>
            </div>
            <el-icon class="card-arrow"><ArrowRight /></el-icon>
          </div>
        </div>
      </div>

      <!-- 系统管理 -->
      <div class="setting-section">
        <h2 class="section-title">系统管理</h2>
        <div class="data-grid">
          <!-- AI 设置卡片 (仅在 AI 服务可用时显示) -->
          <div
            v-if="aiServiceAvailable"
            class="data-card"
            :class="{ 'ai-unconfigured': !aiConfigured }"
            @click="openDrawer('ai')"
          >
            <div class="card-icon ai-icon">
              <Sparkles :size="24" :stroke-width="1.75" />
            </div>
            <div class="card-info">
              <div class="card-title">
                AI+ 设置
                <el-tag v-if="!aiConfigured" size="small" type="warning" style="margin-left: 8px;">未配置</el-tag>
              </div>
              <div class="card-desc">Token 统计与 MCP 状态</div>
            </div>
            <el-icon class="card-arrow"><ArrowRight /></el-icon>
          </div>
          <!-- 系统设置卡片 -->
          <div class="data-card" @click="openDrawer('systemSettings')">
            <div class="card-icon system-icon">
              <Settings :size="24" :stroke-width="1.75" />
            </div>
            <div class="card-info">
              <div class="card-title">系统设置</div>
              <div class="card-desc">鉴权 / 邮件 / 提醒 / 备份 / 版本</div>
            </div>
            <el-icon class="card-arrow"><ArrowRight /></el-icon>
          </div>
          <!-- 数据备份卡片 -->
          <div class="data-card" @click="openDrawer('backup')">
            <div class="card-icon backup-icon">
              <FolderOpen :size="24" :stroke-width="1.75" />
            </div>
            <div class="card-info">
              <div class="card-title">数据备份</div>
              <div class="card-desc">备份与恢复数据库</div>
            </div>
            <el-icon class="card-arrow"><ArrowRight /></el-icon>
          </div>
        </div>
      </div>

      <!-- 其他 -->
      <div class="setting-section">
        <h2 class="section-title">其他</h2>
        <div class="other-actions">
          <el-button size="large" class="about-btn" @click="openAbout">
            <Info :size="16" :stroke-width="1.75" class="btn-icon" />
            <span>关于</span>
            <span v-if="hasUpdate" class="update-dot"></span>
          </el-button>
          <el-button size="large" class="notice-btn" @click="showNoticeDrawer = true">
            <Newspaper :size="16" :stroke-width="1.75" class="btn-icon" />
            <span>公告</span>
            <span v-if="hasUnreadNotice" class="notice-dot"></span>
          </el-button>
          <el-button v-if="showLogout" size="large" type="danger" plain @click="onLogout">
            <LogOut :size="16" :stroke-width="1.75" class="btn-icon" />
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

        <!-- 版本标签 -->
        <div class="about-version-tag">
          <span class="version-label">Version</span>
          <span class="version-value">{{ versions.release || '...' }} ({{ versions.versionCode || '...' }})</span>
        </div>

        <!-- 更新提示 -->
        <div v-if="updateInfo" class="update-banner" @click="showUpdateDialog = true">
          <span class="update-icon">🎉</span>
          <span class="update-text">发现新版本 {{ updateInfo.version }} ({{ updateInfo.versionCode }})</span>
          <span class="update-link">查看详情</span>
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

    <!-- 更新详情弹窗 -->
    <el-dialog
      v-model="showUpdateDialog"
      title="发现新版本"
      width="420"
      class="update-dialog"
    >
      <div v-if="updateInfo" class="update-content">
        <div class="update-header">
          <div class="update-version">{{ updateInfo.version }} ({{ updateInfo.versionCode }})</div>
          <div class="update-date">发布于 {{ updateInfo.releaseDate }}</div>
        </div>
        <div class="update-changelog">
          <div class="changelog-title">更新内容</div>
          <div class="changelog-content markdown-body" v-html="changelogHtml"></div>
        </div>
        <a
          href="https://mercys-organization-2.gitbook.io/easyaccounts/version"
          target="_blank"
          class="update-tip"
        >
          <Info :size="14" :stroke-width="1.75" />
          <span>查看更新指南</span>
          <el-icon class="tip-arrow"><ArrowRight /></el-icon>
        </a>
      </div>
      <template #footer>
        <el-button type="primary" @click="showUpdateDialog = false">我知道了</el-button>
      </template>
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
    <ScheduledFlowManager ref="scheduledFlowRef" v-model:visible="showScheduledFlowDrawer" />
    <AiSettings v-model:visible="showAiDrawer" />
    <SystemSettings
      v-model:visible="showSystemSettings"
      :versions="versions"
    />
    <BackupManager v-model:visible="showBackupDrawer" />
    <NoticeDrawer ref="noticeDrawerRef" v-model:visible="showNoticeDrawer" />
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

/* 系统信息卡片样式 */
.card-icon.system-icon {
  background: var(--color-transfer);
}

/* 数据备份卡片样式 */
.card-icon.backup-icon {
  background: var(--color-transfer);
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
}

.version-label {
  color: var(--color-text-tertiary);
}

.version-value {
  color: var(--color-transfer);
  font-weight: 600;
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

/* 关于按钮红点 */
.about-btn {
  position: relative;
}

.update-dot {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 8px;
  height: 8px;
  background: var(--color-expense);
  border-radius: 50%;
  box-shadow: 0 0 0 2px var(--color-bg-card);
}

/* 更新提示横幅 */
.update-banner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: 16px;
  padding: 12px 16px;
  background: linear-gradient(135deg, rgba(82, 196, 26, 0.12) 0%, rgba(24, 144, 255, 0.12) 100%);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.update-banner:hover {
  background: linear-gradient(135deg, rgba(82, 196, 26, 0.18) 0%, rgba(24, 144, 255, 0.18) 100%);
}

.update-icon {
  font-size: 16px;
}

.update-text {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.update-link {
  font-size: 13px;
  color: var(--color-transfer);
}

/* 更新详情弹窗 */
.update-content {
  padding: 8px 0;
}

.update-header {
  text-align: center;
  margin-bottom: 20px;
}

.update-version {
  font-size: 28px;
  font-weight: 700;
  color: var(--color-income);
}

.update-date {
  margin-top: 4px;
  font-size: 13px;
  color: var(--color-text-tertiary);
}

.update-changelog {
  background: var(--color-bg-page);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
}

.changelog-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 12px;
}

.changelog-content {
  font-size: 14px;
  line-height: 1.8;
  color: var(--color-text-secondary);
}

.changelog-content.markdown-body :deep(h1),
.changelog-content.markdown-body :deep(h2),
.changelog-content.markdown-body :deep(h3) {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 8px 0;
}

.changelog-content.markdown-body :deep(ul),
.changelog-content.markdown-body :deep(ol) {
  margin: 0;
  padding-left: 20px;
}

.changelog-content.markdown-body :deep(li) {
  margin: 4px 0;
}

.changelog-content.markdown-body :deep(p) {
  margin: 0 0 8px 0;
}

.changelog-content.markdown-body :deep(p:last-child) {
  margin-bottom: 0;
}

.update-tip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 14px;
  background: var(--color-transfer-bg);
  border-radius: 8px;
  font-size: 13px;
  color: var(--color-transfer);
  text-decoration: none;
  transition: all 0.2s;
}

.update-tip:hover {
  background: rgba(24, 144, 255, 0.15);
}

.update-tip span {
  flex: 1;
}

.update-tip .tip-arrow {
  font-size: 14px;
}

/* 公告按钮 */
.notice-btn {
  position: relative;
}

.notice-dot {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 8px;
  height: 8px;
  background: var(--color-expense);
  border-radius: 50%;
  box-shadow: 0 0 0 2px var(--color-bg-card);
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

/* el-button 内 Lucide 图标的间距（Lucide 不是 el-icon，不会自动应用 EP 间距规则） */
.el-button .btn-icon {
  margin-right: 6px;
  flex-shrink: 0;
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
