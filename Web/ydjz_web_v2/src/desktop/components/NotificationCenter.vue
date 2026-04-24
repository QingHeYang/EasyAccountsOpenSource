<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Check, Delete, AlarmClock, Bell, InfoFilled, Calendar } from '@element-plus/icons-vue'
import { noticeApi, NoticeType, type UserNotice } from '@shared/api/notice'
import { isHandledError } from '@shared/api/request'

defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
  (e: 'changed'): void
  (e: 'navigate', payload: { ruleId: number }): void
}>()

const loading = ref(false)
const notices = ref<UserNotice[]>([])
/** true = 仅看未读；false = 全部 */
const filterUnread = ref(false)

const unreadCount = computed(() => notices.value.filter((n) => !n.read).length)

const filteredNotices = computed(() => {
  if (filterUnread.value) return notices.value.filter((n) => !n.read)
  return notices.value
})

async function loadNotices() {
  loading.value = true
  try {
    const res = await noticeApi.list({})
    notices.value = res.data.data ?? []
  } catch (err) {
    if (!isHandledError(err)) ElMessage.error('加载通知失败')
    notices.value = []
  } finally {
    loading.value = false
  }
}

/** 不同通知类型的主题：颜色、图标、标签、CSS 修饰类
 *  未来扩展（回收站、AI 错误等）在这里追加分支即可，卡片样式会自动按 `typeClass` 切换颜色 */
function getNoticeMeta(type: NoticeType) {
  switch (type) {
    case NoticeType.SCHEDULED_REMINDER:
      return {
        icon: AlarmClock,
        color: '#13C2C2',
        bg: 'rgba(19, 194, 194, 0.12)',
        label: '定时',
        typeClass: 'type-scheduled',
      }
    default:
      return {
        icon: Bell,
        color: 'var(--color-text-secondary)',
        bg: 'var(--color-bg-page)',
        label: '通知',
        typeClass: 'type-default',
      }
  }
}

function formatTime(s: string): string {
  if (!s) return ''
  return s.length > 16 ? s.substring(0, 16) : s
}

/** 相对时间：刚刚 / X 分钟前 / X 小时前 / X 天前 / yyyy-MM-dd */
function formatRelativeTime(s: string): string {
  if (!s) return ''
  const ts = new Date(s.replace(/-/g, '/')).getTime()
  if (Number.isNaN(ts)) return formatTime(s)
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

async function onMarkRead(notice: UserNotice) {
  if (notice.read) return
  try {
    await noticeApi.markRead(notice.id)
    notice.read = true
    emit('changed')
  } catch (err) {
    if (!isHandledError(err)) ElMessage.error('标记失败')
  }
}

async function onMarkAllRead() {
  if (!unreadCount.value) return
  try {
    await noticeApi.markAllRead()
    notices.value.forEach((n) => (n.read = true))
    ElMessage.success('已全部标记为已读')
    emit('changed')
  } catch (err) {
    if (!isHandledError(err)) ElMessage.error('操作失败')
  }
}

async function onDelete(notice: UserNotice) {
  try {
    await ElMessageBox.confirm('确定删除这条通知吗？', '删除通知', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    await noticeApi.delete(notice.id)
    const idx = notices.value.findIndex((n) => n.id === notice.id)
    if (idx >= 0) notices.value.splice(idx, 1)
    emit('changed')
  } catch (err) {
    if (!isHandledError(err)) ElMessage.error('删除失败')
  }
}

/** 点卡片：未读则标记已读 + 如有关联规则，通知父级跳转 */
function onCardClick(notice: UserNotice) {
  if (!notice.read) onMarkRead(notice) // fire-and-forget，不阻塞跳转
  if (notice.relatedRuleId) {
    emit('navigate', { ruleId: notice.relatedRuleId })
  }
}

defineExpose({
  loadNotices,
  unreadCount,
})
</script>

<template>
  <el-drawer
    :model-value="visible"
    direction="rtl"
    size="480px"
    class="notification-drawer"
    @update:model-value="emit('update:visible', $event)"
    @open="loadNotices"
  >
    <template #header>
      <div class="drawer-header">
        <div class="drawer-header-left">
          <span class="drawer-title">消息通知</span>
          <span v-if="unreadCount" class="unread-badge">{{ unreadCount }}</span>
        </div>
        <div class="drawer-header-right">
          <el-button
            v-if="unreadCount"
            size="small"
            :icon="Check"
            @click="onMarkAllRead"
          >
            全部已读
          </el-button>
        </div>
      </div>
    </template>

    <div class="notice-content">
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

      <!-- 通知列表 -->
      <div class="notice-list" v-loading="loading">
        <div
          v-for="notice in filteredNotices"
          :key="notice.id"
          class="notice-card"
          :class="[
            { unread: !notice.read },
            getNoticeMeta(notice.type).typeClass,
          ]"
          @click="onCardClick(notice)"
        >
          <!-- 顶栏：类型 chip · 相对时间 · 删除 -->
          <div class="notice-top">
            <span
              class="notice-type-chip"
              :style="{
                color: getNoticeMeta(notice.type).color,
                background: getNoticeMeta(notice.type).bg,
              }"
            >
              <el-icon :size="12">
                <component :is="getNoticeMeta(notice.type).icon" />
              </el-icon>
              {{ getNoticeMeta(notice.type).label }}
            </span>
            <span class="notice-time">{{ formatRelativeTime(notice.createTime) }}</span>
            <el-button
              :icon="Delete"
              text
              circle
              size="small"
              class="notice-delete-btn"
              title="删除通知"
              @click.stop="onDelete(notice)"
            />
          </div>

          <!-- 主体：title + content -->
          <div class="notice-title">{{ notice.title }}</div>
          <div v-if="notice.content" class="notice-text">{{ notice.content }}</div>

          <!-- 信息 chips（当前只有 relatedRunDate；将来可扩展金额/账户/分类等） -->
          <div v-if="notice.relatedRunDate" class="notice-chips">
            <span class="notice-chip">
              <el-icon :size="11"><Calendar /></el-icon>
              {{ notice.relatedRunDate }}
            </span>
          </div>
        </div>

        <!-- 空状态 -->
        <div v-if="!loading && !filteredNotices.length" class="empty-state">
          <div class="empty-icon">
            <el-icon :size="32"><Bell /></el-icon>
          </div>
          <div class="empty-title">
            {{ filterUnread ? '没有未读通知' : '暂无通知' }}
          </div>
          <div class="empty-desc">
            <template v-if="filterUnread">所有通知都已读</template>
            <template v-else>
              <el-icon :size="12"><InfoFilled /></el-icon>
              定时记账触发提醒时会在这里显示
            </template>
          </div>
        </div>
      </div>
    </div>
  </el-drawer>
