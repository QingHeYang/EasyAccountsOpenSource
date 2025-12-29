<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Flow, FlowHandle } from '@shared/api/flow'
import alipayIcon from '@shared/assets/icons/alipay.svg'
import wechatIcon from '@shared/assets/icons/wechat.svg'
import housingFundIcon from '@shared/assets/icons/housing-fund.svg'
import cashIcon from '@shared/assets/icons/cash.svg'

const props = defineProps<{
  flow: Flow
  /** 是否显示日期 */
  showDate?: boolean
  /** 是否显示备注 */
  showRemark?: boolean
  /** 是否禁用长按操作（收藏/删除） */
  disableActions?: boolean
}>()

const emit = defineEmits<{
  click: [flow: Flow]
  collect: [flow: Flow]
  delete: [flow: Flow]
}>()

// 长按相关
let pressTimer: ReturnType<typeof setTimeout> | null = null
const isPressing = ref(false)
const showActionSheet = ref(false)

function onTouchStart() {
  if (props.disableActions) return
  isPressing.value = false
  pressTimer = setTimeout(() => {
    isPressing.value = true
    showActionSheet.value = true
  }, 500)
}

function onTouchEnd() {
  if (pressTimer) {
    clearTimeout(pressTimer)
    pressTimer = null
  }
}

function onTouchMove() {
  if (pressTimer) {
    clearTimeout(pressTimer)
    pressTimer = null
  }
}

function onActionSelect(action: { name: string }) {
  showActionSheet.value = false
  if (action.name === '收藏' || action.name === '取消收藏') {
    emit('collect', props.flow)
  } else if (action.name === '删除') {
    emit('delete', props.flow)
  }
}

const actions = computed(() => [
  { name: props.flow.collect ? '取消收藏' : '收藏', color: 'var(--color-transfer)' },
  { name: '删除', color: 'var(--color-expense)' },
])

// 收支类型样式
const handleStyle = computed(() => {
  switch (props.flow.handle) {
    case 0: // 流入
      return { color: 'var(--color-income)', bg: 'var(--color-income-bg)', sign: '+' }
    case 1: // 流出
      return { color: 'var(--color-expense)', bg: 'var(--color-expense-bg)', sign: '-' }
    case 2: // 转账
      return { color: 'var(--color-transfer)', bg: 'var(--color-transfer-bg)', sign: '' }
    default:
      return { color: 'var(--color-text-primary)', bg: 'var(--color-bg-page)', sign: '' }
  }
})

// 格式化日期（只显示日）
const dateDay = computed(() => {
  if (!props.flow.fdate) return ''
  const parts = props.flow.fdate.split('-')
  return parts[2] ? parseInt(parts[2]) : ''
})

// 格式化日期（显示月-日）
const dateShort = computed(() => {
  if (!props.flow.fdate) return ''
  const parts = props.flow.fdate.split('-')
  if (parts.length >= 3) {
    return `${parseInt(parts[1])}/${parseInt(parts[2])}`
  }
  return props.flow.fdate
})

function onClick() {
  if (isPressing.value) {
    isPressing.value = false
    return
  }
  emit('click', props.flow)
}

// 根据账户名获取图标
function getAccountIcon(name: string | undefined): string | null {
  if (!name) return null
  if (name.includes('支付宝')) return alipayIcon
  if (name.includes('微信')) return wechatIcon
  if (name.includes('公积金')) return housingFundIcon
  if (name.includes('现金')) return cashIcon
  return null
}

// 账户图标
const accountIcon = computed(() => getAccountIcon(props.flow.aname))
const toAccountIcon = computed(() => getAccountIcon(props.flow.toAName))
</script>

<template>
  <div
    class="flow-item"
    @click="onClick"
    @touchstart="onTouchStart"
    @touchend="onTouchEnd"
    @touchmove="onTouchMove"
    @contextmenu.prevent
  >
    <!-- 左侧日期 -->
    <div class="flow-date" v-if="showDate">
      <span class="date-day">{{ dateDay }}</span>
    </div>

    <!-- 中间内容 -->
    <div class="flow-content">
      <div class="flow-top">
        <span class="flow-type">{{ flow.tname }}</span>
        <div class="flow-tags">
          <span v-if="flow.hasImages" class="tag tag-image">图</span>
          <span v-if="flow.from === 'ai'" class="tag tag-ai">AI</span>
          <span v-if="flow.collect" class="tag tag-star">★</span>
        </div>
      </div>
      <div class="flow-bottom">
        <span class="flow-account">
          <img v-if="accountIcon" :src="accountIcon" class="account-icon" />
          {{ flow.aname }}
        </span>
        <span v-if="flow.toAName" class="flow-transfer">
          →
          <img v-if="toAccountIcon" :src="toAccountIcon" class="account-icon" />
          {{ flow.toAName }}
        </span>
        <span v-if="flow.exempt" class="flow-exempt">不计入</span>
      </div>
      <!-- 备注 -->
      <div class="flow-remark" v-if="showRemark && flow.note">
        {{ flow.note }}
      </div>
    </div>

    <!-- 右侧金额 -->
    <div class="flow-money" :style="{ color: handleStyle.color }">
      {{ handleStyle.sign }}{{ flow.money }}
    </div>
  </div>

  <!-- 长按操作菜单 -->
  <van-action-sheet
    v-model:show="showActionSheet"
    :title="`${flow.tname} ¥${flow.money}`"
    :actions="actions"
    cancel-text="取消"
    close-on-click-action
    @select="onActionSelect"
    teleport="body"
  />
</template>

<style scoped>
.flow-item {
  display: flex;
  align-items: center;
  padding: 14px 16px;
  background: var(--color-bg-card);
  border-radius: 12px;
  gap: 12px;
}

.flow-item:active {
  opacity: 0.8;
}

/* 日期 */
.flow-date {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-page);
  border-radius: 10px;
  flex-shrink: 0;
}

.date-day {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

/* 内容 */
.flow-content {
  flex: 1;
  min-width: 0;
}

.flow-top {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}

.flow-type {
  font-size: 15px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.flow-tags {
  display: flex;
  gap: 4px;
}

.tag {
  font-size: 10px;
  padding: 2px 5px;
  border-radius: 4px;
  font-weight: 500;
}

.tag-image {
  background: var(--color-income-bg);
  color: var(--color-income);
}

.tag-ai {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

.tag-star {
  background: var(--color-note);
  color: #fff;
}

.flow-bottom {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.flow-account,
.flow-transfer {
  display: inline-flex;
  align-items: center;
}

.flow-transfer {
  color: var(--color-transfer);
}

.account-icon {
  width: 16px;
  height: 16px;
  margin-right: 2px;
  flex-shrink: 0;
}

.flow-exempt {
  padding: 1px 4px;
  border-radius: 3px;
  background: var(--color-bg-page);
  font-size: 10px;
}

/* 备注 */
.flow-remark {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-top: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.4;
}

/* 金额 */
.flow-money {
  font-size: 17px;
  font-weight: 600;
  flex-shrink: 0;
}
</style>
