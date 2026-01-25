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

// 备份状态
const isBackingUp = ref(false)
const backupResult = ref<string | null>(null)

// 恢复状态
const isRestoring = ref(false)
const selectedFile = ref<File | null>(null)

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
  const input = document.getElementById('backup-file-input') as HTMLInputElement
  if (input) input.value = ''
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
      '此操作将覆盖当前所有数据，且无法撤销！\n\n请输入"确认恢复"以继续：',
      '确认恢复数据',
      {
        confirmButtonText: '恢复',
        cancelButtonText: '取消',
        type: 'warning',
        inputPattern: /^确认恢复$/,
        inputErrorMessage: '请输入"确认恢复"',
        customClass: 'restore-confirm-dialog',
      }
    )
  } catch {
    return // 用户取消
  }

  isRestoring.value = true

  try {
    const res = await backupApi.restore(selectedFile.value)
    if (res.data.code === 0) {
      ElMessageBox.alert(
        '数据恢复成功！为确保数据一致性，请重新登录。',
        '恢复成功',
        {
          confirmButtonText: '重新登录',
          type: 'success',
          callback: () => {
            localStorage.removeItem('token')
            window.location.href = '/auth?mode=1'
          }
        }
      )
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
    @update:model-value="emit('update:visible', $event)"
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
            @click="() => document.getElementById('backup-file-input')?.click()"
          >
            <input
              id="backup-file-input"
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
  padding-bottom: 12px;
}

.restore-confirm-dialog .el-message-box__title {
  font-weight: 600;
}

.restore-confirm-dialog .el-message-box__message {
  white-space: pre-wrap;
}
</style>
