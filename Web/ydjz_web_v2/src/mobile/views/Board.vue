<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, onActivated, onDeactivated } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showLoadingToast, closeToast } from 'vant'
import { homeApi, type HomeInfo } from '@shared/api/home'
import { aiApi } from '@shared/api/ai'
import { useNoticeStore } from '@shared/stores/notice'
import logoUrl from '@shared/assets/logo.png'
import ChartOverlay from '@mobile/components/ChartOverlay.vue'

const router = useRouter()
const noticeStore = useNoticeStore()
const unreadCount = computed(() => noticeStore.unreadCount)
const unreadDisplay = computed(() => (unreadCount.value > 99 ? '99+' : String(unreadCount.value)))

function openNotifications() {
  router.push('/notifications')
}

// AI 服务可用状态
const aiServiceAvailable = ref(false)

// 数据
const loading = ref(false)
const homeInfo = ref<HomeInfo | null>(null)
const currentYear = new Date().getFullYear()
const chooseYear = ref(currentYear)
const minYear = 2021
const showYearPicker = ref(false)
const showAccountSheet = ref(false)
const showChartOverlay = ref(false)
const showLegendTip = ref(false)

// 布局模式：list | grid
const layoutMode = ref<'list' | 'grid'>('list')

function toggleLayout() {
  layoutMode.value = layoutMode.value === 'list' ? 'grid' : 'list'
}

// 隐私模式
const privacyMode = ref(false)

function togglePrivacy() {
  privacyMode.value = !privacyMode.value
}

// 隐私金额显示（不同区域不同星号数量）
const PRIVACY_TOTAL = '*******'   // 总资产 7个
const PRIVACY_ACCOUNT = '******'  // 账户明细 6个
const PRIVACY_YEAR = '******'     // 年度收支 6个
const PRIVACY_MONTH = '*****'     // 月度概览 5个

function privacyTotal(amount: string | undefined): string {
  if (privacyMode.value) return PRIVACY_TOTAL
  return amount || '0.00'
}

function privacyAccount(amount: string | undefined): string {
  if (privacyMode.value) return PRIVACY_ACCOUNT
  return amount || '0.00'
}

function privacyYear(amount: string | number | undefined): string {
  if (privacyMode.value) return PRIVACY_YEAR
  return formatAmount(amount)
}

function privacyMonth(amount: string | number | undefined): string {
  if (privacyMode.value) return PRIVACY_MONTH
  return formatMonthAmount(amount)
}

// 滚动状态：是否显示总资产在头部
const showAssetInHeader = ref(false)
const assetCardRef = ref<HTMLElement | null>(null)

// 监听滚动
function handleScroll() {
  if (assetCardRef.value) {
    const rect = assetCardRef.value.getBoundingClientRect()
    showAssetInHeader.value = rect.bottom < 60
  }
}

// 检测 AI 服务
async function checkAiService() {
  const health = await aiApi.checkHealth()
  aiServiceAvailable.value = health !== null
}

onMounted(() => {
  fetchHomeInfo()
  checkAiService()
  noticeStore.refresh()
})

onActivated(() => {
  // 激活时重新计算滚动状态
  handleScroll()
  window.addEventListener('scroll', handleScroll, { passive: true })
  // 从通知中心 / 编辑页返回时同步未读数（用户可能在那边标记/删除了）
  noticeStore.refresh()
})

onDeactivated(() => {
  window.removeEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})

// 年份列表（Popover 用）
const yearActions = computed(() => {
  const years = []
  for (let i = currentYear; i >= minYear; i--) {
    years.push({ text: `${i}年`, value: i })
  }
  return years
})

// 年份选择
function onYearSelect(action: { text: string; value: number }) {
  chooseYear.value = action.value
  showYearPicker.value = false
  fetchHomeInfo()
}

// 账户列表（计算净资产）
const accountList = computed(() => {
  if (!homeInfo.value?.accounts) return []
  return homeInfo.value.accounts.map(acc => {
    // exemptAsset 为 0 或 0.00 时不显示
    const exempt = parseFloat(acc.exemptAsset || '0')
    const hasExempt = exempt !== 0
    return {
      ...acc,
      realAsset: hasExempt
        ? (parseFloat(acc.accountAsset) - exempt).toFixed(2)
        : null
    }
  })
})

