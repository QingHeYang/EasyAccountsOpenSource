<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useThemeStore } from '@shared/stores/theme'
import { homeApi, type VersionInfo, type UpdateInfo, type AuthConfig } from '@shared/api/home'
import MarkdownIt from 'markdown-it'

const md = new MarkdownIt()
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
const versions = ref<VersionInfo>({
  release: '',
  versionCode: 0,
  fontBranch: '',
  backendBranch: '',
  mysqlBranch: '',
  agentBranch: '',
  webhookBranch: '',
})
const authConfig = ref<AuthConfig | null>(null)
const updateInfo = ref<UpdateInfo | null>(null)

// 是否有更新
const hasUpdate = computed(() => updateInfo.value !== null)

async function loadSystemConfig() {
  try {
    const res = await homeApi.getSystemConfig()
    versions.value = res.data.data.versions
    authConfig.value = res.data.data.auth
    updateInfo.value = res.data.data.update
    // 如果不需要认证，清除 token
    if (authConfig.value && !authConfig.value.enable) {
      localStorage.removeItem('token')
    }
  } catch (err) {
    console.error('获取系统配置失败', err)
  }
}

// 更新详情弹窗
const showUpdateDialog = ref(false)

// 渲染 changelog 为 HTML
const changelogHtml = computed(() => {
  if (!updateInfo.value?.changelog) return ''
  return md.render(updateInfo.value.changelog)
})

// 显示更新详情
function showUpdateDetail() {
  if (!updateInfo.value) return
  showUpdateDialog.value = true
}

// 是否显示退出登录（需要认证才显示）
const showLogout = computed(() => authConfig.value?.enable !== false)

function openAbout() {
  showAbout.value = true
  if (!versions.value.release) {
    loadSystemConfig()
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
  // 预加载系统配置
  loadSystemConfig()
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
      </van-cell-group>

      <!-- 系统管理 -->
      <van-cell-group inset title="系统管理">
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
        <van-cell
          title="系统信息"
          icon="setting-o"
          is-link
          to="/setting/system"
        />
      </van-cell-group>

      <!-- 其他 -->
      <van-cell-group inset title="其他">
        <van-cell
          title="关于"
          icon="info-o"
          is-link
          class="about-cell"
          @click="openAbout"
        >
          <template #title>
            <span>关于</span>
            <span v-if="hasUpdate" class="update-dot"></span>
          </template>
        </van-cell>
        <van-cell
          v-if="showLogout"
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

        <!-- 版本标签 -->
        <div class="about-version-tag">
          <span class="version-label">Version</span>
          <span class="version-value">{{ versions.release || '...' }} ({{ versions.versionCode || '...' }})</span>
        </div>

        <!-- 更新提示 -->
        <div v-if="updateInfo" class="update-banner" @click="showUpdateDetail">
          <span class="update-icon">🎉</span>
          <span class="update-text">发现新版本 {{ updateInfo.version }} ({{ updateInfo.versionCode }})</span>
          <van-icon name="arrow" class="update-arrow" />
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

    <!-- 更新详情弹窗 -->
    <van-popup
      v-model:show="showUpdateDialog"
      round
      closeable
      close-icon="cross"
      teleport="body"
      :style="{ width: '85%', maxWidth: '320px' }"
    >
      <div v-if="updateInfo" class="update-dialog">
        <div class="update-header">
          <div class="update-version">{{ updateInfo.version }} ({{ updateInfo.versionCode }})</div>
          <div class="update-date">发布于 {{ updateInfo.releaseDate }}</div>
        </div>
        <div class="update-changelog">
          <div class="changelog-title">更新内容</div>
          <div class="changelog-content markdown-body" v-html="changelogHtml"></div>
        </div>
        <a
          href="https://mercys-organization-2.gitbook.io/easyaccounts/version"
          target="_blank"
          class="update-tip"
        >
          <van-icon name="info-o" />
          <span>查看更新指南</span>
          <van-icon name="arrow" />
        </a>
        <van-button type="primary" block round @click="showUpdateDialog = false">我知道了</van-button>
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
}

.version-label {
  color: var(--color-text-tertiary);
}

.version-value {
  color: var(--color-transfer);
  font-weight: 600;
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

/* 关于单元格红点 */
.about-cell :deep(.van-cell__title) {
  display: flex;
  align-items: center;
  gap: 6px;
}

.update-dot {
  width: 8px;
  height: 8px;
  background: var(--color-expense);
  border-radius: 50%;
}

/* 更新提示横幅 */
.update-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
  padding: 12px 14px;
  background: linear-gradient(135deg, rgba(82, 196, 26, 0.12) 0%, rgba(24, 144, 255, 0.12) 100%);
  border-radius: 10px;
  cursor: pointer;
}

.update-banner:active {
  opacity: 0.8;
}

.update-icon {
  font-size: 16px;
}

.update-text {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.update-arrow {
  color: var(--color-text-tertiary);
  font-size: 14px;
}

/* 更新详情弹窗 */
.update-dialog {
  padding: 24px;
  background: var(--color-bg-card);
}

.update-dialog .update-header {
  text-align: center;
  margin-bottom: 20px;
}

.update-dialog .update-version {
  font-size: 24px;
  font-weight: 700;
  color: var(--color-income);
}

.update-dialog .update-date {
  margin-top: 4px;
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.update-dialog .update-changelog {
  background: var(--color-bg-page);
  border-radius: 10px;
  padding: 14px;
  margin-bottom: 12px;
}

.update-dialog .changelog-title {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 10px;
}

.update-dialog .changelog-content {
  font-size: 13px;
  line-height: 1.7;
  color: var(--color-text-secondary);
}

.update-dialog .changelog-content.markdown-body :deep(h1),
.update-dialog .changelog-content.markdown-body :deep(h2),
.update-dialog .changelog-content.markdown-body :deep(h3) {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 6px 0;
}

.update-dialog .changelog-content.markdown-body :deep(ul),
.update-dialog .changelog-content.markdown-body :deep(ol) {
  margin: 0;
  padding-left: 18px;
}

.update-dialog .changelog-content.markdown-body :deep(li) {
  margin: 3px 0;
}

.update-dialog .changelog-content.markdown-body :deep(p) {
  margin: 0 0 6px 0;
}

.update-dialog .changelog-content.markdown-body :deep(p:last-child) {
  margin-bottom: 0;
}

.update-dialog .update-tip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: var(--color-transfer-bg);
  border-radius: 8px;
  font-size: 13px;
  color: var(--color-transfer);
  text-decoration: none;
  margin-bottom: 16px;
}

.update-dialog .update-tip:active {
  opacity: 0.8;
}

.update-dialog .update-tip span {
  flex: 1;
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
