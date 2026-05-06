<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { House, List, TrendCharts, Setting, Bell } from '@element-plus/icons-vue'
import logoUrl from '@shared/assets/logo.png'
import { AIDrawer, AITriggerButton } from '@desktop/components/ai-plus'
import NotificationCenter from '@desktop/components/NotificationCenter.vue'
import { aiApi } from '@shared/api/ai'
import { noticeApi } from '@shared/api/notice'
import { isHandledError } from '@shared/api/request'

const route = useRoute()
const router = useRouter()

// AI 抽屉状态
const aiDrawerOpen = ref(false)

// AI 服务可用状态
const aiServiceAvailable = ref(false)

// 通知中心
const notificationOpen = ref(false)
const unreadCount = ref(0)
const unreadDisplay = computed(() => (unreadCount.value > 99 ? '99+' : String(unreadCount.value)))

/** 通知点击跳转对应规则：关抽屉，跳到设置页并触发打开规则编辑
 *  - 在别的路由：sessionStorage 埋值 + 跳 /setting，settings 页 onMounted 读
 *  - 已在 /setting：dispatch 全局自定义事件，settings 页运行时监听
 */
function onNotificationNavigate(payload: { ruleId: number }) {
  notificationOpen.value = false
  const ruleIdStr = String(payload.ruleId)
  if (route.path.startsWith('/setting')) {
    window.dispatchEvent(
      new CustomEvent('open-scheduled-rule', { detail: { ruleId: payload.ruleId } })
    )
  } else {
    sessionStorage.setItem('pendingOpenScheduledRule', ruleIdStr)
    router.push('/setting')
  }
}

async function loadUnreadCount() {
  try {
    const res = await noticeApi.list({ isRead: false })
    unreadCount.value = (res.data.data ?? []).length
  } catch (err) {
    if (!isHandledError(err)) {
      // 静默：顶栏徽章不打扰用户
      unreadCount.value = 0
    }
  }
}

// 滚动状态
const isScrolled = ref(false)

function handleScroll() {
  isScrolled.value = window.scrollY > 20
}

// 检测 AI 服务可用性
async function checkAiService() {
  const health = await aiApi.checkHealth()
  // 服务可用且 LLM 已配置
  aiServiceAvailable.value = health !== null && health.data?.llm?.configured === true
}

onMounted(() => {
  window.addEventListener('scroll', handleScroll, { passive: true })
  handleScroll()
  checkAiService()
  loadUnreadCount()
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})

// Tab 配置
const tabs = [
  { path: '/board', icon: House, label: '总览' },
  { path: '/flow', icon: List, label: '明细' },
  { path: '/analysis', icon: TrendCharts, label: '统计' },
  { path: '/setting', icon: Setting, label: '设置' },
]

// 当前激活的 tab 索引
const activeIndex = computed(() => {
  const idx = tabs.findIndex(tab => route.path.startsWith(tab.path))
  return idx >= 0 ? idx : 0
})

// 滑块位置样式（横向）
const sliderStyle = computed(() => ({
  transform: `translateX(${activeIndex.value * 100}%)`,
}))
</script>

<template>
  <div class="home-layout">
    <!-- 背景装饰 -->
    <div class="bg-decoration">
      <div class="card-shape card-red"></div>
      <div class="card-shape card-green"></div>
      <div class="blue-lines">
        <div class="line line-1"></div>
        <div class="line line-2"></div>
        <div class="line line-3"></div>
      </div>
    </div>

    <!-- 顶部导航栏 -->
    <header class="top-header" :class="{ 'is-scrolled': isScrolled }">
      <div class="header-inner">
        <!-- 左侧 Logo -->
        <div class="header-left">
          <img :src="logoUrl" alt="Logo" class="logo-img" />
          <span class="app-name">EasyAccounts</span>
        </div>

        <!-- 中间导航 -->
        <nav class="header-nav">
          <div class="floating-nav">
            <!-- 滑块 -->
            <div class="slider-track">
              <div class="slider" :style="sliderStyle"></div>
            </div>
            <!-- Nav 项 -->
            <router-link
              v-for="(tab, index) in tabs"
              :key="tab.path"
              :to="tab.path"
              class="nav-item"
              :class="{ active: activeIndex === index }"
            >
              <el-icon :size="18">
                <component :is="tab.icon" />
              </el-icon>
              <span class="nav-label">{{ tab.label }}</span>
            </router-link>
          </div>
        </nav>

        <!-- 右侧：通知铃铛 -->
        <div class="header-right">
          <button
            class="bell-btn"
            type="button"
            title="消息通知"
            @click="notificationOpen = true"
          >
            <el-icon :size="20"><Bell /></el-icon>
            <span v-if="unreadCount > 0" class="bell-badge">{{ unreadDisplay }}</span>
          </button>
        </div>
      </div>
    </header>

    <!-- 内容容器 -->
    <div class="content-wrapper" :class="{ 'drawer-open': aiDrawerOpen }">
      <!-- 主内容区 -->
      <main class="main-content">
        <router-view v-slot="{ Component }">
          <keep-alive>
            <component :is="Component" />
          </keep-alive>
        </router-view>
      </main>

      <!-- AI 抽屉 -->
      <AIDrawer v-model="aiDrawerOpen" />
    </div>

    <!-- AI 触发按钮 (仅在 AI 服务可用时显示) -->
    <AITriggerButton v-if="aiServiceAvailable" :visible="!aiDrawerOpen" @click="aiDrawerOpen = true" />

    <!-- 通知中心 -->
    <NotificationCenter
      v-model:visible="notificationOpen"
      @changed="loadUnreadCount"
      @navigate="onNotificationNavigate"
    />
  </div>
