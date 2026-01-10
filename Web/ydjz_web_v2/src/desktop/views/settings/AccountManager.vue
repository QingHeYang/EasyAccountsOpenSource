<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Close, CreditCard } from '@element-plus/icons-vue'
import { accountApi, type Account } from '@shared/api/account'
import alipayIcon from '@shared/assets/icons/alipay.svg'
import wechatIcon from '@shared/assets/icons/wechat.svg'
import housingFundIcon from '@shared/assets/icons/housing-fund.svg'
import cashIcon from '@shared/assets/icons/cash.svg'

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
}>()

// 抽屉状态
const drawerVisible = ref(false)
const showDetail = ref(false)

// 数据
const loading = ref(false)
const accounts = ref<Account[]>([])
const editingAccount = ref<Account | null>(null)

// 表单
const accountForm = ref({
  name: '',
  money: '',
  exemptMoney: '',
  card: '',
  note: '',
})

// 监听外部 visible 变化
watch(() => props.visible, (val) => {
  drawerVisible.value = val
  if (val) {
    loadAccounts()
  }
})

// 监听内部 drawer 变化同步到外部
watch(drawerVisible, (val) => {
  emit('update:visible', val)
  if (!val) {
    showDetail.value = false
    resetForm()
  }
})

// 抽屉宽度
const drawerSize = computed(() => showDetail.value ? '800px' : '480px')

// 根据账户名获取图标
function getAccountIcon(name: string | undefined): string | null {
  if (!name) return null
  if (name.includes('支付宝')) return alipayIcon
  if (name.includes('微信')) return wechatIcon
  if (name.includes('公积金')) return housingFundIcon
  if (name.includes('现金')) return cashIcon
  return null
}

// 格式化金额显示
function formatMoney(money: string | undefined) {
  if (!money || money === '0' || money === '0.00') return '¥0.00'
  return `¥${money}`
}

// 金额输入格式化（允许负数）
function formatMoneyInput(value: string): string {
  // 检查是否以负号开头
  const isNegative = value.startsWith('-')
  let result = value.replace(/[^\d.]/g, '')
  const parts = result.split('.')
  if (parts.length > 2) {
    result = parts[0] + '.' + parts.slice(1).join('')
  }
  if (parts.length === 2 && parts[1].length > 2) {
    result = parts[0] + '.' + parts[1].slice(0, 2)
  }
  // 恢复负号
  if (isNegative && result) {
    result = '-' + result
  }
  return result
}

async function loadAccounts() {
  loading.value = true
  try {
    const res = await accountApi.getAll()
    accounts.value = res.data.data
  } catch (err) {
    console.error('获取账户列表失败', err)
    ElMessage.error('获取账户列表失败')
  } finally {
    loading.value = false
  }
}

function onAdd() {
  editingAccount.value = null
  resetForm()
  showDetail.value = true
}

function onEdit(account: Account) {
  editingAccount.value = account
  accountForm.value = {
    name: account.name,
    money: account.money || '',
    exemptMoney: account.exemptMoney || '',
    card: account.card || '',
    note: account.note || '',
  }
  showDetail.value = true
}

function onCloseDetail() {
  showDetail.value = false
  resetForm()
}

function resetForm() {
  editingAccount.value = null
  accountForm.value = {
    name: '',
    money: '',
    exemptMoney: '',
    card: '',
    note: '',
  }
}

// 判断账户余额是否为负数（负债类账户）
const isNegativeBalance = computed(() => {
  const m = parseFloat(accountForm.value.money || '0')
  return m < 0
})

async function onSubmit() {
  if (!accountForm.value.name.trim()) {
    ElMessage.warning('请输入账户名称')
    return
  }
  if (!accountForm.value.money) {
    ElMessage.warning('请输入账户余额')
    return
  }

  try {
    // 负数账户（负债类）不允许设置不计入金额
    const exemptMoney = isNegativeBalance.value ? '' : (accountForm.value.exemptMoney || '')

    const params = {
      name: accountForm.value.name.trim(),
      money: accountForm.value.money,
      exemptMoney,
      card: accountForm.value.card || '',
      note: accountForm.value.note || '',
    }

    if (editingAccount.value) {
      await accountApi.update(editingAccount.value.id, params)
      ElMessage.success('保存成功')
    } else {
      await accountApi.add(params)
      ElMessage.success('添加成功')
    }
    onCloseDetail()
    loadAccounts()
  } catch (err) {
    console.error('操作失败', err)
    ElMessage.error('操作失败')
  }
}

