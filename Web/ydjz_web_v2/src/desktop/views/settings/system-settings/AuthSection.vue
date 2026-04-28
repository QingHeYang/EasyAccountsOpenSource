<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Lock, Timer, User } from '@element-plus/icons-vue'
import { systemConfigApi, type AuthOverview } from '@shared/api/systemConfig'
import { isHandledError } from '@shared/api/request'

const props = defineProps<{
  data: AuthOverview
}>()

const emit = defineEmits<{
  (e: 'updated'): void
}>()

/* ---- 本地状态：从 props 同步，用户操作时维持自身 ---- */

const localLoginEnable = ref(props.data.loginEnable)
const localSingleLogin = ref(props.data.singleLogin)
const localTokenMinutes = ref(props.data.tokenExpiredMinutes)

watch(
  () => props.data,
  (v) => {
    localLoginEnable.value = v.loginEnable
    localSingleLogin.value = v.singleLogin
    localTokenMinutes.value = v.tokenExpiredMinutes
  },
  { deep: true },
)

/* ---- 启用登录开关 ---- */

async function onLoginEnableChange(val: boolean) {
  // 关闭走 confirm（高风险）
  if (!val) {
    try {
      await ElMessageBox.confirm(
        '关闭后任何人都能访问你的账本，请确认要关闭吗？',
        '关闭登录',
        {
          confirmButtonText: '确认关闭',
          cancelButtonText: '取消',
          type: 'warning',
          confirmButtonClass: 'el-button--danger',
        },
      )
    } catch {
      // 撤回
      localLoginEnable.value = true
      return
    }
  }
  try {
    await systemConfigApi.updateAuth({ loginEnable: val })
    if (!val) localStorage.removeItem('token')
    emit('updated')
  } catch (err) {
    localLoginEnable.value = !val
    if (!isHandledError(err)) ElMessage.error('保存失败')
  }
}

/* ---- 登录模式 segmented ---- */

async function onSingleLoginChange(val: string | number | boolean) {
  const v = val as boolean
  try {
    await systemConfigApi.updateAuth({ singleLogin: v })
    emit('updated')
  } catch (err) {
    localSingleLogin.value = !v
    if (!isHandledError(err)) ElMessage.error('保存失败')
  }
}

/* ---- 会话时长 InputNumber（debounce 600ms） ---- */

let tokenDebounceTimer: ReturnType<typeof setTimeout> | null = null

function onTokenChange(val: number | undefined) {
  if (!val || val < 1) return
  localTokenMinutes.value = val
  if (tokenDebounceTimer) clearTimeout(tokenDebounceTimer)
  tokenDebounceTimer = setTimeout(async () => {
    try {
      await systemConfigApi.updateAuth({ tokenExpiredMinutes: val })
      // 成功后让父级 reload overview，props 进来后 watch 自动同步 localTokenMinutes
      emit('updated')
    } catch (err) {
      if (!isHandledError(err)) ElMessage.error('保存失败')
    }
  }, 600)
}

const sessionTimeText = computed(() => {
  const m = localTokenMinutes.value
  if (m >= 60) {
    const h = Math.floor(m / 60)
    const r = m % 60
    return r > 0 ? `（约 ${h} 小时 ${r} 分钟）` : `（约 ${h} 小时）`
  }
  return ''
})
</script>

<template>
  <div class="sys-section">
    <div class="sys-section-header">
      <el-icon :size="18"><Lock /></el-icon>
      <span>鉴权设置</span>
    </div>
    <div class="sys-section-body">
      <div class="sys-info-grid">
        <div class="sys-info-item">
          <div class="sys-info-label">
            <el-icon :size="14"><Lock /></el-icon>
            <span>启用登录</span>
          </div>
          <div class="sys-info-value">
            <el-switch
              v-model="localLoginEnable"
              @change="onLoginEnableChange"
            />
          </div>
        </div>

        <div
          class="sys-info-item"
          :class="{ 'sys-disabled': !localLoginEnable }"
        >
          <div class="sys-info-label">
            <el-icon :size="14"><User /></el-icon>
            <span>登录模式</span>
          </div>
          <div class="sys-info-value">
            <el-segmented
              v-model="localSingleLogin"
              :options="[
                { label: '单点', value: true },
                { label: '多端', value: false },
              ]"
              size="small"
              :disabled="!localLoginEnable"
              @change="onSingleLoginChange"
            />
          </div>
        </div>

        <div class="sys-info-item">
          <div class="sys-info-label">
            <el-icon :size="14"><Timer /></el-icon>
            <span>会话时长{{ sessionTimeText }}</span>
          </div>
          <div class="sys-info-value">
            <el-input-number
              v-model="localTokenMinutes"
              :min="1"
              :max="100000"
              size="small"
              controls-position="right"
              style="width: 130px"
              @change="onTokenChange"
            />
            <span class="sys-value-suffix">分钟</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
