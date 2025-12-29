/**
 * 主题工具函数
 */

export type ThemeMode = 'light' | 'dark' | 'system'

const THEME_KEY = 'theme'

/** 获取系统主题偏好 */
export function getSystemTheme(): 'light' | 'dark' {
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

/** 获取存储的主题设置 */
export function getStoredTheme(): ThemeMode {
  const stored = localStorage.getItem(THEME_KEY)
  if (stored === 'light' || stored === 'dark' || stored === 'system') {
    return stored
  }
  return 'system'
}

/** 获取实际应用的主题 */
export function getEffectiveTheme(): 'light' | 'dark' {
  const stored = getStoredTheme()
  return stored === 'system' ? getSystemTheme() : stored
}

/** 应用主题到 DOM */
export function applyTheme(theme: 'light' | 'dark') {
  const html = document.documentElement

  if (theme === 'dark') {
    html.classList.add('dark', 'van-theme-dark')
  } else {
    html.classList.remove('dark', 'van-theme-dark')
  }
}

/** 设置主题 */
export function setTheme(mode: ThemeMode) {
  localStorage.setItem(THEME_KEY, mode)
  applyTheme(mode === 'system' ? getSystemTheme() : mode)
}

/** 切换主题（亮 <-> 暗） */
export function toggleTheme() {
  const current = getEffectiveTheme()
  setTheme(current === 'dark' ? 'light' : 'dark')
}

/** 监听系统主题变化 */
export function watchSystemTheme(callback: (theme: 'light' | 'dark') => void) {
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')

  const handler = (e: MediaQueryListEvent) => {
    if (getStoredTheme() === 'system') {
      const theme = e.matches ? 'dark' : 'light'
      applyTheme(theme)
      callback(theme)
    }
  }

  mediaQuery.addEventListener('change', handler)

  return () => mediaQuery.removeEventListener('change', handler)
}

/** 初始化主题（在 Vue app 挂载后调用） */
export function initTheme() {
  const theme = getEffectiveTheme()
  applyTheme(theme)

  // 监听系统主题变化
  watchSystemTheme(() => {})
}