// 是否显示净资产（netAsset 与 totalAsset 不相等时显示）
const showNetAsset = computed(() => {
  if (!homeInfo.value) return false
  return homeInfo.value.netAsset !== homeInfo.value.totalAsset
})

// 格式化金额（缩短显示，保留两位小数）
function formatAmount(amount: string | number | undefined): string {
  if (!amount) return '0.00'
  const num = typeof amount === 'string' ? parseFloat(amount) : amount
  if (Math.abs(num) >= 10000) {
    return (num / 10000).toFixed(2) + '万'
  }
  return num.toFixed(2)
}

// 格式化月度金额（只缩万）
function formatMonthAmount(amount: string | number | undefined): string {
  if (!amount) return '0'
  const num = typeof amount === 'string' ? parseFloat(amount) : amount
  const absNum = Math.abs(num)
  if (absNum >= 10000) {
    return (num / 10000).toFixed(2) + '万'
  }
  return num.toFixed(2)
}

// 判断结余是否为负数
function isNegativeBalance(balance: string | number | undefined): boolean {
  if (!balance) return false
  const num = typeof balance === 'string' ? parseFloat(balance) : balance
  return num < 0
}

// 显示完整金额
function showFullAmount(label: string, amount: string | number | undefined) {
  const num = amount ? (typeof amount === 'string' ? parseFloat(amount) : amount) : 0
  showToast({
    message: `${label}: ¥${num.toFixed(2)}`,
    position: 'top',
  })
}

// 计算最值月份
const maxIncomeMonth = computed(() => {
  if (!homeInfo.value?.monthDetails?.length) return null
  let max = homeInfo.value.monthDetails[0]
  for (const item of homeInfo.value.monthDetails) {
    if (parseFloat(item.income) > parseFloat(max.income)) {
      max = item
    }
  }
  return parseFloat(max.income) > 0 ? max.month : null
})

const maxExpenseMonth = computed(() => {
  if (!homeInfo.value?.monthDetails?.length) return null
  let max = homeInfo.value.monthDetails[0]
  for (const item of homeInfo.value.monthDetails) {
    if (parseFloat(item.outcome) > parseFloat(max.outcome)) {
      max = item
    }
  }
  return parseFloat(max.outcome) > 0 ? max.month : null
})

const maxBalanceMonth = computed(() => {
  if (!homeInfo.value?.monthDetails?.length) return null
  let max = homeInfo.value.monthDetails[0]
  for (const item of homeInfo.value.monthDetails) {
    if (parseFloat(item.balance) > parseFloat(max.balance)) {
      max = item
    }
  }
  return parseFloat(max.balance) > 0 ? max.month : null
})

// 判断是否为最值月份
function isMaxIncome(month: string) {
  return month === maxIncomeMonth.value
}

function isMaxExpense(month: string) {
  return month === maxExpenseMonth.value
}

function isMaxBalance(month: string) {
  return month === maxBalanceMonth.value
}

// 获取首页数据
// 失败标识：用于让 van-empty 显示"加载失败"而不是"暂无数据"
const loadFailed = ref(false)

async function fetchHomeInfo() {
  loading.value = true
  loadFailed.value = false
  showLoadingToast({ message: '加载中...', forbidClick: true, duration: 0 })
  try {
    const res = await homeApi.getHomeInfoByYear(chooseYear.value)
    if (res.data.code === 0) {
      homeInfo.value = res.data.data
    }
    // 成功才关 loading toast；失败时让全局 onError 弹的 showFailToast 自然显示
    closeToast()
  } catch (err) {
    console.error('获取首页数据失败:', err)
    // 网络错误：清空数据 + 标记失败，让月度概览显示"加载失败"占位
    homeInfo.value = null
    loadFailed.value = true
  } finally {
    loading.value = false
  }
}

// 年份切换
function onYearPrev() {
  if (chooseYear.value <= minYear) {
    showToast('已经到最前了')
    return
  }
  chooseYear.value--
  fetchHomeInfo()
}

function onYearNext() {
  if (chooseYear.value >= currentYear) {
    showToast('已经到最后了')
    return
  }
  chooseYear.value++
  fetchHomeInfo()
}


// 跳转
function toFlow(month: string) {
  const monthStr = `${chooseYear.value}-${month.toString().padStart(2, '0')}`
  router.push({ path: '/flow', query: { month: monthStr } })
}

function toScreen(accountId: number) {
  showAccountSheet.value = false
  sessionStorage.setItem('screenFrom', 'new')
  router.push({ path: '/screen', query: { acid: accountId } })
}

