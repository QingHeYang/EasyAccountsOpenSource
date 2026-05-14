<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { useNotice } from '@shared/composables'
import NoticeCard from '@mobile/components/notice/NoticeCard.vue'

const props = defineProps<{
  show: boolean
}>()

const emit = defineEmits<{
  (e: 'update:show', value: boolean): void
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

watch(() => props.show, (val) => {
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
  <van-popup
    :show="show"
    round
    closeable
    close-icon="cross"
    teleport="body"
    position="bottom"
    :style="{ height: '70%' }"
    @update:show="emit('update:show', $event)"
  >
    <div class="notice-popup">
      <div class="popup-header">
        <div class="popup-title">公告</div>
      </div>

      <div class="popup-body">
        <div v-if="loading" class="notice-loading">
          <van-loading size="24" />
        </div>

        <div v-else-if="notices.length === 0" class="notice-empty">
          <van-icon name="volume-o" size="48" class="empty-icon" />
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
    </div>
  </van-popup>
</template>

<style scoped>
.notice-popup {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-card);
}

.popup-header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--color-border-light);
}

.popup-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.popup-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.notice-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
}

.notice-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
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
