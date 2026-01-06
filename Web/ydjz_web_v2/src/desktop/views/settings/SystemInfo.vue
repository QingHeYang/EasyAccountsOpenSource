<script setup lang="ts">
import { computed } from 'vue'
import {
  Sunny,
  Moon,
  Monitor,
  Lock,
  Timer,
  User,
  Refresh,
  Check,
  Close,
  Monitor as VersionIcon
} from '@element-plus/icons-vue'
import { useThemeStore } from '@shared/stores/theme'
import type { VersionInfo, AuthConfig, BackupConfig } from '@shared/api/home'

const props = defineProps<{
  visible: boolean
  versions: VersionInfo
  authConfig: AuthConfig | null
  backupConfig: BackupConfig | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
}>()

const themeStore = useThemeStore()

// 主题选项
const themeOptions = [
  { value: 'light', label: '浅色', icon: Sunny },
  { value: 'dark', label: '深色', icon: Moon },
  { value: 'system', label: '跟随系统', icon: Monitor },
] as const

const currentTheme = computed({
  get: () => themeStore.mode,
  set: (val) => themeStore.set(val as 'light' | 'dark' | 'system')
})

// 认证状态文本
const authStatusText = computed(() => {
  if (!props.authConfig) return '加载中...'
  return props.authConfig.enable ? '已启用' : '未启用'
})

const authModeText = computed(() => {
  if (!props.authConfig) return '-'
  return props.authConfig.singleLogin ? '单点登录' : '多端登录'
})

const sessionTimeText = computed(() => {
  if (!props.authConfig) return '-'
  const minutes = props.authConfig.expiredMinutes
  if (minutes >= 60) {
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    return mins > 0 ? `${hours} 小时 ${mins} 分钟` : `${hours} 小时`
  }
  return `${minutes} 分钟`
})

// 备份状态
const backupStatusText = computed(() => {
  if (!props.backupConfig) return '加载中...'
  return props.backupConfig.description
})

// 版本列表
const versionItems = computed(() => [
  { label: '前端', value: props.versions.fontBranch || '-' },
  { label: '后端', value: props.versions.backendBranch || '-' },
  { label: '数据库', value: props.versions.mysqlBranch || '-' },
  { label: 'AI Agent', value: props.versions.agentBranch || '-' },
  { label: 'WebHook', value: props.versions.webhookBranch || '-' },
])
</script>

<template>
  <el-drawer
    :model-value="visible"
    title="系统信息"
    direction="rtl"
    size="420px"
    class="setting-drawer system-info-drawer"
    @update:model-value="emit('update:visible', $event)"
  >
    <div class="system-info-content">
      <!-- 外观设置 -->
      <div class="info-section">
        <div class="section-header">
          <el-icon :size="18"><Sunny /></el-icon>
          <span>外观设置</span>
        </div>
        <div class="section-body">
          <div class="theme-selector">
            <div
              v-for="opt in themeOptions"
              :key="opt.value"
              class="theme-option"
              :class="{ active: currentTheme === opt.value }"
              @click="currentTheme = opt.value"
            >
              <el-icon :size="20"><component :is="opt.icon" /></el-icon>
              <span>{{ opt.label }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 认证信息 -->
      <div class="info-section">
        <div class="section-header">
          <el-icon :size="18"><Lock /></el-icon>
          <span>认证信息</span>
        </div>
        <div class="section-body">
          <div class="info-grid">
            <div class="info-item">
              <div class="info-label">
                <el-icon :size="14"><Lock /></el-icon>
                <span>认证状态</span>
              </div>
              <div class="info-value">
                <el-tag
                  :type="authConfig?.enable ? 'success' : 'info'"
                  size="small"
                  effect="plain"
                >
                  {{ authStatusText }}
                </el-tag>
              </div>
            </div>
            <div class="info-item">
              <div class="info-label">
                <el-icon :size="14"><User /></el-icon>
                <span>登录模式</span>
              </div>
              <div class="info-value">{{ authModeText }}</div>
            </div>
            <div class="info-item">
              <div class="info-label">
                <el-icon :size="14"><Timer /></el-icon>
                <span>会话时长</span>
              </div>
              <div class="info-value">{{ sessionTimeText }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 备份信息 -->
      <div class="info-section">
        <div class="section-header">
          <el-icon :size="18"><Refresh /></el-icon>
          <span>备份信息</span>
        </div>
        <div class="section-body">
          <div class="backup-status">
            <div class="backup-icon" :class="{ valid: backupConfig?.valid }">
              <el-icon :size="20">
                <Check v-if="backupConfig?.valid" />
                <Close v-else />
              </el-icon>
            </div>
            <div class="backup-info">
              <div class="backup-text">{{ backupStatusText }}</div>
              <div class="backup-cron" v-if="backupConfig?.valid && backupConfig?.cron">
                <code>{{ backupConfig.cron }}</code>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 版本信息 -->
      <div class="info-section">
        <div class="section-header">
          <el-icon :size="18"><VersionIcon /></el-icon>
          <span>版本信息</span>
        </div>
        <div class="section-body">
          <div class="version-list">
            <div class="version-item" v-for="item in versionItems" :key="item.label">
              <span class="version-label">{{ item.label }}</span>
              <span class="version-value">{{ item.value }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </el-drawer>
</template>

<style scoped>
.system-info-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 信息区块 */
.info-section {
  background: var(--color-bg-page);
  border-radius: 12px;
  overflow: hidden;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 16px;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
  border-bottom: 1px solid var(--color-border-light);
}

.section-body {
  padding: 16px;
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
  padding: 16px 12px;
  background: var(--color-bg-card);
  border: 2px solid transparent;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.theme-option:hover {
  background: var(--color-bg-active);
}

.theme-option.active {
  border-color: var(--color-transfer);
  background: rgba(24, 144, 255, 0.08);
}

.theme-option span {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.theme-option.active span {
  color: var(--color-transfer);
  font-weight: 500;
}

/* 信息网格 */
.info-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background: var(--color-bg-card);
  border-radius: 8px;
}

.info-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.info-value {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-primary);
}

/* 备份状态 */
.backup-status {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px;
  background: var(--color-bg-card);
  border-radius: 10px;
}

.backup-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  background: rgba(245, 34, 45, 0.1);
  color: var(--color-expense);
}

.backup-icon.valid {
  background: rgba(82, 196, 26, 0.1);
  color: var(--color-income);
}

.backup-info {
  flex: 1;
}

.backup-text {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.backup-cron {
  margin-top: 4px;
}

.backup-cron code {
  font-size: 12px;
  padding: 2px 8px;
  background: var(--color-bg-page);
  border-radius: 4px;
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
  background: var(--color-bg-card);
  border-radius: 8px;
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

<!-- 暗色模式 -->
<style>
html.dark .info-section {
  background: rgba(255, 255, 255, 0.03);
}

html.dark .section-header {
  border-color: rgba(255, 255, 255, 0.06);
}

html.dark .theme-option {
  background: rgba(255, 255, 255, 0.04);
}

html.dark .theme-option:hover {
  background: rgba(255, 255, 255, 0.08);
}

html.dark .theme-option.active {
  background: rgba(116, 192, 252, 0.1);
  border-color: var(--color-transfer);
}

html.dark .info-item {
  background: rgba(255, 255, 255, 0.04);
}

html.dark .backup-status {
  background: rgba(255, 255, 255, 0.04);
}

html.dark .version-item {
  background: rgba(255, 255, 255, 0.04);
}

html.dark .backup-cron code {
  background: rgba(255, 255, 255, 0.06);
}
</style>
