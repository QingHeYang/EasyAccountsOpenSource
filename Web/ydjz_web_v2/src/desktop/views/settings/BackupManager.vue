<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  UploadFilled,
  Download,
  RefreshRight,
  WarningFilled,
  Check
} from '@element-plus/icons-vue'
import { backupApi } from '@shared/api'

defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
}>()

// 文件输入框引用
const fileInputRef = ref<HTMLInputElement | null>(null)

// 备份状态
const isBackingUp = ref(false)
const backupResult = ref<string | null>(null)

// 恢复状态
const isRestoring = ref(false)
const selectedFile = ref<File | null>(null)
const showRestoreSuccess = ref(false)
const restoreCountdown = ref(30)

// 执行备份
async function doBackup() {
  isBackingUp.value = true
  backupResult.value = null

  try {
    const res = await backupApi.backup()
    if (res.data.code === 0) {
      backupResult.value = res.data.data
      ElMessage.success('备份成功')
    } else {
      ElMessage.error(res.data.msg || '备份失败')
    }
  } catch (err: any) {
    ElMessage.error(err.message || '备份失败')
  } finally {
    isBackingUp.value = false
  }
}

// 选择文件
function onFileChange(e: Event) {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    if (!file.name.endsWith('.sql')) {
      ElMessage.warning('请选择 .sql 格式的备份文件')
      target.value = ''
      return
    }
    selectedFile.value = file
  }
}

// 拖拽上传
function onDrop(e: DragEvent) {
  e.preventDefault()
  const file = e.dataTransfer?.files?.[0]
  if (file) {
    if (!file.name.endsWith('.sql')) {
      ElMessage.warning('请选择 .sql 格式的备份文件')
      return
    }
    selectedFile.value = file
  }
}

function onDragOver(e: DragEvent) {
  e.preventDefault()
}

// 清除选择的文件
function clearFile() {
  selectedFile.value = null
  // 重置 input
  if (fileInputRef.value) fileInputRef.value.value = ''
}

// 触发文件选择
function triggerFileSelect() {
  fileInputRef.value?.click()
}

// 执行恢复
async function doRestore() {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择备份文件')
    return
  }

  // 二次确认
  try {
    await ElMessageBox.prompt(
      `<div class="restore-confirm-content">
        <div class="warning-icon">
          <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M12 9v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <div class="warning-title">确认恢复数据？</div>
        <div class="warning-desc">此操作将<strong>覆盖当前所有数据</strong>，且无法撤销！</div>
        <div class="warning-tip">
          <div class="tip-icon">💡</div>
          <div class="tip-text">数据恢复成功后，系统将自动重启。如果无法成功登录，请手动执行以下命令重启服务：<br/><code>docker compose restart</code></div>
        </div>
        <div class="input-label">请输入 <span class="confirm-text">确认恢复</span> 以继续：</div>
      </div>`,
      '',
      {
        confirmButtonText: '恢复数据',
        cancelButtonText: '取消',
        confirmButtonClass: 'el-button--danger',
        inputPattern: /^确认恢复$/,
        inputErrorMessage: '请输入"确认恢复"',
        customClass: 'restore-confirm-dialog',
        dangerouslyUseHTMLString: true,
        showClose: false,
      }
    )
  } catch {
    return // 用户取消
  }

  isRestoring.value = true

  try {
    const res = await backupApi.restore(selectedFile.value)
    if (res.data.code === 0) {
      // 显示成功提示，30秒后跳转主页
      showRestoreSuccess.value = true
      restoreCountdown.value = 30

      const timer = setInterval(() => {
        restoreCountdown.value--
        if (restoreCountdown.value <= 0) {
          clearInterval(timer)
          window.location.href = '/'
        }
      }, 1000)
    } else {
      ElMessage.error(res.data.msg || '恢复失败')
    }
  } catch (err: any) {
    ElMessage.error(err.message || '恢复失败')
  } finally {
    isRestoring.value = false
  }
}
</script>

