<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showConfirmDialog, showToast } from 'vant'
import { accountApi, AccountType, type Account } from '@shared/api/account'
import { useSmartBack } from '@shared/composables/useSmartBack'
import alipayIcon from '@shared/assets/icons/alipay.svg'
import wechatIcon from '@shared/assets/icons/wechat.svg'
import housingFundIcon from '@shared/assets/icons/housing-fund.svg'
import cashIcon from '@shared/assets/icons/cash.svg'

const router = useRouter()
const { smartBack } = useSmartBack()

// 数据
const loading = ref(false)
const accounts = ref<Account[]>([])

// 当前选中的账户
const showSheet = ref(false)
const currentAccount = ref<Account | null>(null)

// 加载数据
async function fetchAccounts() {
  loading.value = true
  try {
    const res = await accountApi.getAll()
    accounts.value = res.data.data
  } catch (err) {
    console.error('获取账户列表失败', err)
  } finally {
    loading.value = false
  }
}

function onBack() {
  smartBack('/setting')
}

function onAdd() {
  router.push('/setting/account/add')
}

function onItemClick(account: Account) {
  currentAccount.value = account
  showSheet.value = true
}

function onEdit() {
  if (currentAccount.value) {
    showSheet.value = false
    router.push(`/setting/account/edit/${currentAccount.value.id}`)
  }
}

async function onDelete() {
  if (!currentAccount.value) return

  showSheet.value = false

  try {
    await showConfirmDialog({
      title: '停用账户',
      message: '确定停用该账户吗？\n\n请先将账户余额设置为 0，否则此账户金额将无法继续记账！\n\n停用后关于此账户的历史数据不会删除。',
      confirmButtonText: '确定停用',
      confirmButtonColor: 'var(--color-expense)',
    })

    await accountApi.delete(currentAccount.value.id)
    showToast('已停用')
    fetchAccounts()
  } catch {
    // 取消或失败
  }
}

// 格式化金额显示
function formatMoney(money: string | undefined) {
  if (!money || money === '0' || money === '0.00') return '¥0.00'
  return `¥${money}`
}