async function onDelete() {
  if (!editingAccount.value) return

  try {
    await ElMessageBox.confirm(
      '确定停用该账户吗？停用后将无法在此账户下记账！关于此账户的数据不会删除。',
      '停用账户',
      {
        confirmButtonText: '确定停用',
        cancelButtonText: '取消',
        type: 'warning',
        customClass: 'high-zindex-msgbox',
      }
    )

    await accountApi.delete(editingAccount.value.id)
    ElMessage.success('已停用')
    onCloseDetail()
    loadAccounts()
  } catch {
    // 取消
  }
}
</script>

<template>
  <el-drawer
    v-model="drawerVisible"
    title="账户管理"
    direction="rtl"
    :size="drawerSize"
    :z-index="3000"
    class="setting-drawer split-layout"
  >
    <!-- 抽屉头部 -->
    <template #header>
      <div class="drawer-header">
        <div class="drawer-header-left">
          <span class="drawer-title">账户管理</span>
        </div>
        <el-button :icon="Plus" type="primary" @click="onAdd">添加</el-button>
      </div>
    </template>

    <div class="drawer-split-view">
      <!-- 左侧：列表 -->
      <div class="split-list" :class="{ 'has-detail': showDetail }">
        <div v-loading="loading" class="account-list">
          <div
            v-for="account in accounts"
            :key="account.id"
            class="account-item"
            :class="{ active: editingAccount?.id === account.id }"
            @click="onEdit(account)"
          >
            <div class="account-icon" :class="{ 'has-svg': getAccountIcon(account.name) }">
              <img v-if="getAccountIcon(account.name)" :src="getAccountIcon(account.name)!" class="account-svg" />
              <el-icon v-else :size="24"><CreditCard /></el-icon>
            </div>
            <div class="account-info">
              <div class="account-name">{{ account.name }}</div>
              <div v-if="account.card" class="account-card">{{ account.card }}</div>
            </div>
            <div class="account-money">{{ formatMoney(account.money) }}</div>
          </div>
          <el-empty v-if="!loading && accounts.length === 0" description="暂无账户" />
        </div>
      </div>

      <!-- 右侧：详情/表单 -->
      <Transition name="slide-detail">
        <div v-if="showDetail" class="split-detail">
          <div class="detail-header">
            <span class="detail-title">{{ editingAccount ? '编辑账户' : '添加账户' }}</span>
            <el-button :icon="Close" text circle @click="onCloseDetail" />
          </div>
          <div class="detail-body">
            <div class="form-section">
              <!-- 账户名称 -->
              <div class="form-item">
                <label class="form-label">账户名称 <span class="required">*</span></label>
                <el-input
                  v-model="accountForm.name"
                  placeholder="请输入账户名称"
                  size="large"
                />
              </div>

              <!-- 账户余额 -->
              <div class="form-item">
                <label class="form-label">账户余额 <span class="required">*</span></label>
                <el-input
                  :model-value="accountForm.money"
                  @input="(val: string) => accountForm.money = formatMoneyInput(val)"
                  placeholder="0.00"
                  size="large"
                >
                  <template #prefix>¥</template>
                </el-input>
                <div v-if="isNegativeBalance" class="input-hint warning">
                  负数余额通常表示信用卡或负债账户
                </div>
              </div>

              <!-- 不计入金额 -->
              <div class="form-item">
                <label class="form-label">不计入金额</label>
                <el-input
                  :model-value="accountForm.exemptMoney"
                  @input="(val: string) => accountForm.exemptMoney = formatMoneyInput(val)"
                  placeholder="0.00"
                  size="large"
                  :disabled="isNegativeBalance"
                >
                  <template #prefix>¥</template>
                </el-input>
                <div v-if="isNegativeBalance" class="input-hint warning">
                  负债类账户不支持设置不计入金额
                </div>
                <div v-else class="input-hint">此金额不计入资产统计</div>
              </div>

              <!-- 卡号 -->
              <div class="form-item">
                <label class="form-label">卡号/账号</label>
                <el-input
                  v-model="accountForm.card"
                  placeholder="请输入卡号（可选）"
                  size="large"
                />
              </div>

              <!-- 备注 -->
              <div class="form-item">
                <label class="form-label">备注</label>
                <el-input
                  v-model="accountForm.note"
                  type="textarea"
                  :rows="2"
                  placeholder="请输入备注（可选）"
                />
              </div>
            </div>
          </div>
          <div class="detail-footer">
            <el-button v-if="editingAccount" type="danger" plain @click="onDelete">停用</el-button>
            <el-button @click="onCloseDetail">取消</el-button>
            <el-button type="primary" @click="onSubmit">
              {{ editingAccount ? '保存' : '添加' }}
            </el-button>
          </div>
        </div>
      </Transition>
    </div>
  </el-drawer>
