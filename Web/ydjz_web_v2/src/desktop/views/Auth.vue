<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, ElLoading } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import MD5 from 'crypto-js/md5'
import { authApi } from '@shared/api/auth'
import { ApiCode } from '@shared/types'
import logoUrl from '@shared/assets/logo.png'

const route = useRoute()
const router = useRouter()

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
    ElMessage.warning(error)
    return
  }

  loading.value = true
  const loadingInstance = ElLoading.service({
    fullscreen: true,
    text: '请稍候...',
    background: 'rgba(0, 0, 0, 0.5)'
  })

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
      ElMessageBox.alert(res.data.msg, isLogin.value ? '登录失败' : '注册失败', {
        type: 'error'
      })
      return
    }

    // 保存 token
    const token = res.data.data.token
    localStorage.setItem('token', token)

    ElMessage.success(isLogin.value ? '登录成功' : '注册成功')

    // 跳转（使用 replace，不让登录页留在历史记录中）
    const redirect = (route.query.redirect as string) || '/'
    router.replace(redirect)
  } catch (err: any) {
    // 418：登录时用户不存在 → 引导切换到注册模式
    if (err?.code === ApiCode.NOT_REGISTERED && isLogin.value) {
      ElMessage.warning(err.message || '用户尚未注册，已切换到注册模式')
      // 切到注册模式（保留 redirect query 等其它参数）
      router.replace({
        path: '/auth',
        query: { ...route.query, mode: '0' },
      })
      // 清空密码，引导用户重新设置（用户名保留）
      password.value = ''
      return
    }
    ElMessageBox.alert(err.message || '网络错误', '请求失败', {
      type: 'error'
    })
  } finally {
    loading.value = false
    loadingInstance.close()
  }
}

// 忘记密码
function onForgotPassword() {
  ElMessageBox.alert(
    '0. 重置密码不会丢失记账数据\n1. 请登录服务器，找到部署的后台文件夹\n2. 删除文件 ./Server/auth/secret.key\n3. 无需重启服务器，刷新页面重新注册即可\n4. 请妥善保管好您的密码',
    '忘记密码',
    { type: 'info' }
  )
}

// 回车提交
function handleKeyEnter(e: KeyboardEvent) {
  if (e.key === 'Enter') {
    onSubmit()
  }
}
</script>

<template>
  <div class="auth-page">
    <!-- 背景装饰 -->
    <div class="bg-decoration">
      <!-- 红色银行卡 -->
      <div class="card-shape card-red"></div>
      <!-- 绿色银行卡 -->
      <div class="card-shape card-green"></div>
      <!-- 蓝色三条线 -->
      <div class="blue-lines">
        <div class="line line-1"></div>
        <div class="line line-2"></div>
        <div class="line line-3"></div>
      </div>
    </div>

    <!-- 内容区域 -->
    <div class="auth-content">
      <!-- 左侧品牌区 -->
      <div class="brand-section">
        <div class="brand-inner">
          <div class="logo-row">
            <img :src="logoUrl" alt="Logo" class="logo-img" />
            <span class="app-name">EasyAccounts</span>
          </div>
          <p class="slogan">Where flow goes, life shows</p>
          <p class="slogan-cn">流水知去处，岁月自成诗</p>
        </div>
      </div>

      <!-- 右侧登录卡片 -->
      <div class="auth-card">
        <h2 class="card-title">{{ title }}</h2>
        <p class="card-subtitle">{{ subtitle }}</p>

        <el-form class="auth-form" @keydown="handleKeyEnter">
          <el-form-item>
            <el-input
              v-model="username"
              placeholder="请输入用户名"
              size="large"
              clearable
              :prefix-icon="User"
            />
          </el-form-item>

          <el-form-item>
            <el-input
              v-model="password"
              type="password"
              placeholder="请输入密码"
              size="large"
              show-password
              :prefix-icon="Lock"
            />
          </el-form-item>

          <div class="forgot-row" v-if="isLogin">
            <el-link type="primary" :underline="false" @click="onForgotPassword">
              忘记密码？
            </el-link>
          </div>

          <el-form-item class="submit-item">
            <el-button
              type="primary"
              size="large"
              :loading="loading"
              class="submit-btn"
              @click="onSubmit"
            >
              {{ buttonText }}
            </el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>

    <!-- 底部 Powered by -->
    <div class="powered-by">
      Powered by <a href="https://github.com/QingHeYang/EasyAccounts" target="_blank">EasyAccounts</a>
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  min-height: 100vh;
  background: var(--color-bg-page);
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