function toAI() {
  router.push('/ai')
}
</script>

<template>
  <div class="board-page">
    <!-- 固定头部 -->
    <div class="page-header">
      <div class="header-title">
        <template v-if="showAssetInHeader">
          <div class="header-asset-group">
            <span class="header-asset-label">总资产</span>
            <span class="header-asset-value">¥ {{ privacyTotal(homeInfo?.totalAsset) }}</span>
          </div>
        </template>
        <template v-else>
          <img :src="logoUrl" alt="Logo" class="title-logo" />
          <span class="title-text">EasyAccounts</span>
        </template>
      </div>

      <!-- 通知铃铛 -->
      <button
        class="bell-btn"
        type="button"
        title="消息通知"
        @click="openNotifications"
      >
        <svg
          class="bell-icon"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.5"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true"
        >
          <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" />
          <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />
        </svg>
        <span v-if="unreadCount > 0" class="bell-badge">{{ unreadDisplay }}</span>
      </button>
    </div>

    <!-- 页面内容 -->
    <div class="page-body">
      <!-- 资产卡片 -->
      <div class="asset-card" ref="assetCardRef">
        <div class="asset-top">
          <div class="asset-info">
            <div class="asset-label-row">
              <span class="asset-label">总资产</span>
              <div class="privacy-btn" @click="togglePrivacy">
                <van-icon :name="privacyMode ? 'closed-eye' : 'eye-o'" size="18" />
              </div>
            </div>
            <div class="asset-amount">¥ {{ privacyTotal(homeInfo?.totalAsset) }}</div>
            <div class="asset-net" v-if="showNetAsset">净资产 ¥ {{ privacyTotal(homeInfo?.netAsset) }}</div>
          </div>
          <div
            class="asset-action"
            :class="{ disabled: privacyMode }"
            @click="!privacyMode && (showAccountSheet = true)"
          >
            <van-icon name="apps-o" size="20" />
            <span>账户</span>
          </div>
        </div>
      </div>

      <!-- 年度统计卡片 -->
      <div class="year-card">
        <div class="year-header">
          <van-button size="mini" icon="minus" round plain @click="onYearPrev" />
          <van-popover
            v-model:show="showYearPicker"
            :actions="yearActions"
            placement="bottom"
            @select="onYearSelect"
          >
            <template #reference>
              <div class="year-title">
                <span>{{ chooseYear }}年度</span>
                <van-icon :name="showYearPicker ? 'arrow-up' : 'arrow-down'" size="12" />
              </div>
            </template>
          </van-popover>
          <van-button size="mini" icon="plus" round plain @click="onYearNext" />
        </div>
        <div class="year-stats">
          <div class="stat-item" @click="!privacyMode && showFullAmount('收入', homeInfo?.yearIncome)">
            <span class="stat-label">收入</span>
            <span class="stat-value income">{{ privacyYear(homeInfo?.yearIncome) }}</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item" @click="!privacyMode && showFullAmount('支出', homeInfo?.yearOutCome)">
            <span class="stat-label">支出</span>
            <span class="stat-value expense">{{ privacyYear(homeInfo?.yearOutCome) }}</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item" @click="!privacyMode && showFullAmount('结余', homeInfo?.yearBalance)">
            <span class="stat-label">结余</span>
            <span class="stat-value balance">{{ privacyYear(homeInfo?.yearBalance) }}</span>
          </div>
        </div>
      </div>

      <!-- 月度明细卡片 -->
      <div class="month-card">
        <div class="month-card-header">
          <div class="month-header">月度概览</div>
          <div class="header-actions">
            <div class="action-btn" @click="showLegendTip = true">
              <van-icon name="info-o" size="18" />
            </div>
            <div
              class="action-btn"
              :class="{ disabled: privacyMode }"
              @click="!privacyMode && (showChartOverlay = true)"
            >
              <van-icon name="chart-trending-o" size="18" />
            </div>
            <div class="action-btn" @click="toggleLayout">
              <van-icon :name="layoutMode === 'list' ? 'bars' : 'apps-o'" size="18" />
            </div>
          </div>
        </div>

        <!-- List 布局 -->
        <div class="month-list" v-if="homeInfo?.monthDetails?.length && layoutMode === 'list'">
          <div
            class="month-item"
            v-for="item in homeInfo.monthDetails"
            :key="item.month"
            @click="toFlow(item.month)"
          >
            <div class="month-left">
              <div class="month-label">{{ item.month }}月</div>
            </div>
            <div class="month-right">
              <div class="month-stat income">
                <span class="stat-num" :class="{ 'max-tag income': isMaxIncome(item.month) && !privacyMode }">
                  <template v-if="!privacyMode">+</template>{{ privacyMonth(item.income) }}
                </span>
              </div>
              <div class="month-stat expense">
                <span class="stat-num" :class="{ 'max-tag expense': isMaxExpense(item.month) && !privacyMode }">
                  <template v-if="!privacyMode">-</template>{{ privacyMonth(item.outcome) }}
                </span>
              </div>
              <div class="month-stat balance" :class="{ negative: isNegativeBalance(item.balance) && !privacyMode }">
                <span class="stat-num" :class="{ 'max-tag balance': isMaxBalance(item.month) && !privacyMode }">
                  {{ privacyMonth(item.balance) }}
                </span>
              </div>
            </div>
            <van-icon name="arrow" class="month-arrow" />
          </div>
        </div>

        <!-- Grid 布局 -->
        <div class="month-grid" v-else-if="homeInfo?.monthDetails?.length && layoutMode === 'grid'">
          <div
            class="grid-item"
            v-for="item in homeInfo.monthDetails"
            :key="item.month"
            @click="toFlow(item.month)"
          >
            <div class="grid-header">
              <div class="grid-month">{{ item.month }}月</div>
            </div>
            <div class="grid-stats">
              <div class="grid-stat income">
                <span class="grid-label">收入</span>
                <span class="grid-value" :class="{ 'max-tag income': isMaxIncome(item.month) && !privacyMode }">
                  <template v-if="!privacyMode">+</template>{{ privacyMonth(item.income) }}
                </span>
              </div>
              <div class="grid-stat expense">
                <span class="grid-label">支出</span>
                <span class="grid-value" :class="{ 'max-tag expense': isMaxExpense(item.month) && !privacyMode }">
                  <template v-if="!privacyMode">-</template>{{ privacyMonth(item.outcome) }}
                </span>
              </div>
              <div class="grid-stat balance" :class="{ negative: isNegativeBalance(item.balance) && !privacyMode }">
                <span class="grid-label">结余</span>
                <span class="grid-value" :class="{ 'max-tag balance': isMaxBalance(item.month) && !privacyMode }">
                  {{ privacyMonth(item.balance) }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <van-empty
          v-else
          :image="loadFailed ? 'network' : 'default'"
          :description="loadFailed ? '加载失败，请切换年份重试' : '暂无数据'"
        />
      </div>

    </div>

    <!-- 账户详情弹窗 -->
    <van-action-sheet
      v-model:show="showAccountSheet"
      title="账户概览"
      teleport="body"
    >
      <div class="account-list">
        <div
          class="account-item"
          v-for="acc in accountList"
          :key="acc.id"
          @click="toScreen(acc.id)"
        >
          <div class="account-type-tag" :class="acc.accountType === 1 ? 'liability' : 'asset'">
            {{ acc.accountType === 1 ? '负债' : '资产' }}
          </div>
          <div class="account-info">
            <div class="account-name">{{ acc.accountName }}</div>
            <div class="account-note" v-if="acc.note">{{ acc.note }}</div>
          </div>
          <div class="account-amount">
            <div class="account-asset">¥ {{ privacyAccount(acc.accountAsset) }}</div>
            <div class="account-real" v-if="acc.realAsset">净 ¥ {{ privacyAccount(acc.realAsset) }}</div>
          </div>
          <van-icon name="arrow" class="account-arrow" />
        </div>
      </div>
    </van-action-sheet>

    <!-- 全屏图表弹层 -->
    <ChartOverlay
      v-model:show="showChartOverlay"
      :year="chooseYear"
      :month-details="homeInfo?.monthDetails || []"
      :accounts="homeInfo?.accounts || []"
    />

    <!-- 浮动 AI+ 按钮 -->
    <div v-if="aiServiceAvailable" class="fab" @click="toAI">
      <span class="ai-fab-text">AI+</span>
    </div>

    <!-- 图例说明弹窗 -->
    <van-dialog
      v-model:show="showLegendTip"
      title="标记说明"
      confirm-button-text="知道了"
      teleport="body"
    >
      <div class="legend-dialog">
        <div class="legend-item">
          <span class="legend-sample max-tag income">+1,234.56</span>
          <span>收入最高的月份</span>
        </div>
        <div class="legend-item">
          <span class="legend-sample max-tag expense">-1,234.56</span>
          <span>支出最高的月份</span>
        </div>
        <div class="legend-item">
          <span class="legend-sample max-tag balance">1,234.56</span>
          <span>结余最高的月份</span>
        </div>
        <div class="legend-item">
          <span class="legend-sample negative-sample">-500.00</span>
          <span>支出大于收入</span>
        </div>
      </div>
    </van-dialog>
  </div>
</template>

<style scoped>
.board-page {
  min-height: 100vh;
  background: transparent;
}

/* 固定头部 */
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

.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-logo {
  width: 28px;
  height: 28px;
}

.title-text {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.header-asset-group {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.header-asset-label {
  font-size: 11px;
  font-weight: 500;
  color: var(--color-text-tertiary);
  letter-spacing: 0.5px;
}

.header-asset-value {
  font-size: 22px;
  font-weight: 700;
  color: var(--color-text-primary);
  letter-spacing: -0.5px;
}

/* 通知铃铛（顶栏右上角） */
.bell-btn {
  position: relative;
  width: 40px;
  height: 40px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-card);
  border: none;
  border-radius: 12px;
  color: var(--color-text-primary);
  padding: 0;
  cursor: pointer;
}

.bell-btn:active {
  opacity: 0.7;
}

.bell-icon {
  width: 22px;
  height: 22px;
}

.bell-badge {
  position: absolute;
  top: -2px;
  right: -2px;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  background: var(--color-expense);
  color: #fff;
  border-radius: 9px;
  font-size: 11px;
  font-weight: 600;
  line-height: 18px;
  text-align: center;
  font-variant-numeric: tabular-nums;
  box-shadow: 0 0 0 2px var(--color-bg-page);
}

/* 浮动 AI+ 按钮 */
.fab {
  position: fixed;
  right: 20px;
  bottom: 100px;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-transfer);
  color: #fff;
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.4);
  z-index: 50;
}

