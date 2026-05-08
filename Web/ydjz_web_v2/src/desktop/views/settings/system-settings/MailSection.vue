<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  EditPen,
  Promotion,
  InfoFilled,
  Delete,
  CircleCheckFilled,
  CircleCloseFilled,
} from '@element-plus/icons-vue'
import { Mail } from 'lucide-vue-next'
import {
  systemConfigApi,
  type MailOverview,
  type MailConfig,
  type MailConfigUpdate,
} from '@shared/api/systemConfig'
import { isHandledError } from '@shared/api/request'

const props = defineProps<{
  data: MailOverview
}>()

const emit = defineEmits<{
  (e: 'updated'): void
}>()

/* ---- 编辑对话框 ---- */

const showDialog = ref(false)
const loadingDetail = ref(false)
const saving = ref(false)
const testing = ref(false)

// 完整邮件配置（编辑时调 getMail 拿）
const fullConfig = ref<MailConfig | null>(null)

const form = reactive({
  smtpServer: '',
  smtpPort: '465',
  fromEmail: '',
  password: '',
  toList: '',
  sendSqlBackup: false,
  sendExcel: false,
})
const passwordTouched = ref(false)
// 字段级 dirty 比对快照（不含 password，password 单独判定）
const formSnapshot = ref<string>('')

const recipientCount = computed(() => {
  return form.toList
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean).length
})

function snapshotForm(): string {
  return JSON.stringify({
    smtpServer: form.smtpServer,
    smtpPort: form.smtpPort,
    fromEmail: form.fromEmail,
    toList: form.toList,
    sendSqlBackup: form.sendSqlBackup,
    sendExcel: form.sendExcel,
  })
}

const dirty = computed(() => {
  return (
    snapshotForm() !== formSnapshot.value ||
    passwordTouched.value
  )
})

async function openDialog() {
  showDialog.value = true
  loadingDetail.value = true
  try {
    const res = await systemConfigApi.getMail()
    fullConfig.value = res.data.data
    Object.assign(form, {
      smtpServer: fullConfig.value.smtpServer || '',
      smtpPort: fullConfig.value.smtpPort || '465',
      fromEmail: fullConfig.value.fromEmail || '',
      password: '',
      toList: fullConfig.value.toList || '',
      sendSqlBackup: fullConfig.value.sendSqlBackup,
      sendExcel: fullConfig.value.sendExcel,
    })
    passwordTouched.value = false
    formSnapshot.value = snapshotForm()
  } catch (err) {
    if (!isHandledError(err)) ElMessage.error('加载邮件配置失败')
    showDialog.value = false
  } finally {
    loadingDetail.value = false
  }
}

function onPasswordInput() {
  passwordTouched.value = true
}

async function clearPassword() {
  try {
    await ElMessageBox.confirm(
      '清除后下次发送邮件将失败，需要重新设置授权码。继续吗？',
      '清除已设密码',
      { type: 'warning' },
    )
  } catch {
    return
  }
  try {
    await systemConfigApi.updateMail({ password: '' })
    if (fullConfig.value) fullConfig.value.isPasswordSet = false
    ElMessage.success('已清除密码')
    emit('updated')
  } catch (err) {
    if (!isHandledError(err)) ElMessage.error('清除失败')
  }
}

