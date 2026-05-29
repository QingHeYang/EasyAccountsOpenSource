<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showDialog, showLoadingToast, closeToast, showToast } from 'vant'
import MD5 from 'crypto-js/md5'
import { authApi } from '@shared/api/auth'
import { ApiCode } from '@shared/types'
import { useThemeStore } from '@shared/stores/theme'
import logoUrl from '@shared/assets/logo.png'

const route = useRoute()
const router = useRouter()
const themeStore = useThemeStore()

// 单用户系统：mode 由 API 拦截器决定
// mode=0 未注册 → 注册页
// mode=1 未登录 → 登录页
const isLogin = computed(() => route.query.mode !== '0')
const title = computed(() => isLogin.value ? '欢迎回来' : '创建账户')
const subtitle = computed(() => isLogin.value ? '请登录您的账户' : '首次使用，请设置账户')
const buttonText = computed(() => isLogin.value ? '登录' : '注册')

const username = ref('')
const password = ref('')
const loading = ref(false)

// password autocomplete：登录用 current-password，注册用 new-password
const passwordAutocomplete = computed(() => isLogin.value ? 'current-password' : 'new-password')

// 表单验证
function validate(): string | null {
  const u = username.value.trim()
  const p = password.value.trim()

  if (u.length < 3) return '用户名长度至少3位'
  if (u.length > 10) return '用户名长度最多10位'
  if (u.includes(' ')) return '用户名不能包含空格'
  if (p.length < 6) return '密码长度至少6位'
  if (p.length > 15) return '密码长度最多15位'
  if (p.includes(' ')) return '密码不能包含空格'

  return null
}

// 提交
async function onSubmit() {
  const error = validate()
  if (error) {
    showDialog({ message: error })
    return
  }

  loading.value = true
  showLoadingToast({ message: '请稍候...', forbidClick: true })

  try {
    const hashedPassword = MD5(password.value.trim()).toString()
    const params = {
      username: username.value.trim(),
      password: hashedPassword,
    }

    const res = isLogin.value
      ? await authApi.login(params)
      : await authApi.register(params)

    if (res.data.code !== 0) {
      showDialog({
        title: isLogin.value ? '登录失败' : '注册失败',
        message: res.data.msg,
      })
      return
    }

    // 保存 token
    const token = res.data.data.token
    localStorage.setItem('token', token)

    // 跳转（使用 replace，不让登录页留在历史记录中）
    // 净化 redirect：避免 redirect 指向 /auth（会话失效时可能被污染成
    // /auth?redirect=... 嵌套），否则登录成功后又跳回登录页 → 看似登录失败
    const rawRedirect = (route.query.redirect as string) || ''
    const redirect = rawRedirect && !rawRedirect.startsWith('/auth') ? rawRedirect : '/board'
    router.replace(redirect)
  } catch (err: any) {
    // 418：登录时用户不存在 → 引导切换到注册模式
    if (err?.code === ApiCode.NOT_REGISTERED && isLogin.value) {
      closeToast()
      showToast(err.message || '用户尚未注册，已切换到注册模式')
      router.replace({
        path: '/auth',
        query: { ...route.query, mode: '0' },
      })
      password.value = ''
      return
    }
    showDialog({
      title: '请求失败',
      message: err.message || '网络错误',
    })
  } finally {
    loading.value = false
    closeToast()
  }
}

// 忘记密码
function onForgotPassword() {
  showDialog({
    title: '忘记密码',
    message: '0. 重置密码不会丢失记账数据\n1. 请登录服务器，找到部署的后台文件夹\n2. 删除文件 ./Server/auth/secret.key\n3. 无需重启服务器，刷新页面重新注册即可\n4. 请妥善保管好您的密码',
  })
}
</script>

