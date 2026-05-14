<script setup lang="ts">
import { ref, computed, onMounted, onActivated } from 'vue'
import { showToast } from 'vant'
import { useThemeStore } from '@shared/stores/theme'
import { useSmartBack } from '@shared/composables/useSmartBack'
import {
  systemConfigApi,
  type SystemConfigOverview,
} from '@shared/api/systemConfig'
import { homeApi, type VersionInfo } from '@shared/api/home'
import { isHandledError } from '@shared/api/request'
import { Lock, Mail, Bell, FolderOpen, Calendars, Sun, Moon, Monitor } from 'lucide-vue-next'

const { smartBack } = useSmartBack()
const themeStore = useThemeStore()

const overview = ref<SystemConfigOverview | null>(null)
const versions = ref<VersionInfo>({
  release: '',
  versionCode: 0,
  fontBranch: '',
  backendBranch: '',
  mysqlBranch: '',
  agentBranch: '',
})

const themeOptions = [
  { value: 'light', label: '浅色', icon: Sun },
  { value: 'dark', label: '深色', icon: Moon },
  { value: 'system', label: '跟随系统', icon: Monitor },
] as const

async function loadOverview() {
  try {
    const res = await systemConfigApi.getOverview()
    overview.value = res.data.data
  } catch (err) {
    if (!isHandledError(err)) showToast('加载系统设置失败')
  }
}

async function loadVersions() {
  try {
    const res = await homeApi.getSystemConfig()
    versions.value = res.data.data.versions
  } catch {
    // 静默
  }
}

/* 摘要尽量短，避免 cell 换行 */

const authSummary = computed(() => {
  const c = overview.value?.auth
  if (!c) return ''
  if (!c.loginEnable) return '未启用'
  const m = c.tokenExpiredMinutes
  return m >= 60 ? `${Math.floor(m / 60)} 小时` : `${m} 分钟`
})

const mailSummary = computed(() => {
  const c = overview.value?.mail
  if (!c) return ''
  if (!c.isConfigured) return '未配置'
  return `${c.toListCount} 位收件人`
})

const reminderSummary = computed(() => {
  const c = overview.value?.scheduledFlow
  if (!c) return ''
  return `提前 ${c.remindBeforeDays} 天 · ${(c.remindTime || '').substring(0, 5)}`
})

const backupSummary = computed(() => {
  const c = overview.value?.backup
  if (!c) return ''
  if (!c.enabled) return '未启用'
  const time = (c.time || '').substring(0, 5)
  if (c.frequency === 'daily') return `每日 ${time}`
  if (c.frequency === 'weekly') return `每周 · ${time}`
  return `每月 · ${time}`
})

const autoExcelSummary = computed(() => {
  const c = overview.value?.autoExcel
  if (!c) return ''
  if (!c.enabled) return '未启用'
  const t = c.target === 'CURRENT_MONTH' ? '本月' : '上月'
  return `${c.dayOfMonth} 号 · ${t}`
})

const versionItems = computed(() => [
  { label: '前端', value: versions.value.fontBranch || '-' },
  { label: '后端', value: versions.value.backendBranch || '-' },
  { label: '数据库', value: versions.value.mysqlBranch || '-' },
  { label: 'AI Agent', value: versions.value.agentBranch || '-' },
])

function onBack() {
  smartBack('/setting')
}

function onSetTheme(mode: 'light' | 'dark' | 'system') {
  themeStore.set(mode)
}

onMounted(() => {
  window.scrollTo(0, 0)
  loadOverview()
  loadVersions()
})

// 从子页面返回时自动刷新 overview
onActivated(() => {
  loadOverview()
})
</script>

