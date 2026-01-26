<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { homeApi, type Notice } from '@shared/api/home'

const props = defineProps<{
  show: boolean
}>()

const emit = defineEmits<{
  (e: 'update:show', value: boolean): void
}>()

// 公告列表
const notices = ref<Notice[]>([])
const loading = ref(false)

// 已读状态存储 key
const NOTICE_READ_KEY = 'easyaccounts_read_notices'

// 获取已读公告 ID 列表
function getReadNoticeIds(): number[] {
  try {
    const stored = localStorage.getItem(NOTICE_READ_KEY)
    return stored ? JSON.parse(stored) : []
  } catch {
    return []
  }
}

// 保存已读公告 ID
function saveReadNoticeIds(ids: number[]) {
  localStorage.setItem(NOTICE_READ_KEY, JSON.stringify(ids))
}

// 未读公告数量
const unreadCount = computed(() => {
  const readIds = getReadNoticeIds()
  return notices.value.filter(n => !readIds.includes(n.id)).length
})

// 是否有未读公告
const hasUnread = computed(() => unreadCount.value > 0)

// 加载公告列表
async function loadNotices() {
  loading.value = true
  try {
    const res = await homeApi.getNotices()
    if (res.data.code === 0) {
      notices.value = res.data.data || []
    }
  } catch (err) {
    console.error('获取公告列表失败', err)
  } finally {
    loading.value = false
  }
}

// 标记所有为已读
function markAllAsRead() {
  if (notices.value.length > 0) {
    const allIds = notices.value.map(n => n.id)
    saveReadNoticeIds(allIds)
  }
}

// 打开公告链接
function openNoticeLink(url: string) {
  if (url) {
    window.open(url, '_blank')
  }
}

// 弹窗打开时标记已读
watch(() => props.show, (val) => {
  if (val) {
    markAllAsRead()
  }
})

// 组件挂载时加载公告
onMounted(() => {
  loadNotices()
})

// 暴露给父组件
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
    :style="{ height: '60%', maxHeight: '500px' }"
    @update:show="emit('update:show', $event)"
  >
    <div class="notice-popup">
      <div class="popup-header">
        <div class="popup-title">公告</div>
      </div>

      <div class="popup-body">
        <!-- 加载中 -->
        <div v-if="loading" class="notice-loading">
          <van-loading size="24" />
        </div>

        <!-- 无公告 -->
        <div v-else-if="notices.length === 0" class="notice-empty">
          <van-icon name="volume-o" size="48" class="empty-icon" />
          <div class="empty-text">暂无公告</div>
        </div>

        <!-- 公告列表 -->
        <div v-else class="notice-list">
          <div
            v-for="notice in notices"
            :key="notice.id"
            class="notice-item"
            :class="{ 'has-link': notice.url }"
            @click="openNoticeLink(notice.url)"
          >
            <div class="notice-header">
              <div class="notice-title">{{ notice.title }}</div>
              <div class="notice-date">{{ notice.date }}</div>
            </div>
            <div class="notice-body">{{ notice.content }}</div>
            <div v-if="notice.url" class="notice-link">
              <van-icon name="link-o" size="14" />
              <span>查看详情</span>
            </div>
          </div>
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

.notice-item {
  padding: 14px;
  background: var(--color-bg-page);
  border-radius: 12px;
  transition: all 0.2s;
}

.notice-item.has-link {
  cursor: pointer;
}

.notice-item.has-link:active {
  opacity: 0.8;
}

.notice-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.notice-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.notice-date {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.notice-body {
  font-size: 14px;
  color: var(--color-text-secondary);
  line-height: 1.6;
}

.notice-link {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 10px;
  font-size: 13px;
  color: var(--color-transfer);
}
</style>

<style>
/* 暗色模式 */
html.dark .notice-item {
  background: rgba(255, 255, 255, 0.03);
}
</style>
