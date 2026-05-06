<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showConfirmDialog } from 'vant'
import { useSmartBack } from '@shared/composables/useSmartBack'
import { useNoticeStore } from '@shared/stores/notice'
import { noticeApi, NoticeType, type UserNotice } from '@shared/api/notice'
import { isHandledError } from '@shared/api/request'

const router = useRouter()
const { smartBack } = useSmartBack()
const noticeStore = useNoticeStore()

const loading = ref(false)
const notices = ref<UserNotice[]>([])
/** true = 仅看未读；false = 全部 */
const filterUnread = ref(false)
/** "说明"弹层 */
const showInfoPopup = ref(false)

const unreadCount = computed(() => notices.value.filter((n) => !n.read).length)

const filteredNotices = computed(() => {
  if (filterUnread.value) return notices.value.filter((n) => !n.read)
  return notices.value
})

/** 类型主题：颜色 / 图标 / 标签 / CSS 修饰类
 *
 * 通知分两大类：
 *  - 定时记账提醒（type=1）：可点击跳转到规则编辑
 *  - 自动月度 Excel（type=2-5）：聚合一类，仅展示不响应点击
 *    └─ 内部用 icon / 颜色区分细分状态（提醒 / 已生成 / 已跳过 / 失败）
 */
function getNoticeMeta(type: NoticeType) {
  switch (type) {
    case NoticeType.SCHEDULED_REMINDER:
      return {
        icon: 'clock-o',
        color: '#13C2C2',
        bg: 'rgba(19, 194, 194, 0.12)',
        label: '定时',
        typeClass: 'type-scheduled',
      }
    case NoticeType.AUTO_EXCEL_REMIND:
      return {
        icon: 'calendar-o',
        color: 'var(--color-transfer)',
        bg: 'rgba(24, 144, 255, 0.12)',
        label: 'Excel 提醒',
        typeClass: 'type-excel-remind',
      }
    case NoticeType.AUTO_EXCEL_GENERATED:
      return {
        icon: 'passed',
        color: 'var(--color-income)',
        bg: 'rgba(82, 196, 26, 0.12)',
        label: 'Excel 已生成',
        typeClass: 'type-excel-done',
      }
    case NoticeType.AUTO_EXCEL_SKIPPED:
      return {
        icon: 'underway-o',
        color: 'var(--color-text-tertiary)',
        bg: 'var(--color-bg-page)',
        label: 'Excel 已跳过',
        typeClass: 'type-excel-skip',
      }
    case NoticeType.AUTO_EXCEL_FAILED:
      return {
        icon: 'warning-o',
        color: 'var(--color-expense)',
        bg: 'rgba(245, 34, 45, 0.12)',
        label: 'Excel 失败',
        typeClass: 'type-excel-fail',
      }
    default:
      return {
        icon: 'volume-o',
        color: 'var(--color-text-secondary)',
        bg: 'var(--color-bg-page)',
        label: '通知',
        typeClass: 'type-default',
      }
  }
}

/** 仅定时记账提醒（type=1）可点击跳转 */
function isClickable(notice: UserNotice): boolean {
  return notice.type === NoticeType.SCHEDULED_REMINDER && !!notice.relatedRuleId
}