/* 背景装饰 */
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
  width: 500px;
  height: 300px;
  border-radius: 24px;
  opacity: 0.12;
}

.card-red {
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a5a 100%);
  top: -120px;
  right: -100px;
  transform: rotate(-15deg);
}

.card-green {
  background: linear-gradient(135deg, #51cf66 0%, #40c057 100%);
  bottom: -80px;
  left: -120px;
  transform: rotate(20deg);
}

/* 蓝色三条线 */
.blue-lines {
  position: absolute;
  width: 500px;
  height: 300px;
  top: 50%;
  left: -200px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 32px;
  transform: translateY(-50%) rotate(-20deg);
}

.line {
  height: 36px;
  border-radius: 18px;
  background: linear-gradient(90deg, #339af0 0%, #228be6 100%);
  opacity: 0.12;
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

/* 内容区域 */
.auth-content {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 80px;
  max-width: 1000px;
  width: 100%;
  padding: 40px;
}

/* 左侧品牌区 */
.brand-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.brand-inner {
  max-width: 400px;
}

.logo-row {
  display: flex;
  align-items: center;
  gap: 16px;
}

.logo-img {
  width: 72px;
  height: 72px;
}

.app-name {
  font-size: 36px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.slogan {
  margin-top: 16px;
  font-size: 20px;
  color: var(--color-text-tertiary);
  font-style: italic;
}

.slogan-cn {
  margin-top: 8px;
  font-size: 16px;
  color: var(--color-text-secondary);
}

/* 右侧登录卡片 */
.auth-card {
  width: 400px;
  flex-shrink: 0;
  border-radius: 24px;
  padding: 48px 40px;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.card-title {
  font-size: 28px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 8px 0;
}

.card-subtitle {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin: 0 0 32px 0;
}

.auth-form {
  width: 100%;
}

.auth-form :deep(.el-form-item) {
  margin-bottom: 20px;
}

.auth-form :deep(.el-input__wrapper) {
  padding: 8px 16px;
  border-radius: 12px;
}

.forgot-row {
  display: flex;
  justify-content: flex-end;
  margin-top: -8px;
  margin-bottom: 24px;
}

.submit-item {
  margin-bottom: 0;
  margin-top: 8px;
}

.submit-btn {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: 500;
  border-radius: 12px;
}

/* Powered by */
.powered-by {
  position: absolute;
  bottom: 24px;
  font-size: 13px;
  color: var(--color-text-tertiary);
}

.powered-by a {
  color: var(--color-transfer);
  text-decoration: none;
  font-weight: 500;
}

.powered-by a:hover {
  text-decoration: underline;
}

/* 响应式 */
@media (max-width: 900px) {
  .auth-content {
    flex-direction: column;
    gap: 40px;
  }

  .brand-section {
    text-align: center;
  }

  .brand-inner {
    max-width: none;
  }

  .logo-row {
    justify-content: center;
  }

  .auth-card {
    width: 100%;
    max-width: 400px;
  }
}
</style>

<!-- 暗色模式样式 -->
<style>
html.dark .auth-card {
  background: rgba(40, 40, 40, 0.72);
  border-color: rgba(255, 255, 255, 0.08);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

html.dark .card-shape,
html.dark .line {
  opacity: 0.08;
}
</style>
