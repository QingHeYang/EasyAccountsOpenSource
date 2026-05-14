<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'
import { Link, ArrowDown, ArrowUp } from '@element-plus/icons-vue'
import type { Notice } from '@shared/api/home'

const props = defineProps<{
  notice: Notice
  unread: boolean
  contentHtml: string
}>()

const COLLAPSED_MAX_HEIGHT = 72 // px，约 3 行 × 24px line-height

const contentEl = ref<HTMLDivElement | null>(null)
const expandable = ref(false)
const expanded = ref(false)

function measure() {
  if (!contentEl.value) return
  // scrollHeight 是元素完整内容高度（含被 max-height 截断部分）
  expandable.value = contentEl.value.scrollHeight > COLLAPSED_MAX_HEIGHT + 4
}

function toggle() {
  expanded.value = !expanded.value
}

onMounted(() => {
  nextTick(measure)
})

// 内容变化时重新测高度
watch(() => props.contentHtml, () => {
  expanded.value = false
  nextTick(measure)
})

function openLink(url: string) {
  if (url) window.open(url, '_blank', 'noopener,noreferrer')
}
</script>

<template>
  <div class="notice-card" :class="{ 'is-unread': unread }">
    <div class="notice-card__head">
      <div class="notice-title-wrap">
        <span v-if="unread" class="unread-dot"></span>
        <span class="notice-title">{{ notice.title }}</span>
      </div>
      <span class="notice-date">{{ notice.date }}</span>
    </div>

    <div
      ref="contentEl"
      class="notice-card__content markdown-body"
      :class="{ 'is-collapsed': expandable && !expanded }"
      v-html="contentHtml"
    ></div>

    <div v-if="expandable || notice.url" class="notice-card__footer">
      <div v-if="expandable" class="notice-chip" @click="toggle">
        <el-icon :size="12">
          <ArrowUp v-if="expanded" />
          <ArrowDown v-else />
        </el-icon>
        <span>{{ expanded ? '收起' : '展开' }}</span>
      </div>
      <div v-if="notice.url" class="notice-chip" @click="openLink(notice.url)">
        <el-icon :size="12"><Link /></el-icon>
        <span>查看详情</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.notice-card {
  position: relative;
  padding: 14px 16px;
  background: var(--color-bg-page);
  border-radius: 12px;
  transition: background 0.2s, box-shadow 0.2s;
  overflow: hidden;
}

.notice-card:hover {
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

/* 未读：左侧 3px 主题色竖条 */
.notice-card.is-unread::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: var(--color-transfer);
}

.notice-card__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}

.notice-title-wrap {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  min-width: 0;
  flex: 1;
}

.unread-dot {
  flex-shrink: 0;
  width: 6px;
  height: 6px;
  margin-top: 8px;
  border-radius: 50%;
  background: var(--color-transfer);
}

.notice-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
  line-height: 1.4;
  /* 最多两行，第二行末尾省略 */
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
  word-break: break-word;
}

.notice-date {
  flex-shrink: 0;
  font-size: 12px;
  color: var(--color-text-tertiary);
  font-variant-numeric: tabular-nums;
  /* 跟 title 第一行 baseline 对齐：title line-height 1.4 × 16px ≈ 22.4px */
  line-height: 22px;
}

/* 折叠态 max-height 对应 ~3 行 */
.notice-card__content {
  font-size: 13.5px;
  line-height: 1.7;
  color: var(--color-text-secondary);
  transition: max-height 0.3s ease;
}

.notice-card__content.is-collapsed {
  max-height: 72px;
  overflow: hidden;
  /* 底部渐隐遮罩，避免硬截 */
  -webkit-mask-image: linear-gradient(to bottom, #000 60%, transparent);
  mask-image: linear-gradient(to bottom, #000 60%, transparent);
}

/* 底部 chip 行（"展开" + "查看详情" 同行展示） */
.notice-card__footer {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

.notice-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background: rgba(24, 144, 255, 0.08);
  color: var(--color-transfer);
  border-radius: 12px;
  font-size: 12px;
  line-height: 1.5;
  cursor: pointer;
  user-select: none;
  transition: background 0.2s;
}

.notice-chip:hover {
  background: rgba(24, 144, 255, 0.15);
}

/* === markdown body 内排版 === */
.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3),
.markdown-body :deep(h4) {
  font-size: 14px;
  font-weight: 600;
  margin: 8px 0 4px 0;
  color: var(--color-text-primary);
}

.markdown-body :deep(p) {
  margin: 0 0 6px 0;
}

.markdown-body :deep(p:last-child) {
  margin-bottom: 0;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  margin: 4px 0;
  padding-left: 20px;
}

.markdown-body :deep(li) {
  margin: 2px 0;
}

.markdown-body :deep(a) {
  color: var(--color-transfer);
  text-decoration: none;
}

.markdown-body :deep(a:hover) {
  text-decoration: underline;
}

.markdown-body :deep(code) {
  padding: 1px 6px;
  background: rgba(0, 0, 0, 0.06);
  border-radius: 4px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 12.5px;
}

.markdown-body :deep(pre) {
  margin: 6px 0;
  padding: 10px 12px;
  background: rgba(0, 0, 0, 0.04);
  border-radius: 8px;
  overflow-x: auto;
}

.markdown-body :deep(pre code) {
  padding: 0;
  background: transparent;
}

.markdown-body :deep(blockquote) {
  margin: 6px 0;
  padding: 4px 12px;
  border-left: 3px solid var(--color-border);
  color: var(--color-text-tertiary);
}

.markdown-body :deep(strong) {
  color: var(--color-text-primary);
  font-weight: 600;
}

.markdown-body :deep(hr) {
  margin: 10px 0;
  border: none;
  border-top: 1px solid var(--color-border);
}

.markdown-body :deep(img) {
  max-width: 100%;
  border-radius: 6px;
}
</style>

<style>
/* 暗黑模式（非 scoped 才能覆盖 :deep 渲染产物） */
html.dark .notice-card {
  background: rgba(255, 255, 255, 0.03);
}

html.dark .notice-card:hover {
  background: rgba(255, 255, 255, 0.05);
}

html.dark .notice-card .markdown-body :deep(code) {
  background: rgba(255, 255, 255, 0.08);
}

html.dark .notice-card .markdown-body :deep(pre) {
  background: rgba(255, 255, 255, 0.05);
}

html.dark .notice-card .markdown-body :deep(blockquote) {
  border-left-color: rgba(255, 255, 255, 0.15);
}

html.dark .notice-card .notice-chip {
  background: rgba(116, 192, 252, 0.12);
  color: #74C0FC;
}

html.dark .notice-card .notice-chip:hover {
  background: rgba(116, 192, 252, 0.2);
}
</style>
