<script setup lang="ts">
import { computed } from 'vue'
import { Sunny, Moon, Monitor } from '@element-plus/icons-vue'
import { useThemeStore } from '@shared/stores/theme'

const themeStore = useThemeStore()

const themeOptions = [
  { value: 'light', label: '浅色', icon: Sunny },
  { value: 'dark', label: '深色', icon: Moon },
  { value: 'system', label: '跟随系统', icon: Monitor },
] as const

const currentTheme = computed({
  get: () => themeStore.mode,
  set: (val) => themeStore.set(val as 'light' | 'dark' | 'system'),
})
</script>

<template>
  <div class="sys-section">
    <div class="sys-section-header">
      <el-icon :size="18"><Sunny /></el-icon>
      <span>外观设置</span>
    </div>
    <div class="sys-section-body">
      <div class="theme-selector">
        <div
          v-for="opt in themeOptions"
          :key="opt.value"
          class="theme-option"
          :class="{ active: currentTheme === opt.value }"
          @click="currentTheme = opt.value"
        >
          <el-icon :size="20"><component :is="opt.icon" /></el-icon>
          <span>{{ opt.label }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.theme-selector {
  display: flex;
  gap: 10px;
}

.theme-option {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px 12px;
  background: var(--color-bg-card);
  border: 2px solid transparent;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.theme-option:hover {
  background: var(--color-bg-active);
}

.theme-option.active {
  border-color: var(--color-transfer);
  background: rgba(24, 144, 255, 0.08);
}

.theme-option span {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.theme-option.active span {
  color: var(--color-transfer);
  font-weight: 500;
}

html.dark .theme-option {
  background: rgba(255, 255, 255, 0.04);
}

html.dark .theme-option:hover {
  background: rgba(255, 255, 255, 0.08);
}

html.dark .theme-option.active {
  background: rgba(116, 192, 252, 0.1);
  border-color: var(--color-transfer);
}
</style>
