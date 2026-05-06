<script setup lang="ts">
import { computed } from 'vue'
import { Monitor as VersionIcon } from '@element-plus/icons-vue'
import type { VersionInfo } from '@shared/api/home'

const props = defineProps<{
  versions: VersionInfo
}>()

const versionItems = computed(() => [
  { label: '前端', value: props.versions.fontBranch || '-' },
  { label: '后端', value: props.versions.backendBranch || '-' },
  { label: '数据库', value: props.versions.mysqlBranch || '-' },
  { label: 'AI Agent', value: props.versions.agentBranch || '-' },
])
</script>

<template>
  <div class="sys-section">
    <div class="sys-section-header">
      <el-icon :size="18"><VersionIcon /></el-icon>
      <span>版本信息</span>
    </div>
    <div class="sys-section-body">
      <div class="version-list">
        <div
          v-for="item in versionItems"
          :key="item.label"
          class="version-item"
        >
          <span class="version-label">{{ item.label }}</span>
          <span class="version-value">{{ item.value }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.version-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.version-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background: var(--color-bg-card);
  border-radius: 8px;
}

.version-label {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.version-value {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-primary);
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

html.dark .version-item {
  background: rgba(255, 255, 255, 0.04);
}
</style>
