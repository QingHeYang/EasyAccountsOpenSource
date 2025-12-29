import { defineStore } from 'pinia'
import { ref } from 'vue'

/**
 * Desktop 端应用状态
 */
export const useDesktopAppStore = defineStore('desktop-app', () => {
  // 侧边栏折叠状态
  const sidebarCollapsed = ref(false)

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  function setSidebarCollapsed(collapsed: boolean) {
    sidebarCollapsed.value = collapsed
  }

  return {
    sidebarCollapsed,
    toggleSidebar,
    setSidebarCollapsed,
  }
})
