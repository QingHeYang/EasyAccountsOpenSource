<script setup lang="ts">
import { computed } from 'vue'
import { Sunny } from '@element-plus/icons-vue'
import { useThemeStore } from '@shared/stores/theme'

const themeStore = useThemeStore()

// emoji 跟移动端 SystemSettings.vue 保持一致（带 ️ 变体选择符）
const themeOptions = [
  { value: 'light', label: '浅色', emoji: '☀️' },
  { value: 'dark', label: '深色', emoji: '🌙' },
  { value: 'system', label: '跟随系统', emoji: '⚙️' },
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
          <span class="theme-emoji">{{ opt.emoji }}</span>
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

.theme-emoji {
  font-size: 28px;
  line-height: 1;
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
