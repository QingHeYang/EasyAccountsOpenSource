<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useThemeStore } from '@shared/stores/theme'
import { homeApi, type VersionInfo, type AuthConfig, type BackupConfig } from '@shared/api/home'
import { useSmartBack } from '@shared/composables/useSmartBack'
import { showLoadingToast, closeToast, showToast } from 'vant'

const { smartBack } = useSmartBack()
const themeStore = useThemeStore()

// 数据
const loading = ref(false)
const versions = ref<VersionInfo>({
  release: '',
  versionCode: 0,
  fontBranch: '',
  backendBranch: '',
  mysqlBranch: '',
  agentBranch: '',
  webhookBranch: '',
})
const authConfig = ref<AuthConfig | null>(null)
const backupConfig = ref<BackupConfig | null>(null)

// 主题相关
const themeOptions = [
  { value: 'light', label: '浅色', icon: 'bulb-o' },
  { value: 'dark', label: '深色', icon: 'star-o' },
  { value: 'system', label: '跟随系统', icon: 'desktop-o' },
] as const

function onThemeChange(value: 'light' | 'dark' | 'system') {
  themeStore.set(value)
}

// 加载数据
async function loadSystemConfig() {
  loading.value = true
  showLoadingToast({ message: '加载中...', forbidClick: true, duration: 0 })
  try {
    const res = await homeApi.getSystemConfig()
    versions.value = res.data.data.versions
    authConfig.value = res.data.data.auth
    backupConfig.value = res.data.data.backup
  } catch (err) {
    console.error('获取系统配置失败', err)
    showToast('获取系统配置失败')
  } finally {
    loading.value = false
    closeToast()
  }
}

// 认证状态文本
const authStatusText = computed(() => {
  if (!authConfig.value) return '加载中...'
  return authConfig.value.enable ? '已启用' : '未启用'
})

const authModeText = computed(() => {
  if (!authConfig.value) return '-'
  return authConfig.value.singleLogin ? '单点登录' : '多端登录'
})

const sessionTimeText = computed(() => {
  if (!authConfig.value) return '-'
  const minutes = authConfig.value.expiredMinutes
  if (minutes >= 60) {
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    return mins > 0 ? `${hours} 小时 ${mins} 分钟` : `${hours} 小时`
  }
  return `${minutes} 分钟`
})

// 备份状态
const backupStatusText = computed(() => {
  if (!backupConfig.value) return '加载中...'
  return backupConfig.value.description
})

// 版本列表
const versionItems = computed(() => [
  { label: '前端', value: versions.value.fontBranch || '-' },
  { label: '后端', value: versions.value.backendBranch || '-' },
  { label: '数据库', value: versions.value.mysqlBranch || '-' },
  { label: 'AI Agent', value: versions.value.agentBranch || '-' },
  { label: 'WebHook', value: versions.value.webhookBranch || '-' },
])

// 返回
function onBack() {
  smartBack('/setting')
}

// 刷新
function onRefresh() {
  loadSystemConfig()
}

onMounted(() => {
  loadSystemConfig()
})
</script>

