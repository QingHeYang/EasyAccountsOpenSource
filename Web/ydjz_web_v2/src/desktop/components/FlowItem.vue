<script setup lang="ts">
import { computed } from 'vue'
import { Delete, Star, StarFilled, Picture } from '@element-plus/icons-vue'
import type { Flow } from '@shared/api/flow'
import alipayIcon from '@shared/assets/icons/alipay.svg'
import wechatIcon from '@shared/assets/icons/wechat.svg'
import housingFundIcon from '@shared/assets/icons/housing-fund.svg'
import cashIcon from '@shared/assets/icons/cash.svg'

const props = withDefaults(defineProps<{
  flow: Flow
  showActions?: boolean
}>(), {
  showActions: true
})

const emit = defineEmits<{
  click: [flow: Flow]
  collect: [flow: Flow]
  delete: [flow: Flow]
}>()

// 收支类型样式
const handleStyle = computed(() => {
  switch (props.flow.handle) {
    case 0: // 流入
      return { color: 'var(--color-income)', sign: '+' }
    case 1: // 流出
      return { color: 'var(--color-expense)', sign: '-' }
    case 2: // 转账
      return { color: 'var(--color-transfer)', sign: '' }
    default:
      return { color: 'var(--color-text-primary)', sign: '' }
  }
})

// 格式化日期
const dateShort = computed(() => {
  if (!props.flow.fdate) return ''
  const parts = props.flow.fdate.split('-')
  if (parts.length >= 3) {
    return `${parseInt(parts[1])}/${parseInt(parts[2])}`
  }
  return props.flow.fdate
})

// 根据账户名获取图标
function getAccountIcon(name: string | undefined): string | null {
  if (!name) return null
  if (name.includes('支付宝')) return alipayIcon
  if (name.includes('微信')) return wechatIcon
  if (name.includes('公积金')) return housingFundIcon
  if (name.includes('现金')) return cashIcon
  return null
}

const accountIcon = computed(() => getAccountIcon(props.flow.aname))
const toAccountIcon = computed(() => getAccountIcon(props.flow.toAName))

function onClick() {
  emit('click', props.flow)
}

function onCollect(e: Event) {
  e.stopPropagation()
  emit('collect', props.flow)
}

function onDelete(e: Event) {
  e.stopPropagation()
  emit('delete', props.flow)
}
</script>

<template>
  <div class="flow-item" @click="onClick">
    <!-- 日期 -->
    <div class="flow-date">{{ dateShort }}</div>

    <!-- 类型 -->
    <div class="flow-type">
      <span class="type-name">{{ flow.tname }}</span>
      <div class="flow-tags">
        <el-tag v-if="flow.hasImages" size="small" type="success">
          <el-icon><Picture /></el-icon>
        </el-tag>
        <el-tag v-if="flow.from === 'ai'" size="small" class="ai-tag">AI</el-tag>
        <el-tag v-if="flow.exempt" size="small" type="info">不计入</el-tag>
      </div>
    </div>

    <!-- 账户 -->
    <div class="flow-account">
      <img v-if="accountIcon" :src="accountIcon" class="account-icon" />
      <span>{{ flow.aname }}</span>
      <template v-if="flow.toAName">
        <span class="transfer-arrow">→</span>
        <img v-if="toAccountIcon" :src="toAccountIcon" class="account-icon" />
        <span>{{ flow.toAName }}</span>
      </template>
    </div>

    <!-- 备注 -->
    <el-tooltip
      :content="flow.note || '-'"
      placement="top"
      :disabled="!flow.note"
      :show-after="300"
    >
      <div class="flow-remark">{{ flow.note || '-' }}</div>
    </el-tooltip>

    <!-- 金额 -->
    <div class="flow-money" :style="{ color: handleStyle.color }">
      {{ handleStyle.sign }}{{ flow.money }}
    </div>

    <!-- 操作 -->
    <div v-if="showActions" class="flow-actions">
      <!-- 已收藏：始终显示 -->
      <el-button
        v-if="flow.collect"
        :icon="StarFilled"
        circle
        size="small"
        type="warning"
        class="collect-btn always-show"
        @click="onCollect"
      />
      <!-- 未收藏：hover 显示 -->
      <el-button
        v-else
        :icon="Star"
        circle
        size="small"
        class="collect-btn hover-show"
        @click="onCollect"
      />
      <el-button
        :icon="Delete"
        circle
        size="small"
        type="danger"
        plain
        class="delete-btn hover-show"
        @click="onDelete"
      />
    </div>
  </div>
</template>

<style scoped>
.flow-item {
  display: grid;
  grid-template-columns: 60px 180px 240px 1fr 120px 80px;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-border);
  cursor: pointer;
  transition: background 0.2s;
}

.flow-item:last-child {
  border-bottom: none;
}

.flow-item:hover {
  background: var(--color-bg-page);
  border-radius: 8px;
}

/* 日期 */
.flow-date {
  font-size: 14px;
  color: var(--color-text-secondary);
}

/* 类型 */
.flow-type {
  display: flex;
  align-items: center;
  gap: 8px;
}

.type-name {
  font-size: 15px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.flow-tags {
  display: flex;
  gap: 4px;
}

.ai-tag {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: #fff;
}

/* 账户 */
.flow-account {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--color-text-tertiary);
}

.account-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

.transfer-arrow {
  color: var(--color-transfer);
  margin: 0 4px;
}

/* 备注 */
.flow-remark {
  font-size: 13px;
  color: var(--color-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 金额 */
.flow-money {
  font-size: 16px;
  font-weight: 600;
  text-align: right;
}

/* 操作 */
.flow-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

/* 已收藏的星星始终显示 */
.flow-actions .always-show {
  opacity: 1;
}

/* hover 才显示的按钮 */
.flow-actions .hover-show {
  opacity: 0;
  transition: opacity 0.2s;
}

.flow-item:hover .flow-actions .hover-show {
  opacity: 1;
}
</style>