.fab:active {
  transform: scale(0.95);
}

.ai-fab-text {
  font-size: 16px;
  font-weight: 700;
  letter-spacing: -0.5px;
}

/* 页面内容区 */
.page-body {
  padding: 76px 16px 20px 16px;
}

/* 资产卡片 */
.asset-card {
  background: linear-gradient(135deg, var(--color-transfer) 0%, #5b9cf8 100%);
  border-radius: 20px;
  padding: 24px;
  color: #fff;
  margin-bottom: 16px;
}

.asset-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.asset-info {
  flex: 1;
}

.asset-label-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.asset-label {
  font-size: 14px;
  opacity: 0.9;
}

.privacy-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.85;
  padding: 4px;
}

.privacy-btn:active {
  opacity: 0.6;
}

.asset-amount {
  font-size: 32px;
  font-weight: 700;
  word-break: break-all;
}

.asset-net {
  font-size: 14px;
  opacity: 0.85;
  margin-top: 6px;
}

.asset-action {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  font-size: 12px;
  backdrop-filter: blur(10px);
}

.asset-action:active {
  background: rgba(255, 255, 255, 0.3);
}

.asset-action.disabled {
  opacity: 0.5;
  pointer-events: none;
}

/* 年度卡片 */
.year-card {
  background: var(--color-bg-card);
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 16px;
}

