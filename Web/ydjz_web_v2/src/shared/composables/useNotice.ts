/**
 * 公告 composable —— 双端通用
 *
 * 职责：
 *  - 拉取公告列表
 *  - 已读状态管理（localStorage 持久化）
 *  - markdown 渲染
 *
 * 卡片本地的"折叠/展开"状态由各端 NoticeCard 子组件自己管，不在这里。
 */
import { ref, computed } from 'vue'
import MarkdownIt from 'markdown-it'
import { homeApi, type Notice } from '@shared/api/home'
import { storage } from '@shared/utils/storage'

const NOTICE_READ_KEY = 'easyaccounts_read_notices'

const md = new MarkdownIt({
  html: false, // 禁止 raw HTML，防 XSS
  linkify: true, // 自动识别 URL 转链接
  breaks: true, // 单换行 → <br>
})

// 链接默认 target="_blank" + rel
const defaultLinkOpen =
  md.renderer.rules.link_open ||
  ((tokens, idx, options, _env, self) => self.renderToken(tokens, idx, options))
md.renderer.rules.link_open = (tokens, idx, options, env, self) => {
  const token = tokens[idx]
  const aIndex = token.attrIndex('target')
  if (aIndex < 0) token.attrPush(['target', '_blank'])
  else token.attrs![aIndex][1] = '_blank'
  const rIndex = token.attrIndex('rel')
  if (rIndex < 0) token.attrPush(['rel', 'noopener noreferrer'])
  else token.attrs![rIndex][1] = 'noopener noreferrer'
  return defaultLinkOpen(tokens, idx, options, env, self)
}

export function useNotice() {
  const notices = ref<Notice[]>([])
  const loading = ref(false)
  const readIds = ref<number[]>(storage.getJSON<number[]>(NOTICE_READ_KEY, []))

  const unreadCount = computed(
    () => notices.value.filter((n) => !readIds.value.includes(n.id)).length
  )

  const hasUnread = computed(() => unreadCount.value > 0)

  function isUnread(notice: Notice): boolean {
    return !readIds.value.includes(notice.id)
  }

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

  function markAllAsRead() {
    if (notices.value.length === 0) return
    const allIds = notices.value.map((n) => n.id)
    readIds.value = allIds
    storage.setJSON(NOTICE_READ_KEY, allIds)
  }

  function renderMarkdown(content: string): string {
    if (!content) return ''
    return md.render(content)
  }

  return {
    notices,
    loading,
    unreadCount,
    hasUnread,
    isUnread,
    loadNotices,
    markAllAsRead,
    renderMarkdown,
  }
}