// 格式化显示值
function formatValue(value: string | undefined | null, placeholder: string) {
  if (!value || value === '' || value === '￥') return placeholder
  return value
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

onMounted(() => {
  fetchAccounts()
})
</script>

<template>
  <div class="account-page">
    <!-- 顶部导航 -->
    <div class="page-header">
      <div class="header-left" @click="onBack">
        <van-icon name="arrow-left" size="20" />
      </div>
      <div class="header-title">账户管理</div>
      <div class="header-right" @click="onAdd">
        <van-icon name="plus" size="20" />
      </div>
    </div>

    <!-- 列表 -->
    <div class="page-body">
      <div class="account-list">
        <div
          v-for="account in accounts"
          :key="account.id"
          class="account-item"
          @click="onItemClick(account)"
        >
          <div class="account-icon" :class="{ 'has-svg': getAccountIcon(account.name) }">
            <img v-if="getAccountIcon(account.name)" :src="getAccountIcon(account.name)!" class="account-svg" />
            <van-icon v-else name="card" size="24" />
          </div>
          <div class="account-info">
            <div class="account-name-row">
              <span class="account-name">{{ account.name }}</span>
              <span
                class="account-type-badge"
                :class="account.accountType === AccountType.LIABILITY ? 'liability' : 'asset'"
              >
                {{ account.accountType === AccountType.LIABILITY ? '负债' : '资产' }}
              </span>
            </div>
            <div class="account-card" v-if="account.card">{{ account.card }}</div>
          </div>
          <div class="account-money-info">
            <div class="account-money">{{ formatMoney(account.money) }}</div>
            <div v-if="account.exemptMoney && parseFloat(account.exemptMoney) !== 0" class="account-exempt">
              不计入 {{ formatMoney(account.exemptMoney) }}
            </div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <van-empty v-if="!loading && accounts.length === 0" description="暂无账户" />
    </div>

    <!-- 账户详情弹窗 -->
    <van-action-sheet v-model:show="showSheet" teleport="body">
      <div class="sheet-content">
        <!-- 头部：账户名称和类型 -->
        <div class="sheet-header">
          <span class="sheet-title">{{ currentAccount?.name }}</span>
          <span
            class="sheet-type-badge"
            :class="currentAccount?.accountType === AccountType.LIABILITY ? 'liability' : 'asset'"
          >
            {{ currentAccount?.accountType === AccountType.LIABILITY ? '负债账户' : '资产账户' }}
          </span>
        </div>

        <!-- 余额卡片 -->
        <div class="balance-card" :class="currentAccount?.accountType === AccountType.LIABILITY ? 'liability' : 'asset'">
          <div class="balance-label">账户余额</div>
          <div class="balance-value">{{ formatMoney(currentAccount?.money) }}</div>
          <div v-if="currentAccount?.exemptMoney && parseFloat(currentAccount.exemptMoney) !== 0" class="balance-exempt">
            不计入金额：{{ formatMoney(currentAccount?.exemptMoney) }}
          </div>
        </div>

        <!-- 详情信息 -->
        <div class="detail-list">
          <div class="detail-item">
            <span class="detail-label">卡号/账号</span>
            <span class="detail-value">{{ formatValue(currentAccount?.card, '未设置') }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">备注</span>
            <span class="detail-value">{{ formatValue(currentAccount?.note, '暂无备注') }}</span>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="sheet-actions">
          <button class="action-btn edit" @click="onEdit">
            <van-icon name="edit" />
            编辑账户
          </button>
          <button class="action-btn delete" @click="onDelete">
            <van-icon name="close" />
            停用账户
          </button>
        </div>
      </div>
    </van-action-sheet>
  </div>
</template>

<style scoped>
.account-page {
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
.header-right {
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
.header-right:active {
  opacity: 0.7;
}

.header-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.page-body {
  padding: 76px 16px 24px;
}

/* 列表 */
.account-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.account-item {
  display: flex;
  align-items: center;
  padding: 16px;
  background: var(--color-bg-card);
  border-radius: 16px;
  gap: 14px;
}

.account-item:active {
  opacity: 0.8;
}

.account-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-transfer-bg);
  color: var(--color-transfer);
  border-radius: 14px;
}

.account-icon.has-svg {
  background: transparent;
}

.account-svg {
  width: 40px;
  height: 40px;
}

.account-info {
  flex: 1;
  min-width: 0;
}

.account-name-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.account-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.account-type-badge {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 500;
}

.account-type-badge.asset {
  background: var(--color-income-bg);
  color: var(--color-income);
}

.account-type-badge.liability {
  background: var(--color-expense-bg);
  color: var(--color-expense);
}

.account-card {
  font-size: 13px;
  color: var(--color-text-tertiary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.account-money-info {
  text-align: right;
}

.account-money {
  font-size: 17px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.account-exempt {
  font-size: 12px;
  color: var(--color-text-tertiary);
  margin-top: 2px;
}

/* 弹窗内容 */
.sheet-content {
  padding: 20px;
}

/* 弹窗头部 */
.sheet-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.sheet-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.sheet-type-badge {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 6px;
  font-weight: 500;
}

.sheet-type-badge.asset {
  background: var(--color-income-bg);
  color: var(--color-income);
}

.sheet-type-badge.liability {
  background: var(--color-expense-bg);
  color: var(--color-expense);
}

/* 余额卡片 */
.balance-card {
  padding: 20px;
  border-radius: 14px;
  margin-bottom: 16px;
}

.balance-card.asset {
  background: linear-gradient(135deg, rgba(82, 196, 26, 0.12) 0%, rgba(82, 196, 26, 0.06) 100%);
}

.balance-card.liability {
  background: linear-gradient(135deg, rgba(245, 34, 45, 0.12) 0%, rgba(245, 34, 45, 0.06) 100%);
}

.balance-label {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin-bottom: 8px;
}

.balance-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--color-text-primary);
}

.balance-card.liability .balance-value {
  color: var(--color-expense);
}

.balance-exempt {
  margin-top: 10px;
  font-size: 13px;
  color: var(--color-text-tertiary);
}

/* 详情列表 */
.detail-list {
  background: var(--color-bg-page);
  border-radius: 12px;
  padding: 4px 0;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 14px 16px;
}

.detail-label {
  font-size: 14px;
  color: var(--color-text-secondary);
  flex-shrink: 0;
}

.detail-value {
  font-size: 14px;
  color: var(--color-text-primary);
  text-align: right;
  flex: 1;
  margin-left: 16px;
}

/* 操作按钮 */
.sheet-actions {
  display: flex;
  gap: 12px;
  margin-top: 20px;
}

.action-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 14px;
  font-size: 15px;
  font-weight: 500;
  border: none;
  border-radius: 12px;
  cursor: pointer;
}

.action-btn.edit {
  background: var(--color-transfer-bg);
  color: var(--color-transfer);
}

.action-btn.delete {
  background: var(--color-expense-bg);
  color: var(--color-expense);
}

.action-btn:active {
  opacity: 0.8;
}
</style>

<!-- 非 scoped 样式 -->
<style>
.account-page .page-header {
  background: rgba(245, 245, 245, 0.8);
}

html.dark .account-page .page-header {
  background: rgba(10, 10, 10, 0.8);
}

/* 暗黑模式 - 弹窗样式 */
html.dark .van-action-sheet {
  background: var(--color-bg-card);
}

html.dark .van-action-sheet__header {
  color: var(--color-text-primary);
}

html.dark .van-action-sheet__close {
  color: var(--color-text-secondary);
}
</style>
