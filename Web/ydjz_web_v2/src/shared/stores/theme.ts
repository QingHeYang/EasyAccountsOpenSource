import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import {
  type ThemeMode,
  getStoredTheme,
  getEffectiveTheme,
  setTheme,
  toggleTheme,
  watchSystemTheme,
} from '../utils/theme'

export const useThemeStore = defineStore('theme', () => {
  // 用户选择的主题模式
  const mode = ref<ThemeMode>(getStoredTheme())

  // 实际显示的主题
  const effectiveTheme = computed(() => {
    return mode.value === 'system' ? getEffectiveTheme() : mode.value
  })

  // 是否为暗色模式
  const isDark = computed(() => effectiveTheme.value === 'dark')

  // 设置主题
  function set(newMode: ThemeMode) {
    mode.value = newMode
    setTheme(newMode)
  }

  // 切换主题
  function toggle() {
    toggleTheme()
    mode.value = getStoredTheme()
  }

  // 监听系统主题变化
  watchSystemTheme((theme) => {
    if (mode.value === 'system') {
      // 触发响应式更新
      mode.value = 'system'
    }
  })

  return {
    mode,
    effectiveTheme,
    isDark,
    set,
    toggle,
  }
})