<template>
  <van-config-provider :theme="themeStore.effectiveTheme">
    <div class="auth-page">
      <!-- 背景装饰 -->
      <div class="bg-decoration">
        <!-- 红色银行卡（右上角露出） -->
        <div class="card-shape card-red"></div>
        <!-- 绿色银行卡（左下角露出） -->
        <div class="card-shape card-green"></div>
        <!-- 蓝色三条线 -->
        <div class="blue-lines">
          <div class="line line-1"></div>
          <div class="line line-2"></div>
          <div class="line line-3"></div>
        </div>
      </div>

      <!-- 头部 -->
      <div class="header">
        <div class="logo-row">
          <img :src="logoUrl" alt="Logo" class="logo-img" />
          <span class="app-name">EasyAccounts</span>
        </div>
        <p class="slogan">Where flow goes, life shows</p>
        <p class="slogan-cn">流水知去处，岁月自成诗</p>
      </div>

      <!-- 登录卡片 -->
      <div class="auth-card">
        <h2 class="card-title">{{ title }}</h2>
        <p class="card-subtitle">{{ subtitle }}</p>

        <van-form @submit="onSubmit">
          <van-cell-group inset class="form-group">
            <van-field
              v-model="username"
              name="username"
              autocomplete="username"
              label="用户名"
              placeholder="请输入用户名"
              :rules="[{ required: true, message: '请填写用户名' }]"
              clearable
            />
            <van-field
              v-model="password"
              name="password"
              :autocomplete="passwordAutocomplete"
              label="密码"
              type="password"
              placeholder="请输入密码"
              :rules="[{ required: true, message: '请填写密码' }]"
            />
          </van-cell-group>

          <div class="forgot-row" v-if="isLogin">
            <a class="forgot-link" @click="onForgotPassword">忘记密码？</a>
          </div>

          <div class="submit-row">
            <van-button
              type="primary"
              block
              round
              native-type="submit"
              :loading="loading"
              class="submit-btn"
            >
              {{ buttonText }}
            </van-button>
          </div>
        </van-form>

      </div>
    </div>
  </van-config-provider>
</template>

<style scoped>
.auth-page {
  height: 100vh;
  padding: 24px;
  background: var(--color-bg-page);
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* 背景装饰圆 */
.bg-decoration {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  overflow: hidden;
}

/* 银行卡样式 */
.card-shape {
  position: absolute;
  width: 360px;
  height: 220px;
  border-radius: 20px;
  opacity: 0.15;
}

.card-red {
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a5a 100%);
  top: -100px;
  right: -160px;
  transform: rotate(-15deg);
}

.card-green {
  background: linear-gradient(135deg, #51cf66 0%, #40c057 100%);
  bottom: 80px;
  left: -180px;
  transform: rotate(20deg);
}

/* 蓝色三条线（整体大小接近银行卡） */
.blue-lines {
  position: absolute;
  width: 360px;
  height: 220px;
  bottom: 280px;
  right: -200px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 24px;
  transform: rotate(-20deg);
}

.line {
  height: 28px;
  border-radius: 14px;
  background: linear-gradient(90deg, #339af0 0%, #228be6 100%);
  opacity: 0.15;
}

.line-1 {
  width: 85%;
  margin-left: 15%;
}

.line-2 {
  width: 70%;
  margin-left: 5%;
}

.line-3 {
  width: 80%;
  margin-left: 20%;
}

/* 头部 */
.header {
  position: relative;
  z-index: 1;
  margin-top: 60px;
  margin-bottom: 40px;
  padding-left: 8px;
}

.logo-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-img {
  width: 56px;
  height: 56px;
}

.app-name {
  font-size: 28px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.slogan {
  margin-top: 8px;
  font-size: 16px;
  color: var(--color-text-tertiary);
}

.slogan-cn {
  margin-top: 4px;
  font-size: 14px;
  color: var(--color-text-secondary);
}

/* 登录卡片 */
.auth-card {
  position: relative;
  z-index: 1;
  border-radius: 24px;
  padding: 32px 20px;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.card-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 4px 8px;
}

.card-subtitle {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin: 0 0 24px 8px;
}

.form-group {
  margin: 0;
}

.form-group :deep(.van-cell-group--inset) {
  margin: 0;
}

.form-group :deep(.van-cell) {
  background: transparent;
}

.forgot-row {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
  padding-right: 8px;
}

.forgot-link {
  font-size: 14px;
  color: var(--color-transfer);
}

.submit-row {
  margin-top: 24px;
}

.submit-btn {
  height: 48px;
  font-size: 16px;
  font-weight: 500;
}

</style>

<!-- 暗色模式样式 -->
<style>
html.dark .auth-card {
  background: rgba(40, 40, 40, 0.72);
  border-color: rgba(255, 255, 255, 0.08);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

html.dark .circle {
  opacity: 0.1;
}
</style>