/** 相对时间：刚刚 / X 分钟前 / X 小时前 / X 天前 / yyyy-MM-dd */
function formatRelativeTime(s: string): string {
  if (!s) return ''
  const ts = new Date(s.replace(/-/g, '/')).getTime()
  if (Number.isNaN(ts)) return s.length > 16 ? s.substring(0, 16) : s
  const diff = Date.now() - ts
  const m = Math.floor(diff / 60000)
  if (m < 1) return '刚刚'
  if (m < 60) return `${m} 分钟前`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h} 小时前`
  const d = Math.floor(h / 24)
  if (d < 7) return `${d} 天前`
  return s.length > 10 ? s.substring(0, 10) : s
}

/* -------- 数据 -------- */

async function loadNotices() {
  loading.value = true
  try {
    const res = await noticeApi.list({})
    notices.value = res.data.data ?? []
    // 拉完后同步未读数到 store（页面是最新数据来源）
    noticeStore.unreadCount = unreadCount.value
    noticeStore.loaded = true
  } catch (err) {
    if (!isHandledError(err)) showToast('加载通知失败')
    notices.value = []
  } finally {
    loading.value = false
  }
}

/* -------- 事件 -------- */

function onBack() {
  smartBack('/board')
}

async function onMarkRead(notice: UserNotice) {
  if (notice.read) return
  try {
    await noticeApi.markRead(notice.id)
    notice.read = true
    noticeStore.decrementUnread(1)
  } catch (err) {
    if (!isHandledError(err)) showToast('标记失败')
  }
}

async function onMarkAllRead() {
  if (!unreadCount.value) return
  try {
    await showConfirmDialog({
      title: '全部已读',
      message: `确定将 ${unreadCount.value} 条未读通知全部标记为已读吗？`,
      confirmButtonText: '确定',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }
  try {
    await noticeApi.markAllRead()
    notices.value.forEach((n) => (n.read = true))
    noticeStore.clearUnread()
    showToast('已全部标记为已读')
  } catch (err) {
    if (!isHandledError(err)) showToast('操作失败')
  }
}

async function onDelete(notice: UserNotice) {
  try {
    await showConfirmDialog({
      title: '删除通知',
      message: '确定删除这条通知吗？',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }
  try {
    await noticeApi.delete(notice.id)
    const wasUnread = !notice.read
    const idx = notices.value.findIndex((n) => n.id === notice.id)
    if (idx >= 0) notices.value.splice(idx, 1)
    if (wasUnread) noticeStore.decrementUnread(1)
  } catch (err) {
    if (!isHandledError(err)) showToast('删除失败')
  }
}

/** 点卡片：未读则标记已读；仅定时记账类（type=1）才触发跳转，
 *  自动 Excel 类（type=2-5）只标已读，不响应跳转 */
function onCardClick(notice: UserNotice) {
  if (!notice.read) onMarkRead(notice) // fire-and-forget
  if (isClickable(notice)) {
    router.push(`/setting/scheduled-flow/edit/${notice.relatedRuleId}`)
  }
}

onMounted(() => {
  window.scrollTo(0, 0)
  loadNotices()
})
</script>

<template>
  <div class="notification-center-page">
    <!-- 顶部导航 -->
    <div class="page-header">
      <div class="header-left" @click="onBack">
        <van-icon name="arrow-left" size="20" />
      </div>
      <div class="header-title">
        <span>消息通知</span>
        <span v-if="unreadCount" class="header-unread-badge">{{ unreadCount }}</span>
      </div>
      <!-- 右侧 group：说明（常驻） + 全部已读（条件） -->
      <div class="header-right-group">
        <div
          v-if="unreadCount"
          class="header-icon-btn header-icon-btn-action"
          title="全部已读"
          @click="onMarkAllRead"
        >
          <van-icon name="completed" size="20" />
        </div>
        <div
          class="header-icon-btn"
          title="通知说明"
          @click="showInfoPopup = true"
        >
          <van-icon name="question-o" size="20" />
        </div>
      </div>
    </div>

    <div class="page-body">
      <!-- 过滤条 -->
      <div class="filter-bar">
        <div
          class="filter-pill"
          :class="{ active: !filterUnread }"
          @click="filterUnread = false"
        >
          全部
          <span class="filter-count">{{ notices.length }}</span>
        </div>
        <div
          class="filter-pill"
          :class="{ active: filterUnread }"
          @click="filterUnread = true"
        >
          未读
          <span class="filter-count">{{ unreadCount }}</span>
        </div>
      </div>

      <!-- 通知卡片列表 -->
      <template v-if="filteredNotices.length">
        <div
          v-for="notice in filteredNotices"
          :key="notice.id"
          class="notice-card"
          :class="[
            { unread: !notice.read, 'not-clickable': !isClickable(notice) },
            getNoticeMeta(notice.type).typeClass,
          ]"
          @click="onCardClick(notice)"
        >
          <!-- 顶行：类型 chip · 相对时间 · 删除 -->
          <div class="notice-top">
            <span
              class="notice-type-chip"
              :style="{
                color: getNoticeMeta(notice.type).color,
                background: getNoticeMeta(notice.type).bg,
              }"
            >
              <van-icon :name="getNoticeMeta(notice.type).icon" size="11" />
              {{ getNoticeMeta(notice.type).label }}
            </span>
            <span class="notice-time">{{ formatRelativeTime(notice.createTime) }}</span>
            <van-icon
              name="cross"
              size="16"
              class="notice-delete"
              @click.stop="onDelete(notice)"
            />
          </div>

          <!-- 主体 -->
          <div class="notice-title">{{ notice.title }}</div>
          <div v-if="notice.content" class="notice-text">{{ notice.content }}</div>

          <!-- 信息 chips（当前只有 relatedRunDate；后续可扩展金额/账户/分类） -->
          <div v-if="notice.relatedRunDate" class="notice-chips">
            <span class="notice-chip">
              <van-icon name="calendar-o" size="11" />
              {{ notice.relatedRunDate }}
            </span>
          </div>
        </div>
      </template>

      <!-- 空状态 -->
      <div v-else-if="!loading" class="empty-state">
        <div class="empty-icon">
          <van-icon name="volume-o" size="40" />
        </div>
        <div class="empty-title">
          {{ filterUnread ? '没有未读通知' : '暂无通知' }}
        </div>
        <div class="empty-desc">
          <template v-if="filterUnread">所有通知都已读</template>
          <template v-else>定时记账触发提醒时会在这里显示</template>
        </div>
      </div>

      <!-- 加载占位 -->
      <van-skeleton
        v-if="loading && !notices.length"
        title
        :row="3"
        class="loading-skeleton"
      />
    </div>

    <!-- 说明弹层 -->
    <van-popup
      v-model:show="showInfoPopup"
      round
      position="bottom"
      teleport="body"
      closeable
      close-icon-position="top-right"
      :style="{ maxHeight: '80vh' }"
    >
      <div class="info-popup">
        <div class="info-header">
          <van-icon name="question-o" size="22" class="info-header-icon" />
          <div class="info-title">什么时候清提醒</div>
        </div>

        <div class="info-section">
          <div class="info-section-head">
            <span class="info-section-no">1</span>
            <span class="info-section-title">记账成功</span>
          </div>
          <div class="info-section-text">那一天的提醒自动消失。</div>
        </div>

        <div class="info-section">
          <div class="info-section-head">
            <span class="info-section-no">2</span>
            <span class="info-section-title">修改规则</span>
          </div>
          <div class="info-section-text">旧提醒清空，按新计划重新生成。</div>
        </div>

        <div class="info-section">
          <div class="info-section-head">
            <span class="info-section-no">3</span>
            <span class="info-section-title">删除 / 暂停规则</span>
          </div>
          <div class="info-section-text">剩余提醒一起清空。</div>
        </div>
      </div>
    </van-popup>
  </div>
</template>

<style scoped>
.notification-center-page {
  min-height: 100vh;
  background: var(--color-bg-page);
}

/* 顶部导航 */
.page-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 50;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.header-left,
.header-icon-btn {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: var(--color-bg-card);
  color: var(--color-text-primary);
}

.header-left:active,
.header-icon-btn:active {
  opacity: 0.7;
}

.header-right-group {
  display: flex;
  gap: 8px;
}

.header-icon-btn-action {
  color: var(--color-transfer);
}

.header-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.header-unread-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  background: var(--color-expense);
  color: #fff;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.page-body {
  padding: 76px 16px 32px;
}

/* 过滤条 */
.filter-bar {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.filter-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  font-size: 13px;
  color: var(--color-text-secondary);
  background: var(--color-bg-card);
  border-radius: 16px;
  transition: opacity 0.15s;
}

.filter-pill:active {
  opacity: 0.75;
}

.filter-pill.active {
  color: #fff;
  background: var(--color-transfer);
  font-weight: 500;
}

.filter-count {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.06);
  font-variant-numeric: tabular-nums;
}

.filter-pill.active .filter-count {
  background: rgba(255, 255, 255, 0.2);
}

/* 通知卡 */
.notice-card {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px 14px;
  margin-bottom: 8px;
  background: var(--color-bg-card);
  border: 1px solid transparent;
  border-radius: 12px;
  transition: opacity 0.15s;
}

.notice-card:active {
  opacity: 0.85;
}

/* 未读：左侧彩色竖条（按类型着色） */
.notice-card.unread {
  border-left-width: 3px;
  padding-left: 11px;
}

.notice-card.type-scheduled.unread {
  border-left-color: #13C2C2;
}

.notice-card.type-excel-remind.unread {
  border-left-color: var(--color-transfer);
}

.notice-card.type-excel-done.unread {
  border-left-color: var(--color-income);
}

.notice-card.type-excel-skip.unread {
  border-left-color: var(--color-text-tertiary);
}

.notice-card.type-excel-fail.unread {
  border-left-color: var(--color-expense);
}

.notice-card.type-default.unread {
  border-left-color: var(--color-transfer);
}

/* 不可点击：取消 active 反馈 */
.notice-card.not-clickable:active {
  opacity: 1;
}

/* 顶行 */
.notice-top {
  display: flex;
  align-items: center;
  gap: 8px;
}

.notice-type-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  font-size: 11px;
  font-weight: 600;
  border-radius: 5px;
  line-height: 1.4;
}

.notice-time {
  flex: 1;
  font-size: 11px;
  color: var(--color-text-tertiary);
  font-variant-numeric: tabular-nums;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.notice-delete {
  flex-shrink: 0;
  color: var(--color-text-tertiary);
  padding: 4px;
}

.notice-delete:active {
  color: var(--color-expense);
}

/* 标题 & 内容 */
.notice-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
  line-height: 1.4;
  word-break: break-word;
}

.notice-text {
  font-size: 12.5px;
  color: var(--color-text-secondary);
  line-height: 1.5;
  word-break: break-word;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 信息 chips */
.notice-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 2px;
}

.notice-chip {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 2px 8px;
  font-size: 11px;
  color: var(--color-text-secondary);
  background: var(--color-bg-page);
  border-radius: 5px;
  font-variant-numeric: tabular-nums;
}

.notice-card.type-scheduled .notice-chip {
  color: #13C2C2;
  background: rgba(19, 194, 194, 0.08);
}

.notice-card.type-excel-remind .notice-chip {
  color: var(--color-transfer);
  background: rgba(24, 144, 255, 0.08);
}

.notice-card.type-excel-done .notice-chip {
  color: var(--color-income);
  background: rgba(82, 196, 26, 0.08);
}

.notice-card.type-excel-fail .notice-chip {
  color: var(--color-expense);
  background: rgba(245, 34, 45, 0.08);
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px 20px 20px;
  text-align: center;
}

.empty-icon {
  width: 72px;
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-card);
  border-radius: 50%;
  color: var(--color-text-tertiary);
  margin-bottom: 16px;
}

.empty-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 6px;
}

.empty-desc {
  font-size: 13px;
  color: var(--color-text-tertiary);
  line-height: 1.5;
}

/* 加载占位 */
.loading-skeleton {
  padding: 14px;
  background: var(--color-bg-card);
  border-radius: 12px;
}

/* "说明"弹层 */
.info-popup {
  padding: 22px 20px 28px;
  background: var(--color-bg-card);
  max-width: 100%;
}

.info-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 18px;
  padding-bottom: 14px;
  border-bottom: 1px dashed var(--color-border);
}

.info-header-icon {
  color: #13C2C2;
  flex-shrink: 0;
}

.info-title {
  font-size: 17px;
  font-weight: 600;
  color: var(--color-text-primary);
  line-height: 1.3;
}

.info-section + .info-section {
  margin-top: 14px;
}

.info-section-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.info-section-no {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #13C2C2;
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  flex-shrink: 0;
}

.info-section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
  line-height: 1.4;
}

.info-section-text {
  font-size: 13px;
  line-height: 1.65;
  color: var(--color-text-secondary);
  word-break: break-word;
  padding-left: 28px;
}

/* 暗色模式 */
html.dark .notice-card {
  background: rgba(40, 40, 40, 0.5);
}

html.dark .notice-chip {
  background: rgba(255, 255, 255, 0.06);
}

html.dark .notice-card.type-scheduled .notice-chip {
  background: rgba(19, 194, 194, 0.16);
}

html.dark .filter-count {
  background: rgba(255, 255, 255, 0.08);
}
</style>

<style>
.notification-center-page .page-header {
  background: rgba(245, 245, 245, 0.8);
}

html.dark .notification-center-page .page-header {
  background: rgba(10, 10, 10, 0.8);
}
</style>
