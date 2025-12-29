<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useThemeStore } from '@shared/stores/theme'

const route = useRoute()
const themeStore = useThemeStore()

// Vant 主题：'light' | 'dark'
const vantTheme = computed(() => themeStore.effectiveTheme)

// Tab 配置
const tabs = [
  { path: '/board', icon: 'balance-pay', label: '总览' },
  { path: '/flow', icon: 'records-o', label: '明细' },
  { path: '/analysis', icon: 'chart-trending-o', label: '统计' },
  { path: '/setting', icon: 'setting-o', label: '设置' },
]

// 当前激活的 tab 索引
const activeIndex = computed(() => {
  const idx = tabs.findIndex(tab => route.path === tab.path)
  return idx >= 0 ? idx : 0
})

// 滑块位置样式
const sliderStyle = computed(() => ({
  transform: `translateX(${activeIndex.value * 100}%)`,
}))
</script>

<template>
  <van-config-provider :theme="vantTheme">
    <div class="home-layout">
      <!-- 背景装饰 -->
      <div class="bg-decoration">
        <!-- 红色银行卡（右上角） -->
        <div class="card-shape card-red"></div>
        <!-- 绿色银行卡（左下角） -->
        <div class="card-shape card-green"></div>
        <!-- 蓝色三条线 -->
        <div class="blue-lines">
          <div class="line line-1"></div>
          <div class="line line-2"></div>
          <div class="line line-3"></div>
        </div>
      </div>

      <router-view v-slot="{ Component }">
        <keep-alive>
          <component :is="Component" class="page-content" />
        </keep-alive>
      </router-view>

      <!-- 浮动 Tabbar 容器 -->
      <div class="tabbar-wrapper">
        <div class="floating-tabbar">
          <!-- 滑块背景 -->
          <div class="slider-track">
            <div class="slider" :style="sliderStyle"></div>
          </div>
          <!-- Tab 项 -->
          <router-link
            v-for="(tab, index) in tabs"
            :key="tab.path"
            :to="tab.path"
            class="tab-item"
            :class="{ active: activeIndex === index }"
          >
            <van-icon :name="tab.icon" size="22" />
            <span class="tab-label">{{ tab.label }}</span>
          </router-link>
        </div>
      </div>
    </div>
  </van-config-provider>
</template>

<style scoped>
.home-layout {
  min-height: 100vh;
  background: transparent; /* 透明，使用 body 背景 */
  position: relative;
  /* 确保内容可以滚动到 tabbar 下方 */
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

/* 银行卡样式 */
.card-shape {
  position: absolute;
  width: 360px;
  height: 220px;
  border-radius: 20px;
  opacity: 0.12;
}

.card-red {
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a5a 100%);
  top: -100px;
  right: -160px;
  transform: rotate(-15deg);
}

.card-green {
  background: linear-gradient(135deg, #51cf66 0%, #40c057 100%);
  bottom: 120px;
  left: -180px;
  transform: rotate(20deg);
}

/* 蓝色三条线 */
.blue-lines {
  position: absolute;
  width: 360px;
  height: 220px;
  bottom: 320px;
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

.page-content {
  padding-bottom: 100px;
  position: relative;
  z-index: 1;
}

.tabbar-wrapper {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 16px 24px calc(20px + env(safe-area-inset-bottom));
  pointer-events: none;
  z-index: 10; /* 降低层级，让弹窗能覆盖 */
}

/* 自定义 Tabbar 样式 */
.floating-tabbar {
  position: relative;
  display: flex;
  align-items: center;
  height: 56px;
  padding: 0 8px;
}

/* 滑块轨道 */
.slider-track {
  position: absolute;
  top: 6px;
  bottom: 6px;
  left: 8px;
  right: 8px;
  pointer-events: none;
}

/* 滑块 */
.slider {
  width: calc(100% / 4);
  height: 100%;
  background: var(--color-transfer);
  border-radius: 14px;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Tab 项 */
.tab-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  text-decoration: none;
  color: var(--color-text-tertiary);
  transition: color 0.2s ease;
  position: relative;
  z-index: 1;
}

.tab-item.active {
  color: #ffffff;
}

.tab-label {
  font-size: 11px;
  font-weight: 500;
}
</style>

<!-- 非 scoped 样式用于主题切换 -->
<style>
.floating-tabbar {
  pointer-events: auto;
  border-radius: 20px;
  overflow: hidden;

  /* 亮色模式 - 轻度毛玻璃 */
  background: rgba(255, 255, 255, 0.65);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.5);
}

/* 暗色模式 */
html.dark .floating-tabbar {
  background: rgba(40, 40, 40, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.3);
}

html.dark .slider {
  background: rgba(116, 192, 252, 0.25);
}

html.dark .tab-item.active {
  color: var(--color-transfer);
}
</style>