</template>

<style scoped>
.home-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow-x: hidden;
}

/* 背景装饰 */
.bg-decoration {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  overflow: hidden;
  z-index: 0;
}

.card-shape {
  position: absolute;
  width: 500px;
  height: 300px;
  border-radius: 24px;
  opacity: 0.10;
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

.blue-lines {
  position: absolute;
  width: 400px;
  height: 240px;
  bottom: 150px;
  right: -100px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 28px;
  transform: rotate(-20deg);
}

.line {
  height: 32px;
  border-radius: 16px;
  background: linear-gradient(90deg, #339af0 0%, #228be6 100%);
  opacity: 0.10;
}

.line-1 { width: 85%; margin-left: 15%; }
.line-2 { width: 70%; margin-left: 5%; }
.line-3 { width: 80%; margin-left: 20%; }

/* 顶部导航栏 */
.top-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  padding: 16px 32px;
  transition: background 0.3s, backdrop-filter 0.3s, box-shadow 0.3s;
}

.top-header.is-scrolled {
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.06);
}

.header-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  max-width: 1400px;
  margin: 0 auto;
}

/* 左侧 Logo */
.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 180px; /* 与右侧对称，保持胶囊居中 */
}

.logo-img {
  width: 36px;
  height: 36px;
}

.app-name {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-primary);
}

/* 中间导航 */
.header-nav {
  flex: 1;
  display: flex;
  justify-content: center;
}

/* 右侧：通知铃铛 */
.header-right {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  min-width: 180px; /* 与左侧 logo+app-name 视觉平衡，保持胶囊居中 */
}

.bell-btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: rgba(255, 255, 255, 0.65);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.5);
  border-radius: 50%;
  color: var(--color-text-secondary);
  cursor: pointer;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  transition: all 0.2s;
  padding: 0;
}

.bell-btn:hover {
  color: var(--color-transfer);
  transform: translateY(-1px);
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.08);
}

.bell-btn:active {
  transform: translateY(0);
}

.bell-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  background: var(--color-expense);
  color: #fff;
  border-radius: 9px;
  font-size: 11px;
  font-weight: 600;
  line-height: 18px;
  text-align: center;
  box-shadow: 0 0 0 2px var(--color-bg-card, #fff);
  font-variant-numeric: tabular-nums;
}

.floating-nav {
  position: relative;
  display: flex;
  align-items: center;
  height: 48px;
  padding: 0 6px;
  border-radius: 24px;

  /* 毛玻璃效果 */
  background: rgba(255, 255, 255, 0.65);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.5);
}

/* 滑块轨道 */
.slider-track {
  position: absolute;
  top: 6px;
  bottom: 6px;
  left: 6px;
  right: 6px;
  pointer-events: none;
}

/* 滑块 */
.slider {
  width: calc(100% / 4);
  height: 100%;
  background: var(--color-transfer);
  border-radius: 18px;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 导航项 */
.nav-item {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 0 24px;
  height: 36px;
  text-decoration: none;
  color: var(--color-text-tertiary);
  transition: color 0.2s ease;
  white-space: nowrap;
}

.nav-item.active {
  color: #ffffff;
}

.nav-item:hover:not(.active) {
  color: var(--color-text-primary);
}

.nav-label {
  font-size: 14px;
  font-weight: 500;
}

/* 内容容器 */
.content-wrapper {
  display: flex;
  flex: 1;
  padding-top: 80px;
  transition: padding-right 0.3s ease;
}

.content-wrapper.drawer-open {
  padding-right: 460px;
}

/* 主内容区 */
.main-content {
  flex: 1;
  padding: 0 32px 32px;
  position: relative;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
}
</style>

<!-- 暗色模式样式 -->
<style>
html.dark .top-header.is-scrolled {
  background: rgba(20, 20, 20, 0.75);
  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.3);
}

html.dark .floating-nav {
  background: rgba(40, 40, 40, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.3);
}

html.dark .slider {
  background: rgba(116, 192, 252, 0.25);
}

html.dark .nav-item.active {
  color: var(--color-transfer);
}

html.dark .card-shape,
html.dark .line {
  opacity: 0.06;
}

html.dark .bell-btn {
  background: rgba(40, 40, 40, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
}

html.dark .bell-btn:hover {
  background: rgba(50, 50, 50, 0.8);
}

html.dark .bell-badge {
  box-shadow: 0 0 0 2px #1a1a1a;
}
</style>