</template>

<style scoped>
.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.drawer-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.drawer-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.unread-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  height: 22px;
  padding: 0 8px;
  background: var(--color-expense);
  color: #fff;
  border-radius: 11px;
  font-size: 12px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

/* 过滤条 */
.notice-content {
  padding: 0 0 8px;
}

/* 收紧 drawer header 自身 + 与 body 的间距 */
:deep(.el-drawer__header) {
  padding: 14px 20px;
  margin-bottom: 12px;
  border-bottom: 1px solid var(--color-border-light);
}

.filter-bar {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
}

.filter-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  font-size: 13px;
  color: var(--color-text-secondary);
  background: var(--color-bg-page);
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.15s;
}

.filter-pill:hover {
  color: var(--color-text-primary);
}

.filter-pill.active {
  color: #fff;
  background: var(--color-transfer);
}

.filter-count {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.2);
  font-variant-numeric: tabular-nums;
}

.filter-pill:not(.active) .filter-count {
  background: var(--color-bg-card);
  color: var(--color-text-tertiary);
}

/* 通知列表 */
.notice-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 200px;
}

/* 通知卡片 —— 紧凑分层布局 */
.notice-card {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(8px);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.15s;
}

.notice-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
}

/* 未读：左侧彩色竖条（按类型着色） */
.notice-card.unread {
  border-left-width: 3px;
  padding-left: 10px;
}

.notice-card.type-scheduled.unread {
  border-left-color: #13C2C2;
}

.notice-card.type-default.unread {
  border-left-color: var(--color-transfer);
}

/* Hover 时卡片边框跟着类型色变 */
.notice-card.type-scheduled:hover {
  border-color: rgba(19, 194, 194, 0.5);
}

.notice-card.type-default:hover {
  border-color: var(--color-transfer);
}

/* 顶栏：类型 chip · 时间 · 删除 */
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

.notice-delete-btn {
  flex-shrink: 0;
  color: var(--color-text-tertiary);
  opacity: 0;
  transition: opacity 0.15s;
  height: 22px;
  width: 22px;
  min-height: 22px;
}

.notice-card:hover .notice-delete-btn {
  opacity: 1;
}

.notice-delete-btn:hover {
  color: var(--color-expense);
  background: var(--color-expense-bg);
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
  /* 最多展示 2 行 */
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 数据 chips —— 未来可以按类型往里塞金额/账户/分类等 */
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

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 20px 20px;
  text-align: center;
}

.empty-icon {
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-page);
  border-radius: 50%;
  color: var(--color-text-tertiary);
  margin-bottom: 12px;
}

.empty-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 6px;
}

.empty-desc {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--color-text-tertiary);
  line-height: 1.6;
}

/* 暗色模式 */
html.dark .notice-card {
  background: rgba(40, 40, 40, 0.5);
  border-color: rgba(255, 255, 255, 0.08);
}

html.dark .notice-card:hover {
  background: rgba(50, 50, 50, 0.7);
}

html.dark .notice-chip {
  background: rgba(255, 255, 255, 0.06);
}

html.dark .notice-card.type-scheduled .notice-chip {
  background: rgba(19, 194, 194, 0.16);
}

html.dark .empty-icon {
  background: rgba(255, 255, 255, 0.04);
}
</style>
