<script setup lang="ts">
import { computed } from 'vue'
import { Sun, Moon, Monitor } from 'lucide-vue-next'
import { useThemeStore } from '@shared/stores/theme'

const themeStore = useThemeStore()

// 跟移动端 SystemSettings.vue 保持一致（Lucide Sun/Moon/Monitor）
const themeOptions = [
  { value: 'light', label: '浅色', icon: Sun },
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
      <Sun :size="18" :stroke-width="1.75" />
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
          <component :is="opt.icon" :size="22" :stroke-width="1.75" class="theme-icon" />
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

.theme-icon {
  display: block;
  color: var(--color-text-secondary);
}

.theme-option.active {
  border-color: var(--color-transfer);
  background: rgba(24, 144, 255, 0.08);
}

.theme-option.active .theme-icon {
  color: var(--color-transfer);
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