async function save() {
  // 收件人格式清洗
  const cleanedToList = form.toList
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
    .join(',')

  const payload: MailConfigUpdate = {
    smtpServer: form.smtpServer,
    smtpPort: form.smtpPort,
    fromEmail: form.fromEmail,
    toList: cleanedToList,
    sendSqlBackup: form.sendSqlBackup,
    sendExcel: form.sendExcel,
  }
  if (passwordTouched.value && form.password) {
    payload.password = form.password
  }

  saving.value = true
  try {
    await systemConfigApi.updateMail(payload)
    ElMessage.success('已保存')
    showDialog.value = false
    emit('updated')
  } catch (err) {
    if (!isHandledError(err)) ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function testMail() {
  testing.value = true
  try {
    const res = await systemConfigApi.testMail()
    const result = res.data.data
    if (result.success) {
      ElMessage.success('测试邮件已发送')
    } else {
      ElMessageBox.alert(result.message || '发送失败', '邮件测试失败', {
        confirmButtonText: '我知道了',
        type: 'error',
      })
    }
  } catch (err) {
    if (!isHandledError(err)) ElMessage.error('测试发送失败')
  } finally {
    testing.value = false
  }
}
</script>

<template>
  <div class="sys-section">
    <div class="sys-section-header">
      <Mail :size="18" :stroke-width="1.75" />
      <span>邮件设置</span>
      <el-button
        type="primary"
        size="small"
        text
        class="sys-section-edit"
        @click="openDialog"
      >
        <el-icon><EditPen /></el-icon>
        <span>编辑</span>
      </el-button>
    </div>
    <div class="sys-section-body">
      <!-- 状态横幅 -->
      <div class="mail-status" :class="{ 'mail-status--ok': data.isConfigured }">
        <el-icon :size="16">
          <CircleCheckFilled v-if="data.isConfigured" />
          <CircleCloseFilled v-else />
        </el-icon>
        <span>{{ data.isConfigured ? '邮件服务已配置' : '邮件服务未配置' }}</span>
      </div>

      <!-- 已配置：展示具体字段 -->
      <div v-if="data.isConfigured" class="mail-info-list">
        <div class="mail-info-item">
          <span class="mail-info-label">SMTP 服务器</span>
          <span class="mail-info-value">{{ data.smtpServer || '-' }}</span>
        </div>
        <div class="mail-info-item">
          <span class="mail-info-label">发件人</span>
          <span class="mail-info-value">{{ data.fromEmail || '-' }}</span>
        </div>
        <div class="mail-info-item">
          <span class="mail-info-label">收件人</span>
          <span class="mail-info-value">{{ data.toListCount }} 位</span>
        </div>
      </div>

      <!-- 邮件触发开关展示 -->
      <div class="mail-toggle-list">
        <div class="mail-toggle-item">
          <span class="mail-toggle-label">SQL 备份邮件</span>
          <el-tag
            :type="data.sendSqlBackup ? 'success' : 'info'"
            size="small"
            effect="plain"
            round
          >
            {{ data.sendSqlBackup ? '开启' : '关闭' }}
          </el-tag>
        </div>
        <div class="mail-toggle-item">
          <span class="mail-toggle-label">Excel 邮件</span>
          <el-tag
            :type="data.sendExcel ? 'success' : 'info'"
            size="small"
            effect="plain"
            round
          >
            {{ data.sendExcel ? '开启' : '关闭' }}
          </el-tag>
        </div>
      </div>
    </div>

    <el-dialog
      v-model="showDialog"
      title="邮件配置"
      width="540px"
      class="sys-dialog mail-dialog"
      append-to-body
    >
      <div v-loading="loadingDetail" class="sf-form">
        <!-- 组 1：服务器 -->
        <div class="sf-card">
          <div class="sf-card-title">SMTP 服务器</div>
          <div class="sf-card-body">
            <div class="sf-row">
              <span class="sf-label">服务器</span>
              <el-input
                v-model="form.smtpServer"
                placeholder="smtp.qq.com"
                class="sf-input"
              />
            </div>
            <div class="sf-row">
              <span class="sf-label">
                端口
                <el-tooltip
                  content="465 = SMTPS（推荐）  /  587 = STARTTLS  /  25 = 明文"
                  placement="top"
                >
                  <el-icon class="sf-info"><InfoFilled /></el-icon>
                </el-tooltip>
              </span>
              <el-input
                v-model="form.smtpPort"
                placeholder="465"
                class="sf-input sf-input--narrow"
              />
            </div>
          </div>
        </div>

        <!-- 组 2：账户认证 -->
        <div class="sf-card">
          <div class="sf-card-title">账户认证</div>
          <div class="sf-card-body">
            <div class="sf-row">
              <span class="sf-label">发件人</span>
              <el-input
                v-model="form.fromEmail"
                placeholder="xxx@qq.com"
                class="sf-input"
              />
            </div>
            <div class="sf-row">
              <span class="sf-label">
                授权码
                <el-popover
                  trigger="hover"
                  placement="top-start"
                  :width="320"
                  popper-class="sf-info-popover"
                >
                  <template #reference>
                    <el-icon class="sf-info"><InfoFilled /></el-icon>
                  </template>
                  <div class="ip-content">
                    <div class="ip-title">什么是授权码？</div>
                    <div class="ip-desc">
                      授权码是邮箱服务商发放的、专门给第三方客户端使用的"代密码"。
                    </div>
                    <ul class="ip-list">
                      <li>
                        <strong>QQ / 163 / 126 / 新浪</strong> 等：必须使用授权码，
                        在邮箱后台「设置 → 账户」开启 SMTP/IMAP 服务后获取
                      </li>
                      <li>
                        <strong>Gmail / Outlook</strong> 等：开启「应用专用密码」后使用
                      </li>
                      <li>
                        <strong>企业邮 / 自建 SMTP</strong>：通常直接使用登录密码即可
                      </li>
                    </ul>
                    <div class="ip-tip">
                      💡 在邮箱网页端搜索「授权码」或「SMTP」可快速找到入口
                    </div>
                  </div>
                </el-popover>
                <el-tag
                  v-if="!fullConfig?.isPasswordSet"
                  type="info"
                  size="small"
                  effect="plain"
                  class="sf-tag"
                >
                  未设置
                </el-tag>
              </span>
              <!-- 已设置：不显示输入框，给一个清除按钮替换。
                   清除后 isPasswordSet 变 false，UI 自动切回输入框可重新设置 -->
              <el-button
                v-if="fullConfig?.isPasswordSet"
                type="danger"
                plain
                class="sf-clear-btn"
                @click="clearPassword"
              >
                <el-icon><Delete /></el-icon>
                <span>清除已设授权码</span>
              </el-button>
              <el-input
                v-else
                v-model="form.password"
                type="password"
                show-password
                placeholder="请输入授权码"
                class="sf-input"
                @input="onPasswordInput"
              />
            </div>
          </div>
        </div>

        <!-- 组 3：收件人 -->
        <div class="sf-card">
          <div class="sf-card-title">
            <span>收件人</span>
            <span class="sf-card-meta">{{ recipientCount }} 位</span>
          </div>
          <div class="sf-card-body">
            <el-input
              v-model="form.toList"
              type="textarea"
              :rows="2"
              placeholder="多个邮箱用英文逗号分隔，例：a@x.com,b@y.com"
              class="sf-input"
            />
          </div>
        </div>

        <!-- 组 4：邮件触发开关 -->
        <div class="sf-card">
          <div class="sf-card-title">邮件触发</div>
          <div class="sf-card-body sf-card-body--list">
            <div class="sf-toggle-row">
              <div class="sf-toggle-label">
                <span>SQL 备份邮件</span>
                <span class="sf-toggle-hint">备份完成后将文件发到收件人</span>
              </div>
              <el-switch v-model="form.sendSqlBackup" />
            </div>
            <div class="sf-toggle-row">
              <div class="sf-toggle-label">
                <span>Excel 邮件</span>
                <span class="sf-toggle-hint">月度 / 筛选 Excel 生成后发送</span>
              </div>
              <el-switch v-model="form.sendExcel" />
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="sf-footer">
          <el-tooltip
            v-if="dirty"
            content="请先保存当前修改后再测试"
            placement="top"
          >
            <span>
              <el-button :disabled="true">
                <el-icon><Promotion /></el-icon>
                <span>测试发邮件</span>
              </el-button>
            </span>
          </el-tooltip>
          <el-button v-else :loading="testing" @click="testMail">
            <el-icon v-if="!testing"><Promotion /></el-icon>
            <span>{{ testing ? '发送中...' : '测试发邮件' }}</span>
          </el-button>
          <div class="sf-footer-spacer" />
          <el-button @click="showDialog = false">取消</el-button>
          <el-button type="primary" :loading="saving" @click="save">保存</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
/* === 邮件设置 section 摘要展示（结构化，非字符串拼接） === */

.mail-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: rgba(0, 0, 0, 0.03);
  border-radius: 8px;
  font-size: 13px;
  color: var(--color-text-tertiary);
  margin-bottom: 10px;
}

.mail-status .el-icon {
  color: var(--color-text-tertiary);
}

.mail-status--ok {
  background: rgba(82, 196, 26, 0.08);
  color: var(--color-income);
}

.mail-status--ok .el-icon {
  color: var(--color-income);
}

.mail-info-list {
  display: flex;
  flex-direction: column;
  gap: 1px;
  background: var(--color-border-light);
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 10px;
}

.mail-info-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  background: var(--color-bg-card);
  font-size: 13px;
}

.mail-info-label {
  color: var(--color-text-secondary);
}

.mail-info-value {
  color: var(--color-text-primary);
  font-weight: 500;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

.mail-toggle-list {
  display: flex;
  flex-direction: column;
  gap: 1px;
  background: var(--color-border-light);
  border-radius: 8px;
  overflow: hidden;
}

.mail-toggle-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  background: var(--color-bg-card);
  font-size: 13px;
}

.mail-toggle-label {
  color: var(--color-text-secondary);
}

html.dark .mail-status {
  background: rgba(255, 255, 255, 0.04);
}

html.dark .mail-status--ok {
  background: rgba(105, 219, 124, 0.12);
  color: #69db7c;
}

html.dark .mail-status--ok .el-icon {
  color: #69db7c;
}

html.dark .mail-info-list,
html.dark .mail-toggle-list {
  background: rgba(255, 255, 255, 0.06);
}

html.dark .mail-info-item,
html.dark .mail-toggle-item {
  background: rgba(255, 255, 255, 0.04);
}
</style>