<template>
  <div class="system-settings-page">
    <!-- 顶部导航 -->
    <div class="page-header">
      <div class="header-left" @click="onBack">
        <van-icon name="arrow-left" size="20" />
      </div>
      <div class="header-title">系统设置</div>
      <div class="header-right-placeholder"></div>
    </div>

    <div class="page-body">
      <!-- 外观 -->
      <van-cell-group inset title="外观">
        <div class="theme-selector">
          <div
            v-for="opt in themeOptions"
            :key="opt.value"
            class="theme-option"
            :class="{ active: themeStore.mode === opt.value }"
            @click="onSetTheme(opt.value)"
          >
            <component :is="opt.icon" :size="22" :stroke-width="1.75" class="theme-icon" />
            <span class="theme-label">{{ opt.label }}</span>
            <van-icon
              v-if="themeStore.mode === opt.value"
              name="success"
              size="14"
              class="theme-check"
            />
          </div>
        </div>
      </van-cell-group>

      <!-- 鉴权 -->
      <van-cell-group inset>
        <van-cell
          is-link
          :value="authSummary"
          to="/setting/system/auth"
          class="m-link-cell"
        >
          <template #icon>
            <div class="m-cell-icon">
              <Lock :size="18" :stroke-width="1.75" />
            </div>
          </template>
          <template #title>
            <span class="m-cell-title">鉴权设置</span>
          </template>
        </van-cell>
      </van-cell-group>

      <!-- 邮件 -->
      <van-cell-group inset>
        <van-cell
          is-link
          :value="mailSummary"
          to="/setting/system/mail"
          class="m-link-cell"
        >
          <template #icon>
            <div class="m-cell-icon">
              <Mail :size="18" :stroke-width="1.75" />
            </div>
          </template>
          <template #title>
            <span class="m-cell-title">邮件设置</span>
          </template>
        </van-cell>
      </van-cell-group>

      <!-- 提醒 -->
      <van-cell-group inset>
        <van-cell
          is-link
          :value="reminderSummary"
          to="/setting/system/reminder"
          class="m-link-cell"
        >
          <template #icon>
            <div class="m-cell-icon">
              <Bell :size="18" :stroke-width="1.75" />
            </div>
          </template>
          <template #title>
            <span class="m-cell-title">提醒设置</span>
          </template>
        </van-cell>
      </van-cell-group>

      <!-- 备份 -->
      <van-cell-group inset>
        <van-cell
          is-link
          :value="backupSummary"
          to="/setting/system/backup"
          class="m-link-cell"
        >
          <template #icon>
            <div class="m-cell-icon">
              <FolderOpen :size="18" :stroke-width="1.75" />
            </div>
          </template>
          <template #title>
            <span class="m-cell-title">备份设置</span>
          </template>
        </van-cell>
      </van-cell-group>

      <!-- 月度报表 -->
      <van-cell-group inset>
        <van-cell
          is-link
          :value="autoExcelSummary"
          to="/setting/system/auto-excel"
          class="m-link-cell"
        >
          <template #icon>
            <div class="m-cell-icon">
              <Calendars :size="18" :stroke-width="1.75" />
            </div>
          </template>
          <template #title>
            <span class="m-cell-title">月度报表生成</span>
          </template>
        </van-cell>
      </van-cell-group>

      <!-- 版本信息 -->
      <van-cell-group inset title="版本信息">
        <van-cell
          v-for="item in versionItems"
          :key="item.label"
          :title="item.label"
        >
          <template #value>
            <span class="version-value">{{ item.value }}</span>
          </template>
        </van-cell>
      </van-cell-group>
    </div>
  </div>
</template>

<style scoped>
.system-settings-page {
  min-height: 100vh;
  background: var(--color-bg-page);
}

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

.header-left {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: var(--color-bg-card);
  color: var(--color-text-primary);
}

.header-left:active {
  opacity: 0.7;
}

.header-right-placeholder {
  width: 40px;
  height: 40px;
}

.header-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.page-body {
  padding: 76px 0 32px;
}

/* === cell-group 之间统一加间距，避免坨在一起 === */
.page-body :deep(.van-cell-group--inset) {
  margin-bottom: 12px;
}

.page-body :deep(.van-cell-group--inset:last-child) {
  margin-bottom: 0;
}

/* === 外观选择器（朴素 emoji 卡片） === */
.theme-selector {
  display: flex;
  gap: 10px;
  padding: 12px 14px;
}

.theme-option {
  flex: 1;
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 14px 6px 12px;
  background: var(--color-bg-page);
  border: 2px solid transparent;
  border-radius: 12px;
  transition: transform 0.15s;
}

.theme-option:active {
  transform: scale(0.96);
}

.theme-icon {
  display: block;
  color: var(--color-text-secondary);
}

.theme-option.active .theme-icon {
  color: var(--color-transfer);
}

.theme-label {
  font-size: 12px;
  color: var(--color-text-secondary);
  font-weight: 500;
}

.theme-option.active {
  border-color: var(--color-transfer);
  background: var(--color-transfer-bg);
}

.theme-option.active .theme-label {
  color: var(--color-transfer);
  font-weight: 600;
}

.theme-check {
  position: absolute;
  top: 8px;
  right: 8px;
  color: var(--color-transfer);
}

html.dark .theme-option {
  background: rgba(255, 255, 255, 0.04);
}

html.dark .theme-option.active {
  background: rgba(116, 192, 252, 0.14);
}

/* === iOS 风格 cell 彩色 icon 方块 === */
.m-cell-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  margin-right: 8px;
  flex-shrink: 0;
  color: var(--color-text-secondary);
}

.m-cell-title {
  font-size: 14px;
  color: var(--color-text-primary);
  font-weight: 500;
}

/* cell value 单行不换行（防止"月度报表"摘要折成两行） */
.m-link-cell :deep(.van-cell__value) {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 60%;
  font-size: 13px;
  color: var(--color-text-tertiary);
}

/* 版本号 mono 字体 */
.version-value {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  color: var(--color-text-primary);
  font-size: 13px;
}
</style>

<style>
.system-settings-page .page-header {
  background: rgba(245, 245, 245, 0.8);
}

html.dark .system-settings-page .page-header {
  background: rgba(10, 10, 10, 0.8);
}
</style>
