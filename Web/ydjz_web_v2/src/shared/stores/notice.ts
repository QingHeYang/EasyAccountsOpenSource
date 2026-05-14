import { ref } from 'vue'
import { defineStore } from 'pinia'
import { noticeApi } from '@shared/api/notice'
import { isHandledError } from '@shared/api/request'

/**
 * 用户通知中心 Store（v2.7.0+）
 *
 * 维护未读数，让 Board 顶栏铃铛 / Setting 入口 cell / NotificationCenter 三处自动同步。
 * 任意一处对通知做"标记已读 / 删除 / 全部已读"后调用 refresh()。
 *
 * 注意：这里只关心**未读数**，不缓存通知列表本身——列表由 NotificationCenter 拉。
 */
export const useNoticeStore = defineStore('notice', () => {
  const unreadCount = ref(0)
  /** 是否已经至少加载过一次（用于决定是否要在挂载时拉首次） */
  const loaded = ref(false)

  /** 拉一次未读数；静默失败，不打扰 UI */
  async function refresh() {
    try {
      const res = await noticeApi.list({ isRead: false })
      unreadCount.value = (res.data.data ?? []).length
      loaded.value = true
    } catch (err) {
      if (!isHandledError(err)) {
        // 静默：未读徽章失败不打扰用户
        unreadCount.value = 0
      }
    }
  }

  /** 本地操作（标记已读/删除已读项）后乐观地减一，避免一定要等 refresh */
  function decrementUnread(delta = 1) {
    unreadCount.value = Math.max(0, unreadCount.value - delta)
  }

  /** 全部已读：本地直接清零（NotificationCenter 调用 markAllRead 后调） */
  function clearUnread() {
    unreadCount.value = 0
  }

  return {
    unreadCount,
    loaded,
    refresh,
    decrementUnread,
    clearUnread,
  }
})
