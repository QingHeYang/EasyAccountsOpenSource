<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { actionApi, type Action, ActionHandle } from '@shared/api/action'
import { useSmartBack } from '@shared/composables/useSmartBack'

const router = useRouter()
const { smartBack } = useSmartBack()

// 数据
const loading = ref(false)
const actions = ref<Action[]>([])

// 获取操作类型文本和样式
function getHandleInfo(handle: ActionHandle) {
  switch (handle) {
    case ActionHandle.IN:
      return { text: '流入', color: 'var(--color-income)', bg: 'var(--color-income-bg)' }
    case ActionHandle.OUT:
      return { text: '流出', color: 'var(--color-expense)', bg: 'var(--color-expense-bg)' }
    case ActionHandle.TRANSFER:
      return { text: '转账', color: 'var(--color-transfer)', bg: 'var(--color-transfer-bg)' }
    default:
      return { text: '未知', color: 'var(--color-text-secondary)', bg: 'var(--color-bg-page)' }
  }
}

// 加载数据
async function fetchActions() {
  loading.value = true
  try {
    const res = await actionApi.getAll()
    actions.value = res.data.data
  } catch (err) {
    console.error('获取收支列表失败', err)
  } finally {
    loading.value = false
  }
}

function onBack() {
  smartBack('/setting')
}

function onAdd() {
  router.push('/setting/action/add')
}

function onItemClick(action: Action) {
  router.push(`/setting/action/edit/${action.id}`)
}

onMounted(() => {
  fetchActions()
})
</script>

<template>
  <div class="action-page">
    <!-- 顶部导航 -->
    <div class="page-header">
      <div class="header-left" @click="onBack">
        <van-icon name="arrow-left" size="20" />
      </div>
      <div class="header-title">收支管理</div>
      <div class="header-right" @click="onAdd">
        <van-icon name="plus" size="20" />
      </div>
    </div>

    <!-- 列表 -->
    <div class="page-body">
      <div class="action-list">
        <div
          v-for="action in actions"
          :key="action.id"
          class="action-item"
          @click="onItemClick(action)"
        >
          <div class="action-info">
            <div class="action-name">{{ action.hname }}</div>
            <div class="action-tags">
              <span
                class="action-tag"
                :style="{
                  color: getHandleInfo(action.handle).color,
                  background: getHandleInfo(action.handle).bg,
                }"
              >
                {{ getHandleInfo(action.handle).text }}
              </span>
              <span v-if="action.exempt" class="action-tag exempt">不计入</span>
            </div>
          </div>
          <van-icon name="arrow" class="action-arrow" />
        </div>
      </div>

      <!-- 空状态 -->
      <van-empty v-if="!loading && actions.length === 0" description="暂无收支类型" />
    </div>
  </div>
</template>

<style scoped>
.action-page {
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
.action-list {
  background: var(--color-bg-card);
  border-radius: 16px;
  overflow: hidden;
}

.action-item {
  display: flex;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid var(--color-border);
}

.action-item:last-child {
  border-bottom: none;
}

.action-item:active {
  background: var(--color-bg-active);
}

.action-info {
  flex: 1;
}

.action-name {
  font-size: 16px;
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: 6px;
}

.action-tags {
  display: flex;
  gap: 8px;
}

.action-tag {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
}

.action-tag.exempt {
  color: var(--color-text-secondary);
  background: var(--color-bg-page);
}

.action-arrow {
  color: var(--color-text-tertiary);
  font-size: 16px;
}
</style>

<!-- 非 scoped 样式 -->
<style>
.action-page .page-header {
  background: rgba(245, 245, 245, 0.8);
}

html.dark .action-page .page-header {
  background: rgba(10, 10, 10, 0.8);
}
</style>