<template>
  <div class="system-info-page">
    <!-- 顶部导航 -->
    <div class="page-header">
      <div class="header-left" @click="onBack">
        <van-icon name="arrow-left" size="20" />
      </div>
      <div class="header-title">系统信息</div>
      <div class="header-right" @click="onRefresh">
        <van-icon name="replay" size="20" />
      </div>
    </div>

    <div class="page-body">
      <!-- 外观设置 -->
      <div class="info-card">
        <div class="card-header">
          <div class="card-icon theme">
            <van-icon name="bulb-o" size="20" />
          </div>
          <div class="card-title">外观设置</div>
        </div>
        <div class="theme-selector">
          <div
            v-for="opt in themeOptions"
            :key="opt.value"
            class="theme-option"
            :class="{ active: themeStore.mode === opt.value }"
            @click="onThemeChange(opt.value)"
          >
            <van-icon :name="opt.icon" size="20" />
            <span>{{ opt.label }}</span>
          </div>
        </div>
      </div>

      <!-- 认证信息 -->
      <div class="info-card">
        <div class="card-header">
          <div class="card-icon auth">
            <van-icon name="shield-o" size="20" />
          </div>
          <div class="card-title">认证信息</div>
        </div>
        <div class="info-list">
          <div class="info-item">
            <span class="info-label">认证状态</span>
            <van-tag
              :type="authConfig?.enable ? 'success' : 'default'"
              size="medium"
            >
              {{ authStatusText }}
            </van-tag>
          </div>
          <div class="info-item">
            <span class="info-label">登录模式</span>
            <span class="info-value">{{ authModeText }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">会话时长</span>
            <span class="info-value">{{ sessionTimeText }}</span>
          </div>
        </div>
      </div>

      <!-- 备份信息 -->
      <div class="info-card">
        <div class="card-header">
          <div class="card-icon backup" :class="{ valid: backupConfig?.valid }">
            <van-icon :name="backupConfig?.valid ? 'passed' : 'close'" size="20" />
          </div>
          <div class="card-title">备份信息</div>
        </div>
        <div class="backup-content">
          <div class="backup-text">{{ backupStatusText }}</div>
          <div v-if="backupConfig?.valid && backupConfig?.cron" class="backup-cron">
            <code>{{ backupConfig.cron }}</code>
          </div>
        </div>
      </div>

      <!-- 版本信息 -->
      <div class="info-card">
        <div class="card-header">
          <div class="card-icon version">
            <van-icon name="info-o" size="20" />
          </div>
          <div class="card-title">版本信息</div>
        </div>
        <div class="version-list">
          <div class="version-item" v-for="item in versionItems" :key="item.label">
            <span class="version-label">{{ item.label }}</span>
            <span class="version-value">{{ item.value }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.system-info-page {
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

/* 卡片 */
.info-card {
  background: var(--color-bg-card);
  border-radius: 16px;
  padding: 16px;
  margin-bottom: 12px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
}

.card-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
}

.card-icon.theme {
  background: rgba(250, 173, 20, 0.1);
  color: #faad14;
}

.card-icon.auth {
  background: var(--color-transfer-bg);
  color: var(--color-transfer);
}

.card-icon.backup {
  background: var(--color-expense-bg);
  color: var(--color-expense);
}

.card-icon.backup.valid {
  background: var(--color-income-bg);
  color: var(--color-income);
}

.card-icon.version {
  background: rgba(114, 46, 209, 0.1);
  color: #722ed1;
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
}

/* 主题选择器 */
.theme-selector {
  display: flex;
  gap: 10px;
}

.theme-option {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 14px 10px;
  background: var(--color-bg-page);
  border: 2px solid transparent;
  border-radius: 12px;
  color: var(--color-text-secondary);
  transition: all 0.2s;
}

.theme-option:active {
  opacity: 0.8;
}

.theme-option.active {
  border-color: var(--color-transfer);
  background: var(--color-transfer-bg);
  color: var(--color-transfer);
}

.theme-option span {
  font-size: 12px;
  font-weight: 500;
}

/* 信息列表 */
.info-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background: var(--color-bg-page);
  border-radius: 10px;
}

.info-label {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.info-value {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-primary);
}

/* 备份内容 */
.backup-content {
  padding: 12px;
  background: var(--color-bg-page);
  border-radius: 10px;
}

.backup-text {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.backup-cron {
  margin-top: 8px;
}

.backup-cron code {
  font-size: 12px;
  padding: 4px 10px;
  background: var(--color-bg-card);
  border-radius: 6px;
  color: var(--color-text-secondary);
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

/* 版本列表 */
.version-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.version-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background: var(--color-bg-page);
  border-radius: 10px;
}

.version-label {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.version-value {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-primary);
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}
</style>

<!-- 非 scoped 样式 -->
<style>
.system-info-page .page-header {
  background: rgba(245, 245, 245, 0.8);
}

html.dark .system-info-page .page-header {
  background: rgba(10, 10, 10, 0.8);
}

html.dark .system-info-page .theme-option {
  background: rgba(255, 255, 255, 0.04);
}

html.dark .system-info-page .theme-option.active {
  background: rgba(116, 192, 252, 0.1);
}

html.dark .system-info-page .info-item {
  background: rgba(255, 255, 255, 0.04);
}

html.dark .system-info-page .backup-content {
  background: rgba(255, 255, 255, 0.04);
}

html.dark .system-info-page .backup-cron code {
  background: rgba(255, 255, 255, 0.06);
}

html.dark .system-info-page .version-item {
  background: rgba(255, 255, 255, 0.04);
}
</style>