<template>
  <el-drawer
    :model-value="visible"
    title="数据备份"
    direction="rtl"
    size="420px"
    class="setting-drawer backup-drawer"
    :close-on-click-modal="!showRestoreSuccess"
    :close-on-press-escape="!showRestoreSuccess"
    :show-close="!showRestoreSuccess"
    @update:model-value="!showRestoreSuccess && emit('update:visible', $event)"
  >
    <div class="backup-content">
      <!-- 手动备份 -->
      <div class="backup-section">
        <div class="section-header">
          <el-icon :size="18"><Download /></el-icon>
          <span>手动备份</span>
        </div>
        <div class="section-body">
          <p class="section-desc">立即创建数据库备份文件，备份完成后会通过 WebHook 发送通知。</p>

          <el-button
            type="primary"
            size="large"
            :loading="isBackingUp"
            :disabled="isBackingUp"
            class="backup-btn"
            @click="doBackup"
          >
            <el-icon v-if="!isBackingUp"><Download /></el-icon>
            <span>{{ isBackingUp ? '备份中...' : '立即备份' }}</span>
          </el-button>

          <!-- 备份结果 -->
          <div v-if="backupResult" class="backup-result">
            <el-icon :size="16" class="result-icon"><Check /></el-icon>
            <span>备份文件：{{ backupResult }}</span>
          </div>
        </div>
      </div>

      <!-- 数据恢复 -->
      <div class="backup-section">
        <div class="section-header">
          <el-icon :size="18"><RefreshRight /></el-icon>
          <span>数据恢复</span>
        </div>
        <div class="section-body">
          <!-- 警告提示 -->
          <div class="restore-warning">
            <el-icon :size="16"><WarningFilled /></el-icon>
            <span>恢复将覆盖当前所有数据，请谨慎操作</span>
          </div>

          <!-- 文件上传区域 -->
          <div
            class="upload-area"
            :class="{ 'has-file': selectedFile }"
            @drop="onDrop"
            @dragover="onDragOver"
            @click="triggerFileSelect"
          >
            <input
              ref="fileInputRef"
              type="file"
              accept=".sql"
              style="display: none"
              @change="onFileChange"
            />

            <template v-if="selectedFile">
              <div class="file-info">
                <el-icon :size="32" class="file-icon"><UploadFilled /></el-icon>
                <div class="file-name">{{ selectedFile.name }}</div>
                <div class="file-size">{{ (selectedFile.size / 1024).toFixed(1) }} KB</div>
              </div>
              <el-button
                size="small"
                text
                class="clear-btn"
                @click.stop="clearFile"
              >
                重新选择
              </el-button>
            </template>

            <template v-else>
              <el-icon :size="40" class="upload-icon"><UploadFilled /></el-icon>
              <div class="upload-text">点击或拖拽上传</div>
              <div class="upload-hint">支持 .sql 备份文件</div>
            </template>
          </div>

          <!-- 恢复按钮 -->
          <el-button
            type="danger"
            size="large"
            :loading="isRestoring"
            :disabled="!selectedFile || isRestoring"
            class="restore-btn"
            @click="doRestore"
          >
            <el-icon v-if="!isRestoring"><RefreshRight /></el-icon>
            <span>{{ isRestoring ? '恢复中...' : '恢复数据' }}</span>
          </el-button>
        </div>
      </div>
    </div>

    <!-- 恢复成功遮罩 -->
    <div v-if="showRestoreSuccess" class="restore-success-overlay">
      <div class="success-content">
        <div class="success-icon">
          <el-icon :size="64" color="#52C41A"><Check /></el-icon>
        </div>
        <div class="success-title">数据恢复成功</div>
        <div class="success-desc">正在重新加载数据，请稍候...</div>
        <div class="success-countdown">
          <el-progress
            type="circle"
            :percentage="Math.round(restoreCountdown / 30 * 100)"
            :width="80"
            :stroke-width="6"
            color="#52C41A"
          >
            <template #default>
              <span class="countdown-text">{{ restoreCountdown }}s</span>
            </template>
          </el-progress>
        </div>
        <div class="success-tip">即将跳转到主页</div>
      </div>
    </div>
  </el-drawer>
</template>

