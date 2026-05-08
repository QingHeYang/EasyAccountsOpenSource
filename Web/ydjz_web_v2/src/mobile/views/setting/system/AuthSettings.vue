<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { showToast, showConfirmDialog, showLoadingToast, closeToast } from 'vant'
import { useSmartBack } from '@shared/composables/useSmartBack'
import {
  systemConfigApi,
  type AuthConfig,
  type AuthConfigUpdate,
} from '@shared/api/systemConfig'
import { isHandledError } from '@shared/api/request'
import { Info } from 'lucide-vue-next'

import './page-styles.css'

const { smartBack } = useSmartBack()

const original = ref<AuthConfig | null>(null)
const form = reactive<AuthConfig>({
  loginEnable: true,
  singleLogin: true,
  tokenExpiredMinutes: 30,
})
const saving = ref(false)

async function loadData() {
  try {
    const res = await systemConfigApi.getAuth()
    original.value = { ...res.data.data }
    Object.assign(form, original.value)
  } catch (err) {
    if (!isHandledError(err)) showToast('加载失败')
  }
}

const dirty = computed(() => {
  if (!original.value) return false
  return (
    form.loginEnable !== original.value.loginEnable ||
    form.singleLogin !== original.value.singleLogin ||
    form.tokenExpiredMinutes !== original.value.tokenExpiredMinutes
  )
})

/* 关闭登录是高风险操作，切换 UI 前先 confirm */
async function onLoginEnableChange(val: boolean) {
  if (!val) {
    try {
      await showConfirmDialog({
        title: '关闭登录',
        message: '关闭后任何人都能访问你的账本，确认要关闭吗？',
        confirmButtonText: '确认关闭',
        confirmButtonColor: '#F5222D',
      })
    } catch {
      // 撤回 UI
      form.loginEnable = true
      return
    }
  }
  form.loginEnable = val
}

function onSingleLoginChange(val: boolean) {
  if (!form.loginEnable) return
  form.singleLogin = val
}

function onTokenChange(val: number | string) {
  const n = typeof val === 'number' ? val : parseInt(val, 10)
  if (isNaN(n) || n < 1) return
  form.tokenExpiredMinutes = n
}

async function onSave() {
  if (!dirty.value || !original.value) return
  const payload: AuthConfigUpdate = {
    loginEnable: form.loginEnable,
    singleLogin: form.singleLogin,
    tokenExpiredMinutes: form.tokenExpiredMinutes,
  }
  saving.value = true
  showLoadingToast({ message: '保存中...', forbidClick: true, duration: 0 })
  try {
    await systemConfigApi.updateAuth(payload)
    closeToast()
    // 关闭登录后清 token
    if (!form.loginEnable && original.value.loginEnable) {
      localStorage.removeItem('token')
    }
    showToast({ message: '已保存', type: 'success' })
    smartBack('/setting/system')
  } catch (err) {
    if (!isHandledError(err)) {
      closeToast()
      showToast('保存失败')
    }
  } finally {
    saving.value = false
  }
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
      <div class="sys-mob-header-title">鉴权设置</div>
      <div class="sys-mob-header-right"></div>
    </div>

    <div class="sys-mob-body sys-mob-body-with-footer">
      <van-cell-group v-if="original" inset>
        <van-cell title="启用登录" center>
          <template #value>
            <van-switch
              :model-value="form.loginEnable"
              @update:model-value="onLoginEnableChange"
            />
          </template>
        </van-cell>

        <van-cell
          title="登录模式"
          center
          :class="{ 'sys-mob-cell-disabled': !form.loginEnable }"
        >
          <template #value>
            <div class="sys-mob-segmented">
              <div
                class="seg-item"
                :class="{ active: form.singleLogin === true }"
                @click="onSingleLoginChange(true)"
              >
                单点
              </div>
              <div
                class="seg-item"
                :class="{ active: form.singleLogin === false }"
                @click="onSingleLoginChange(false)"
              >
                多端
              </div>
            </div>
          </template>
        </van-cell>

        <van-cell title="会话时长" center>
          <template #value>
            <div class="stepper-wrap">
              <van-stepper
                :model-value="form.tokenExpiredMinutes"
                :min="1"
                :max="100000"
                :step="5"
                input-width="50px"
                button-size="28px"
                @update:model-value="onTokenChange"
              />
              <span class="suffix">分钟</span>
            </div>
          </template>
        </van-cell>
      </van-cell-group>

      <div class="sys-mob-hint">
        <Info :size="14" :stroke-width="1.75" class="hint-icon" />
        <div class="hint-content">
          <div class="hint-title">关于登录模式</div>
          <div class="hint-text">
            <strong>单点</strong>：新设备登录会踢掉旧设备，更安全。<br />
            <strong>多端</strong>：多个设备共享 Token，使用更方便。
          </div>
        </div>
      </div>
    </div>

    <!-- 底部固定保存栏 -->
    <div class="sys-mob-footer">
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
.stepper-wrap {
  display: flex;
  align-items: center;
  gap: 6px;
}

.suffix {
  font-size: 12px;
  color: var(--color-text-tertiary);
}
</style>
