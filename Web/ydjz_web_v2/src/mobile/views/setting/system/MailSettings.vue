<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { showToast, showConfirmDialog, showDialog, showLoadingToast, closeToast } from 'vant'
import { useSmartBack } from '@shared/composables/useSmartBack'
import {
  systemConfigApi,
  type MailConfig,
  type MailConfigUpdate,
} from '@shared/api/systemConfig'
import { isHandledError } from '@shared/api/request'

import './page-styles.css'

const { smartBack } = useSmartBack()

const fullConfig = ref<MailConfig | null>(null)
const saving = ref(false)
const testing = ref(false)

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
  return snapshotForm() !== formSnapshot.value || passwordTouched.value
})

async function loadData() {
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
    if (!isHandledError(err)) showToast('加载失败')
  }
}

function onPasswordInput() {
  passwordTouched.value = true
}

async function clearPassword() {
  try {
    await showConfirmDialog({
      title: '清除已设授权码',
      message: '清除后下次发送邮件将失败，需要重新设置授权码。继续吗？',
      confirmButtonColor: '#F5222D',
    })
  } catch {
    return
  }
  try {
    await systemConfigApi.updateMail({ password: '' })
    if (fullConfig.value) fullConfig.value.isPasswordSet = false
    showToast('已清除')
  } catch (err) {
    if (!isHandledError(err)) showToast('清除失败')
  }
}

async function onSave() {
  if (!dirty.value || !fullConfig.value) return
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
  showLoadingToast({ message: '保存中...', forbidClick: true, duration: 0 })
  try {
    await systemConfigApi.updateMail(payload)
    closeToast()
    showToast({ message: '已保存', type: 'success' })
    smartBack('/setting/system')
  } catch (err) {
    closeToast()
    if (!isHandledError(err)) showToast('保存失败')
  } finally {
    saving.value = false
  }
}

async function testMail() {
  if (dirty.value) {
    showToast('请先保存修改后再测试')
    return
  }
  testing.value = true
  showLoadingToast({ message: '发送中...', forbidClick: true, duration: 0 })
  try {
    const res = await systemConfigApi.testMail()
    closeToast()
    const result = res.data.data
    if (result.success) {
      showToast({ message: '测试邮件已发送', type: 'success' })
    } else {
      showDialog({
        title: '邮件测试失败',
        message: result.message || '发送失败',
        messageAlign: 'left',
      })
    }
  } catch (err) {
    closeToast()
    if (!isHandledError(err)) showToast('测试发送失败')
  } finally {
    testing.value = false
  }
}

function showInfoDialog() {
  showDialog({
    title: '什么是授权码？',
    message:
      '授权码是邮箱服务商发放的、专门给第三方客户端使用的"代密码"。\n\n' +
      'QQ / 163 / 126 / 新浪 等：必须使用授权码，在邮箱后台「设置 → 账户」开启 SMTP/IMAP 服务后获取。\n\n' +
      'Gmail / Outlook 等：开启「应用专用密码」后使用。\n\n' +
      '企业邮 / 自建 SMTP：通常直接使用登录密码即可。',
    confirmButtonText: '我知道了',
    messageAlign: 'left',
  })
}

function showPortDialog() {
  showDialog({
    title: '常用端口',
    message: '465 = SMTPS（推荐）\n587 = STARTTLS\n25 = 明文',
    confirmButtonText: '我知道了',
    messageAlign: 'left',
  })
}

function onBack() {
  smartBack('/setting/system')
}

onMounted(() => {
  window.scrollTo(0, 0)
  loadData()
})
</script>

<template>
  <div class="sys-mob-page">
    <div class="sys-mob-header">
      <div class="sys-mob-header-left" @click="onBack">
        <van-icon name="arrow-left" size="20" />
      </div>
      <div class="sys-mob-header-title">邮件设置</div>
      <div class="sys-mob-header-right is-info" @click="showInfoDialog">
        <van-icon name="question-o" size="20" />
      </div>
    </div>

    <div class="sys-mob-body sys-mob-body-with-footer">
      <!-- SMTP 服务器 -->
      <van-cell-group v-if="fullConfig" inset title="SMTP 服务器">
        <van-field
          v-model="form.smtpServer"
          label="服务器"
          placeholder="smtp.qq.com"
          input-align="right"
        />
        <van-field
          v-model="form.smtpPort"
          label="端口"
          placeholder="465"
          input-align="right"
        >
          <template #right-icon>
            <van-icon
              name="info-o"
              class="port-info"
              @click="showPortDialog"
            />
          </template>
        </van-field>
      </van-cell-group>

      <!-- 账户认证 -->
      <van-cell-group v-if="fullConfig" inset title="账户认证">
        <van-field
          v-model="form.fromEmail"
          label="发件人"
          placeholder="xxx@qq.com"
          input-align="right"
        />

        <!-- 已设：在同一个 cell 里给「已设置」徽章 + 「清除」红字链接 -->
        <van-cell v-if="fullConfig.isPasswordSet" title="授权码" center>
          <template #value>
            <div class="password-row">
              <van-tag type="success" plain>已设置</van-tag>
              <span class="clear-link" @click="clearPassword">清除</span>
            </div>
          </template>
        </van-cell>
        <van-field
          v-else
          v-model="form.password"
          label="授权码"
          type="password"
          placeholder="请输入授权码"
          input-align="right"
          @input="onPasswordInput"
        />
      </van-cell-group>

      <!-- 收件人（独立栏目） -->
      <van-cell-group v-if="fullConfig" inset title="收件人">
        <van-field
          v-model="form.toList"
          type="textarea"
          rows="2"
          autosize
          placeholder="多个邮箱用英文逗号分隔，例：a@x.com,b@y.com"
        />
        <div class="hint-line">{{ recipientCount }} 位收件人</div>
      </van-cell-group>

      <!-- 邮件触发 -->
      <van-cell-group v-if="fullConfig" inset title="邮件触发">
        <van-cell
          title="SQL 备份邮件"
          label="备份完成后将文件发到收件人"
          center
        >
          <template #value>
            <van-switch v-model="form.sendSqlBackup" />
          </template>
        </van-cell>
        <van-cell
          title="Excel 邮件"
          label="月度 / 筛选 Excel 生成后发送"
          center
        >
          <template #value>
            <van-switch v-model="form.sendExcel" />
          </template>
        </van-cell>
      </van-cell-group>

      <div v-if="fullConfig && dirty" class="hint-line">
        有未保存的修改，请先保存才能测试发邮件
      </div>
    </div>

    <!-- 底部固定栏：测试发邮件 + 保存 -->
    <div class="sys-mob-footer">
      <van-button
        plain
        round
        :loading="testing"
        :disabled="dirty"
        @click="testMail"
      >
        测试发邮件
      </van-button>
      <van-button
        type="primary"
        round
        :disabled="!dirty"
        :loading="saving"
        @click="onSave"
      >
        保存
      </van-button>
    </div>
  </div>
</template>

<style scoped>
.port-info {
  color: var(--color-text-tertiary);
  cursor: pointer;
  font-size: 16px;
}

.hint-line {
  padding: 4px 22px 12px;
  font-size: 11px;
  color: var(--color-text-tertiary);
  text-align: center;
}

/* 授权码 cell：「已设置」+「清除」放同行 */
.password-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.clear-link {
  color: var(--color-expense);
  font-size: 13px;
  font-weight: 500;
  padding: 4px 0;
}

.clear-link:active {
  opacity: 0.7;
}
</style>
