<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { Bell } from '@element-plus/icons-vue'
import { useNotice } from '@shared/composables'
import NoticeCard from '@desktop/components/notice/NoticeCard.vue'

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
}>()

const {
  notices,
  loading,
  hasUnread,
  unreadCount,
  isUnread,
  loadNotices,
  markAllAsRead,
  renderMarkdown,
} = useNotice()

watch(() => props.visible, (val) => {
  if (val) markAllAsRead()
})

onMounted(() => {
  loadNotices()
})

defineExpose({
  hasUnread,
  unreadCount,
  loadNotices,
})
</script>

<template>
  <el-drawer
    :model-value="visible"
    title="公告"
    direction="rtl"
    size="500px"
    class="setting-drawer notice-drawer"
    @update:model-value="emit('update:visible', $event)"
  >
    <div class="notice-content" v-loading="loading">
      <div v-if="!loading && notices.length === 0" class="notice-empty">
        <el-icon :size="48" class="empty-icon"><Bell /></el-icon>
        <div class="empty-text">暂无公告</div>
      </div>

      <div v-else class="notice-list">
        <NoticeCard
          v-for="notice in notices"
          :key="notice.id"
          :notice="notice"
          :unread="isUnread(notice)"
          :content-html="renderMarkdown(notice.content)"
        />
      </div>
    </div>
  </el-drawer>
</template>

<style scoped>
.notice-content {
  min-height: 200px;
}

.notice-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 0;
  color: var(--color-text-tertiary);
}

.notice-empty .empty-icon {
  margin-bottom: 12px;
  opacity: 0.5;
}

.notice-empty .empty-text {
  font-size: 14px;
}

.notice-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
</style>