<style scoped>
.backup-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 区块 */
.backup-section {
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

.section-desc {
  margin: 0 0 16px 0;
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.6;
}

/* 备份按钮 */
.backup-btn {
  width: 100%;
}

/* 备份结果 */
.backup-result {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  padding: 10px 12px;
  background: rgba(82, 196, 26, 0.1);
  border-radius: 8px;
  font-size: 13px;
  color: var(--color-income);
}

.backup-result .result-icon {
  flex-shrink: 0;
}

/* 警告提示 */
.restore-warning {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: rgba(250, 173, 20, 0.1);
  border-radius: 8px;
  font-size: 13px;
  color: #d48806;
  margin-bottom: 16px;
}

/* 上传区域 */
.upload-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px 16px;
  background: var(--color-bg-card);
  border: 2px dashed var(--color-border);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.upload-area:hover {
  border-color: var(--color-transfer);
  background: rgba(24, 144, 255, 0.04);
}

.upload-area.has-file {
  border-style: solid;
  border-color: var(--color-transfer);
  background: rgba(24, 144, 255, 0.04);
}

.upload-icon {
  color: var(--color-text-tertiary);
  margin-bottom: 8px;
}

.upload-text {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.upload-hint {
  margin-top: 4px;
  font-size: 12px;
  color: var(--color-text-tertiary);
}

/* 已选文件 */
.file-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.file-icon {
  color: var(--color-transfer);
}

.file-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
  word-break: break-all;
  text-align: center;
}

.file-size {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.clear-btn {
  margin-top: 8px;
  color: var(--color-text-secondary);
}

/* 恢复按钮 */
.restore-btn {
  width: 100%;
  margin-top: 16px;
}

/* 恢复成功遮罩 */
.restore-success-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--color-bg-card);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.success-content {
  text-align: center;
  padding: 40px;
}

.success-icon {
  margin-bottom: 24px;
}

.success-title {
  font-size: 22px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 8px;
}

.success-desc {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin-bottom: 32px;
}

.success-countdown {
  display: flex;
  justify-content: center;
  margin-bottom: 24px;
}

.countdown-text {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-income);
}

.success-tip {
  font-size: 13px;
  color: var(--color-text-tertiary);
}
</style>

<!-- 暗色模式 -->
<style>
html.dark .backup-section {
  background: rgba(255, 255, 255, 0.03);
}

html.dark .section-header {
  border-color: rgba(255, 255, 255, 0.06);
}

html.dark .upload-area {
  background: rgba(255, 255, 255, 0.02);
  border-color: rgba(255, 255, 255, 0.1);
}

html.dark .upload-area:hover {
  background: rgba(24, 144, 255, 0.08);
  border-color: var(--color-transfer);
}

html.dark .upload-area.has-file {
  background: rgba(24, 144, 255, 0.08);
}

html.dark .restore-warning {
  background: rgba(250, 173, 20, 0.15);
  color: #faad14;
}

/* 恢复确认对话框 */
.restore-confirm-dialog .el-message-box__header {
  display: none;
}

.restore-confirm-dialog .el-message-box__content {
  padding: 0;
}

.restore-confirm-dialog .el-message-box {
  width: 420px;
  max-width: 90vw;
  border-radius: 16px;
  overflow: hidden;
}

.restore-confirm-dialog .el-message-box__btns {
  padding: 16px 24px 24px;
}

.restore-confirm-content {
  text-align: center;
  padding: 32px 24px 20px;
}

.restore-confirm-content .warning-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 72px;
  height: 72px;
  background: linear-gradient(135deg, rgba(245, 34, 45, 0.12) 0%, rgba(250, 84, 28, 0.12) 100%);
  border-radius: 50%;
  margin-bottom: 20px;
  color: #f5222d;
}

.restore-confirm-content .warning-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 8px;
}

.restore-confirm-content .warning-desc {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin-bottom: 16px;
}

.restore-confirm-content .warning-desc strong {
  color: #f5222d;
}

.restore-confirm-content .warning-tip {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  text-align: left;
  padding: 14px 16px;
  background: var(--color-bg-page, #f5f5f5);
  border-radius: 10px;
  margin-bottom: 20px;
}

.restore-confirm-content .tip-icon {
  flex-shrink: 0;
  font-size: 16px;
  line-height: 1.6;
}

.restore-confirm-content .tip-text {
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.6;
}

.restore-confirm-content .tip-text code {
  display: inline-block;
  margin-top: 8px;
  padding: 6px 12px;
  background: rgba(0, 0, 0, 0.06);
  border-radius: 6px;
  font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
  font-size: 12px;
  color: var(--color-text-primary);
}

html.dark .restore-confirm-content .tip-text code {
  background: rgba(255, 255, 255, 0.1);
}

.restore-confirm-content .input-label {
  font-size: 14px;
  color: var(--color-text-primary);
  margin-bottom: 8px;
  text-align: left;
}

.restore-confirm-content .confirm-text {
  color: #f5222d;
  font-weight: 600;
}

/* 暗色模式 */
html.dark .restore-confirm-content .warning-icon {
  background: linear-gradient(135deg, rgba(245, 34, 45, 0.2) 0%, rgba(250, 84, 28, 0.2) 100%);
}

html.dark .restore-confirm-content .warning-tip {
  background: rgba(255, 255, 255, 0.05);
}
</style>
