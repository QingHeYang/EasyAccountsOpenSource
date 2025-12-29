import { defineStore } from 'pinia'
import { ref } from 'vue'

/**
 * Mobile 端应用状态
 */
export const useMobileAppStore = defineStore('mobile-app', () => {
  // 当前激活的底部导航
  const activeTab = ref('home')

  // 页面是否正在刷新
  const isRefreshing = ref(false)

  function setActiveTab(tab: string) {
    activeTab.value = tab
  }

  function setRefreshing(refreshing: boolean) {
    isRefreshing.value = refreshing
  }

  return {
    activeTab,
    isRefreshing,
    setActiveTab,
    setRefreshing,
  }
})
