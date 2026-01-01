<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useThemeStore } from '@shared/stores/theme'
import { homeApi, type VersionInfo } from '@shared/api/home'
import { aiApi, type AiHealthResponse } from '@shared/api/ai'
import { showConfirmDialog } from 'vant'
import logoUrl from '@shared/assets/logo.png'

const router = useRouter()
const themeStore = useThemeStore()

// AI 服务状态
const aiHealth = ref<AiHealthResponse | null>(null)
const aiServiceAvailable = computed(() => aiHealth.value !== null)
const aiConfigured = computed(() => aiHealth.value?.data?.llm?.configured === true)

// 主题相关
const themeText = computed(() => {
  const map = { light: '浅色', dark: '深色', system: '跟随系统' }
  return map[themeStore.mode]
})

function onThemeChange() {
  const modes = ['light', 'dark', 'system'] as const
  const idx = modes.indexOf(themeStore.mode)
  const next = modes[(idx + 1) % modes.length]
  themeStore.set(next)
}

// 关于弹窗
const showAbout = ref(false)
const showVersionDetail = ref(false)
const versions = ref<VersionInfo>({
  release: '',
  fontBranch: '',
  backendBranch: '',
  mysqlBranch: '',
  agentBranch: '',
  webhookBranch: '',
})

async function loadVersion() {
  try {
    const res = await homeApi.getVersion()
    versions.value = res.data.data
  } catch (err) {
    console.error('获取版本信息失败', err)
  }
}

function openAbout() {
  showAbout.value = true
  if (!versions.value.release) {
    loadVersion()
  }
}

// 退出登录
function onLogout() {
  showConfirmDialog({
    title: '退出登录',
    message: '确定要退出登录吗？',
  }).then(() => {
    localStorage.removeItem('token')
    router.push('/auth?mode=1')
  }).catch(() => {})
}

// 检测 AI 服务
async function checkAiService() {
  aiHealth.value = await aiApi.checkHealth()
}

// 点击 AI 设置
function onAiClick() {
  if (!aiConfigured.value) {
    // AI 未配置时显示提示
    const missing = aiHealth.value?.data?.llm?.missing || []
    showConfirmDialog({
      title: 'AI 服务未配置',
      message: `请在 docker-compose.yml 中配置以下环境变量：\n\n${missing.join('\n')}`,
      showCancelButton: false,
      confirmButtonText: '知道了',
    }).catch(() => {})
    return
  }
  router.push('/setting/ai')
}

onMounted(() => {
  // 预加载版本信息
  loadVersion()
  // 检测 AI 服务
  checkAiService()
})
</script>

<template>
  <div class="setting-page">
    <!-- 顶部导航 -->
    <div class="page-header">
      <div class="header-title">设置</div>
    </div>

    <div class="page-body">
      <!-- 数据管理 -->
      <van-cell-group inset title="数据管理">
        <van-cell
          title="收支"
          icon="exchange"
          is-link
          to="/setting/action"
        />
        <van-cell
          title="账户"
          icon="paid"
          is-link
          to="/setting/account"
        />
        <van-cell
          title="分类"
          icon="balance-list-o"
          is-link
          to="/setting/type"
        />
        <van-cell
          title="快记模板"
          icon="cluster-o"
          is-link
          to="/setting/template"
        />
        <!-- AI+ 设置（仅在 AI 服务可用时显示） -->
        <van-cell
          v-if="aiServiceAvailable"
          title="AI+ 设置"
          icon="fire-o"
          is-link
          :class="{ 'ai-unconfigured': !aiConfigured }"
          @click="onAiClick"
        >
          <template #value>
            <van-tag v-if="!aiConfigured" type="warning">未配置</van-tag>
          </template>
        </van-cell>
      </van-cell-group>

      <!-- 外观设置 -->
      <van-cell-group inset title="外观">
        <van-cell
          title="主题模式"
          icon="brush-o"
          :value="themeText"
          is-link
          @click="onThemeChange"
        />
      </van-cell-group>

      <!-- 其他 -->
      <van-cell-group inset title="其他">
        <van-cell
          title="关于"
          icon="info-o"
          is-link
          @click="openAbout"
        />
        <van-cell
          title="退出登录"
          icon="revoke"
          is-link
          @click="onLogout"
        />
      </van-cell-group>
    </div>

    <!-- 关于弹窗 -->
    <van-popup
      v-model:show="showAbout"
      round
      closeable
      close-icon="cross"
      teleport="body"
      :style="{ width: '85%', maxWidth: '320px' }"
    >
      <div class="about-dialog">
        <!-- 顶部装饰背景 -->
        <div class="about-bg"></div>

        <!-- Logo -->
        <div class="about-logo-wrapper">
          <img :src="logoUrl" alt="Logo" class="about-logo" />
        </div>

        <!-- 应用名称 -->
        <div class="about-name">EasyAccounts</div>

        <!-- 副标题 -->
        <div class="about-slogan">认真生活, 好好记账</div>

        <!-- 版本标签（可点击展开） -->
        <div class="about-version-tag" @click="showVersionDetail = !showVersionDetail">
          <span class="version-label">Version</span>
          <span class="version-value">{{ versions.release || '...' }}</span>
          <van-icon :name="showVersionDetail ? 'arrow-up' : 'arrow-down'" class="version-arrow" />
        </div>

        <!-- 版本详情 -->
        <div v-if="showVersionDetail" class="version-detail">
          <div class="version-item">
            <span class="item-label">前端</span>
            <span class="item-value">{{ versions.fontBranch || '-' }}</span>
          </div>
          <div class="version-item">
            <span class="item-label">后端</span>
            <span class="item-value">{{ versions.backendBranch || '-' }}</span>
          </div>
          <div class="version-item">
            <span class="item-label">数据库</span>
            <span class="item-value">{{ versions.mysqlBranch || '-' }}</span>
          </div>
          <div class="version-item">
            <span class="item-label">AI Agent</span>
            <span class="item-value">{{ versions.agentBranch || '-' }}</span>
          </div>
          <div class="version-item">
            <span class="item-label">WebHook</span>
            <span class="item-value">{{ versions.webhookBranch || '-' }}</span>
          </div>
        </div>

        <!-- 分隔线 -->
        <div class="about-divider"></div>

        <!-- 开发者信息 -->
        <div class="about-developer">
          <a
            href="https://github.com/QingHeYang/EasyAccounts"
            target="_blank"
            class="developer-card"
          >
            <img
              src="https://avatars.githubusercontent.com/u/19968251?u=5bc82e5f642e80a6aa51c9eb10389932db38135f&v=4&size=64"
              alt="Avatar"
              class="developer-avatar"
            />
            <div class="developer-info">
              <div class="developer-name">QingHeYang</div>
              <div class="developer-role">Developer</div>
            </div>
            <van-icon name="arrow" class="developer-arrow" />
          </a>
        </div>

        <!-- 底部 -->
        <div class="about-footer">
          Made with care
        </div>
      </div>
    </van-popup>
  </div>
