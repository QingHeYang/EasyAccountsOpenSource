<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import FlowList from './flow/FlowList.vue'
import Screen from './flow/Screen.vue'

type TabType = 'list' | 'screen'

const route = useRoute()
const activeTab = ref<TabType>('list')

function switchTab(tab: TabType) {
  activeTab.value = tab
}

// 监听路由参数变化
watch(() => route.query, (query) => {
  // 如果带 tab=screen 参数则切换到筛选
  if (query.tab === 'screen') {
    activeTab.value = 'screen'
  }
  // 如果带 month 参数则切回明细
  else if (query.month) {
    activeTab.value = 'list'
  }
}, { immediate: true })
</script>

<template>
  <div class="flow-page">
    <!-- 页面标题 + Tab 切换 -->
    <div class="page-header">
      <div class="tab-nav">
        <span
          class="tab-item"
          :class="{ active: activeTab === 'list' }"
          @click="switchTab('list')"
        >
          明细
        </span>
        <span class="tab-divider">|</span>
        <span
          class="tab-item"
          :class="{ active: activeTab === 'screen' }"
          @click="switchTab('screen')"
        >
          筛选
        </span>
      </div>
    </div>

    <!-- 内容区 -->
    <div class="page-content">
      <FlowList v-if="activeTab === 'list'" />
      <Screen v-else />
    </div>
  </div>
</template>

<style scoped>
.flow-page {
  padding: 20px 20px 12px 20px;
  position: relative;
  min-height: calc(100vh - 80px);
}

.page-header {
  height: 40px;
  margin-bottom: 20px;
}

/* Tab 导航 */
.tab-nav {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  height: 100%;
}

.tab-item {
  font-weight: 500;
  color: var(--color-text-tertiary);
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 20px;
  line-height: 1;
}

.tab-item:hover {
  color: var(--color-text-secondary);
}

.tab-item.active {
  color: var(--color-transfer);
  font-size: 28px;
  font-weight: 600;
}

.tab-divider {
  color: var(--color-text-quaternary);
  font-size: 20px;
  font-weight: 300;
  line-height: 1;
  user-select: none;
}

.page-content {
  /* 内容区 */
}
</style>