</template>

<style scoped>
/* 抽屉头部 */
.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.drawer-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.drawer-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
}

/* 分栏布局 - 使用全局样式 .drawer-split-view */
.split-list {
  padding: 20px;
  transition: width 0.3s ease;
  background: var(--color-bg-card);
}

.split-list.has-detail {
  width: 340px;
  border-right: 1px solid var(--color-border);
}

.split-detail {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, var(--color-bg-page) 0%, var(--color-bg-card) 100%);
  overflow: hidden;
  position: relative;
}

.split-detail::before {
  content: '';
  position: absolute;
  top: -60px;
  right: -60px;
  width: 200px;
  height: 200px;
  background: linear-gradient(135deg, var(--color-transfer) 0%, var(--color-income) 100%);
  border-radius: 50%;
  opacity: 0.08;
  filter: blur(40px);
  pointer-events: none;
}

.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  background: transparent;
  position: relative;
  z-index: 1;
}

.detail-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.detail-body {
  flex: 1;
  padding: 0 24px 24px;
  overflow-y: auto;
  position: relative;
  z-index: 1;
}

.detail-footer {
  display: flex;
  gap: 12px;
  padding: 16px 24px;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-top: 1px solid var(--color-border-light);
}

.detail-footer .el-button {
  flex: 1;
  height: 44px;
  border-radius: 12px;
  font-weight: 500;
}

/* 详情面板动画 */
.slide-detail-enter-active,
.slide-detail-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-detail-enter-from,
.slide-detail-leave-to {
  opacity: 0;
  transform: translateX(30px);
}

/* 账户列表 */
.account-list {
  min-height: 200px;
}

.account-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 18px;
  margin-bottom: 10px;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.25s ease;
  border: 1.5px solid rgba(0, 0, 0, 0.04);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.account-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08);
  border-color: rgba(0, 0, 0, 0.06);
}

.account-item.active {
  border-color: var(--color-transfer);
  background: linear-gradient(135deg, rgba(24, 144, 255, 0.08) 0%, rgba(24, 144, 255, 0.04) 100%);
  box-shadow: 0 4px 16px rgba(24, 144, 255, 0.15);
}

.account-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-transfer-bg);
  color: var(--color-transfer);
  border-radius: 12px;
  flex-shrink: 0;
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

.account-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.account-card {
  margin-top: 4px;
  font-size: 13px;
  color: var(--color-text-tertiary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.account-money {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

/* 表单样式 */
.form-section {
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-radius: 16px;
  padding: 24px;
  border: 1px solid rgba(0, 0, 0, 0.04);
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.04);
}

.form-item {
  margin-bottom: 24px;
}

.form-item:last-child {
  margin-bottom: 0;
}

.form-label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-secondary);
  margin-bottom: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.required {
  color: var(--color-expense);
}

.input-hint {
  margin-top: 8px;
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.input-hint.warning {
  color: var(--color-expense);
}
</style>
