<script setup lang="ts">
import { ref } from 'vue'
import AnalysisMain from './AnalysisMain.vue'
import TypeDetail from './TypeDetail.vue'

type TabType = 'main' | 'type'

const activeTab = ref<TabType>('main')

// 从主页面点击分类时，切换到分类详情并传递参数
const selectedTypeId = ref<number | null>(null)
const selectedStartDate = ref('')
const selectedEndDate = ref('')

function switchTab(tab: TabType) {
  activeTab.value = tab
}

function onTypeClick(typeId: number, startDate: string, endDate: string) {
  selectedTypeId.value = typeId
  selectedStartDate.value = startDate
  selectedEndDate.value = endDate
  activeTab.value = 'type'
}
</script>

<template>
  <div class="analysis-page">
    <!-- 页面标题 + Tab 切换 -->
    <div class="page-header">
      <div class="tab-nav">
        <span
          class="tab-item"
          :class="{ active: activeTab === 'main' }"
          @click="switchTab('main')"
        >
          统计
        </span>
        <span class="tab-divider">|</span>
        <span
          class="tab-item"
          :class="{ active: activeTab === 'type' }"
          @click="switchTab('type')"
        >
          分类
        </span>
      </div>
    </div>

    <!-- 内容区 -->
    <div class="page-content">
      <AnalysisMain
        v-if="activeTab === 'main'"
        @type-click="onTypeClick"
      />
      <TypeDetail
        v-else
        :initial-type-id="selectedTypeId"
        :initial-start-date="selectedStartDate"
        :initial-end-date="selectedEndDate"
      />
    </div>
  </div>
</template>

<style scoped>
.analysis-page {
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