</template>

<style scoped>
.setting-page {
  min-height: 100vh;
  background: transparent;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

/* 顶部导航 */
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

.header-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--color-text-primary);
}

.page-body {
  padding: 70px 0 100px;
}

/* ===== 关于弹窗 ===== */
.about-dialog {
  position: relative;
  padding: 24px;
  text-align: center;
  overflow: hidden;
  background: var(--color-bg-card);
}

/* 顶部装饰背景 */
.about-bg {
  position: absolute;
  top: -60px;
  left: 50%;
  transform: translateX(-50%);
  width: 200px;
  height: 200px;
  background: linear-gradient(135deg, var(--color-transfer) 0%, var(--color-income) 100%);
  border-radius: 50%;
  opacity: 0.15;
  filter: blur(40px);
}

/* Logo */
.about-logo-wrapper {
  position: relative;
  display: inline-flex;
  padding: 16px;
  background: var(--color-bg-page);
  border-radius: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  margin-top: 16px;
}

.about-logo {
  width: 56px;
  height: 56px;
}

/* 应用名称 */
.about-name {
  margin-top: 20px;
  font-size: 22px;
  font-weight: 700;
  color: var(--color-text-primary);
  letter-spacing: -0.5px;
}

/* 副标题 */
.about-slogan {
  margin-top: 6px;
  font-size: 14px;
  color: var(--color-text-secondary);
}

/* 版本标签 */
.about-version-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: 16px;
  padding: 6px 14px;
  background: var(--color-bg-page);
  border-radius: 20px;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s;
}

.about-version-tag:active {
  background: var(--color-border);
}

.version-label {
  color: var(--color-text-tertiary);
}

.version-value {
  color: var(--color-transfer);
  font-weight: 600;
}

.version-arrow {
  color: var(--color-text-tertiary);
  font-size: 12px;
  margin-left: 2px;
}

/* 版本详情 */
.version-detail {
  margin-top: 12px;
  padding: 12px 16px;
  background: var(--color-bg-page);
  border-radius: 12px;
  text-align: left;
}

.version-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
}

.version-item:not(:last-child) {
  border-bottom: 1px solid var(--color-border-light);
}

.version-item .item-label {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.version-item .item-value {
  font-size: 13px;
  color: var(--color-text-primary);
  font-weight: 500;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

/* 分隔线 */
.about-divider {
  margin: 24px 0;
  height: 1px;
  background: var(--color-border);
}

/* 开发者卡片 */
.about-developer {
  margin: 0 -8px;
}

.developer-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: var(--color-bg-page);
  border-radius: 12px;
  text-decoration: none;
  transition: background 0.2s;
}

.developer-card:active {
  background: var(--color-bg-active);
}

.developer-avatar {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  object-fit: cover;
}

.developer-info {
  flex: 1;
  text-align: left;
}

.developer-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.developer-role {
  margin-top: 2px;
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.developer-arrow {
  color: var(--color-text-tertiary);
  font-size: 14px;
}

/* 底部 */
.about-footer {
  margin-top: 20px;
  font-size: 12px;
  color: var(--color-text-tertiary);
}

/* AI 未配置状态 */
.ai-unconfigured {
  opacity: 0.7;
}
</style>

<!-- 非 scoped 样式用于主题切换 -->
<style>
.setting-page .page-header {
  background: rgba(245, 245, 245, 0.8);
}

html.dark .setting-page .page-header {
  background: rgba(10, 10, 10, 0.8);
}
</style>