.year-header {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.year-title {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
  padding: 6px 16px;
  background: var(--color-bg-page);
  border-radius: 20px;
}

.year-stats {
  display: flex;
  justify-content: space-around;
  align-items: center;
}

.stat-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  cursor: pointer;
}

.stat-item:active {
  opacity: 0.7;
}

.stat-divider {
  width: 1px;
  height: 40px;
  background: var(--color-border-light);
}

.stat-label {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.stat-value {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.stat-value.income {
  color: var(--color-income);
}

.stat-value.expense {
  color: var(--color-expense);
}

.stat-value.balance {
  color: var(--color-transfer);
}

/* 月度卡片 */
.month-card {
  background: var(--color-bg-card);
  border-radius: 16px;
  padding: 20px;
}

.month-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.month-header {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.header-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  background: var(--color-bg-page);
  color: var(--color-text-secondary);
}

.action-btn:active {
  opacity: 0.7;
}

.action-btn.disabled {
  opacity: 0.35;
  pointer-events: none;
}

.month-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.month-item {
  display: flex;
  align-items: center;
  padding: 12px 12px;
  border-radius: 10px;
  background: var(--color-bg-page);
  transition: opacity 0.2s;
}

.month-item:active {
  opacity: 0.7;
}

.month-left {
  width: 50px;
  flex-shrink: 0;
}

.month-label {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.month-right {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.month-stat {
  flex: 1;
  text-align: center;
}

.stat-num {
  font-size: 13px;
  font-weight: 500;
}

.month-stat.income .stat-num {
  color: var(--color-income);
}

.month-stat.expense .stat-num {
  color: var(--color-expense);
}

.month-stat.balance .stat-num {
  color: var(--color-text-secondary);
}

/* 负数结余红框 */
.month-stat.balance.negative .stat-num {
  border: 1px solid var(--color-expense);
  border-radius: 4px;
  padding: 1px 4px;
}

/* 最高值标签样式 */
.max-tag {
  padding: 2px 6px;
  border-radius: 4px;
  color: #fff !important;
}

.max-tag.income {
  background: var(--color-income);
}

.max-tag.expense {
  background: var(--color-expense);
}

.max-tag.balance {
  background: var(--color-transfer);
}

/* 图例说明弹窗 */
.legend-dialog {
  padding: 16px 24px 8px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
  font-size: 14px;
  color: var(--color-text-primary);
  border-bottom: 1px solid var(--color-border);
}

.legend-item:last-child {
  border-bottom: none;
}

.legend-sample {
  font-size: 12px;
  font-weight: 500;
  flex-shrink: 0;
  min-width: 70px;
  text-align: center;
}

.negative-sample {
  color: var(--color-expense);
  border: 1.5px solid var(--color-expense);
  border-radius: 4px;
  padding: 2px 6px;
}

.month-arrow {
  color: var(--color-text-tertiary);
  margin-left: 8px;
  flex-shrink: 0;
}

/* 账户列表 */
.account-list {
  padding: 8px 16px 24px;
}

.account-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px;
  border-radius: 12px;
  margin-bottom: 8px;
  background: var(--color-bg-page);
}

.account-item:active {
  opacity: 0.8;
}

.account-type-tag {
  font-size: 10px;
  padding: 4px 6px;
  border-radius: 4px;
  font-weight: 500;
  flex-shrink: 0;
}

.account-type-tag.asset {
  background: var(--color-income-bg);
  color: var(--color-income);
}

.account-type-tag.liability {
  background: var(--color-expense-bg);
  color: var(--color-expense);
}

.account-info {
  flex: 1;
  min-width: 0;
}

.account-name {
  font-size: 16px;
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: 4px;
}

.account-note {
  font-size: 13px;
  color: var(--color-text-tertiary);
}

.account-amount {
  text-align: right;
  margin-right: 8px;
}

.account-asset {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.account-real {
  font-size: 12px;
  color: var(--color-text-tertiary);
  margin-top: 2px;
}

.account-arrow {
  color: var(--color-text-tertiary);
}

/* Grid 布局 */
.month-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.grid-item {
  background: var(--color-bg-page);
  border-radius: 12px;
  padding: 14px;
  position: relative;
  transition: opacity 0.2s;
}

.grid-item:active {
  opacity: 0.7;
}

.grid-header {
  margin-bottom: 10px;
}

.grid-month {
  font-size: 18px;
  font-weight: 700;
  color: var(--color-text-primary);
}

.grid-stats {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.grid-stat {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.grid-label {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.grid-value {
  font-size: 13px;
  font-weight: 600;
}

.grid-stat.income .grid-value {
  color: var(--color-income);
}

.grid-stat.expense .grid-value {
  color: var(--color-expense);
}

.grid-stat.balance .grid-value {
  color: var(--color-text-secondary);
}

/* Grid 负数结余红框 */
.grid-stat.balance.negative .grid-value {
  border: 1px solid var(--color-expense);
  border-radius: 4px;
  padding: 1px 4px;
}

</style>

<!-- 暗色模式样式（非 scoped） -->
<style>
.board-page .page-header {
  background: rgba(245, 245, 245, 0.8);
}

html.dark .board-page .page-header {
  background: rgba(10, 10, 10, 0.8);
}
</style>
